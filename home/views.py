from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import *
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone
import requests
from django.db.models import Q

# Create your views here.

User = get_user_model()

def home_page(request):
    context={'page':'BIT'}
    return render(request, 'homee/index.html', context)

def fetch_news(source=None, language='en'):
    api_key = 'NTIr1l-Avuroc_hwjRbiZgDNIpKLKmJCbw_EloVxa9BGk_jS'  # Replace with your valid Currents API key
    base_url = 'https://api.currentsapi.services/v1/latest-news?'

    # Construct the API URL based on the provided source
    if source:
        url = f'{base_url}domain={source}&apiKey={api_key}'
    else:
        url = f'{base_url}language={language}&apiKey={api_key}'

    # print(f"Fetching news from: {url}")  # Debug log

    response = requests.get(url)
    # print(f"API Response Code: {response.status_code}")  # Debug log
    # print(f"API Response Content: {response.content}")  # Debug log

    if response.status_code == 200:
        news_data = response.json()
        print("Raw news data:", news_data)  # Debug log

        if 'news' in news_data:
            return news_data['news']  # Return list of news articles
        else:
            print("No 'news' key in the response.")  # Debug log
            return []
    else:
        print("Failed to fetch news:", response.status_code, response.content)
        return []

    


@login_required(login_url="/login/")
def books(request, book_id=None):

    newspapers = [
        {
            'name': 'Times of India',
            'image_url': '/static/photos/times_of_india.png', 
            'domain': 'timesofindia.indiatimes.com'
        },
        {
            'name': 'Loksatta',
            'image_url': '/static/photos/loksatta.png',
            'domain': 'lokmat.com'
        },
        {
            'name': 'The Indian Express',
            'image_url': '/static/photos/indian_express.png', 
            'domain': 'indianexpress.com'
        },
    ]

    selected_newspaper = None  
    news_articles = []

    if request.method == "GET":
        selected_newspaper = request.GET.get('newspaper', None)

        news_articles = fetch_news(source=selected_newspaper) if selected_newspaper else []

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'news_articles': news_articles})


    if request.user.is_authenticated:
        user = request.user
        first_name = user.first_name
        last_name = user.last_name

        try:
            profile = StudentProfile.objects.get(user=user)
            full_name = profile.full_name
            student_image = profile.student_image
            gender = profile.gender

            if gender == 'male':
                default_avatar = settings.STATIC_URL + 'photos/boy.avif'
            else:
                default_avatar = settings.STATIC_URL + 'photos/girl.avif'

        except StudentProfile.DoesNotExist:
            full_name = f"{first_name} {last_name}"
            student_image = None
    else:
        first_name = "Guest"
        last_name = "guest"
        full_name = "Guest User"
        student_image = None

    borrowed_book_ids = Borrow.objects.filter(user=request.user).values_list('book_id', flat=True) if request.user.is_authenticated else []
    borrowed_books_status = {borrow.book_id: borrow.user for borrow in Borrow.objects.filter(returned_date__isnull=True)}

    overdue_books = Borrow.objects.filter(user=request.user, returned_date__isnull=True)
    overdue_ids = [
        borrow.id for borrow in overdue_books if borrow.calculate_fine() > 0
    ]

    if request.method == "POST":
        if 'add_book' in request.POST:
            title = request.POST.get('title')
            author = request.POST.get('author')
            total_copies = int(request.POST.get('total_copies', 0)) 
            book_image = request.FILES.get('book_image')  

            if not title or not author or total_copies <= 0:
                messages.error(request, "All fields are required.")
                return redirect('books')
            
            book = Book(
                title=title, 
                author=author, 
                total_copies=total_copies, 
                available_copies=total_copies, 
                book_image=book_image
            )
            try:
                book.save()
            except Exception as e:
                messages.error(request, f"Error saving book: {str(e)}")

            messages.success(request, f'Book "{title}" added successfully!')
            return redirect('books')

        if book_id is not None:
            book = get_object_or_404(Book, id=book_id)

            if 'borrow' in request.POST:
                if book.is_available():
                    Borrow.objects.create(user=request.user, book=book, borrowed_date=timezone.now())
                    book.available_copies -= 1
                    book.borrowed_by.add(request.user)
                    book.save()

                    messages.success(request, f'You’ve successfully borrowed "{book.title}". 📚')
                else:
                    messages.error(request, "Oops, this book is not available right now.")

            elif 'return' in request.POST:
                borrow_record = Borrow.objects.filter(user=request.user, book=book, returned_date__isnull=True).first()
                if borrow_record:
                    fine = borrow_record.calculate_fine()
                    borrow_record.returned_date = timezone.now()
                    borrow_record.save()

                    book.available_copies += 1
                    book.borrowed_by.remove(request.user)
                    book.save()

                    if fine > 0:
                        messages.error(request, f"You’re late! Pay {fine} rupees for the overdue days. 💸")
                    else:
                        messages.success(request, f'Thanks for returning "{book.title}" on time! 👏')
                else:
                    messages.error(request, "You can’t return a book you haven’t borrowed, silly! 😜")

            reminder_date = timezone.now().date() - timedelta(days=6)
            borrows = Borrow.objects.filter(borrowed_date=reminder_date, returned_date__isnull=True)

            for borrow in borrows:
                user_email = user.email
                book_title = borrow.book.title

                send_mail(
                    subject="Reminder: Return Your Book",
                    message=f"Dear {first_name},\n\n"
                            f"Please return the book '{book_title}' within the next day to avoid fines.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user_email],
                )

                # if borrow_record.borrowed_date 
        
    books_list = Book.objects.all()
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all') 

    # if request.GET.get('search'):
    #     books_list = books_list.filter(title__icontains = request.GET.get('search'))
        # newspapers = newspapers.filter(name__icontains = request.GET.get('search'))

    if search_query:
        books_list = books_list.filter(Q(title__icontains=search_query) | Q(author__icontains=search_query))
        
        newspapers = [paper for paper in newspapers if search_query.lower() in paper['name'].lower()]

    if filter_type == 'books':
        books_list = books_list 
        newspapers = []

    elif filter_type == 'newspaper':
        books_list = []
        newspapers = newspapers

    context = {
        'page': 'Books',
        'first_name': first_name,
        'last_name': last_name,
        'full_name': full_name,
        'student_image': student_image,
        'default_avatar': default_avatar,
        'gender': gender,
        'books': books_list,
        'borrowed_book_ids': borrowed_book_ids,
        'borrowed_books_status': borrowed_books_status,
        'overdue_ids': overdue_ids,
        'newspapers': newspapers,
        'selected_newspaper': selected_newspaper,
        'news_articles': news_articles,
        'search_query': search_query,
        'filter_type': filter_type, 
    }

    return render(request, 'homee/BookSec.html', context)

def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        if not User.objects.filter(email=email).exists():
            messages.info(request, "Invalid email..!")
            return redirect('/login/')

        user = authenticate(username=email, password=password)

        if user is None:
            messages.info(request, "Invalid password..!")
            return redirect('/login/')
        else:
            login(request, user)

            try:
                profile = StudentProfile.objects.get(user=user)
                if profile.full_name:
                    return redirect('/')
                else:
                    return redirect('/profile/')
            except StudentProfile.DoesNotExist:
                messages.error(request, "Student profile does not exist.")
                return redirect('/profile/') 

    return render(request, 'login_page.html')

def logout_page(request):
    logout(request)
    return redirect('/login/')   

def register(request):
    # User = get_user_model()

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not email:
            messages.error(request, "Email is required.")
            return redirect('/register/')

        if password and confirm_password and password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('/register/')
        
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, "" + "; ".join(e.messages))
            return redirect('/register/')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already in use.")
            return redirect('/register/')

        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )

        subject = "Welcome to Bit Library! 📚"
        message = f"Hello {first_name},\n\nWelcome to BIT Library! We're glad to have you.\n\nAbout Bit Library: Bit Library is more than just a collection of books; it’s a gateway to knowledge, inspiration, and connection.\n\nOnline Access: Can’t make it to the physical library? No worries! Our online catalog is accessible 24/7.\n\nHappy reading, {first_name}! 📖\n\nWarm regards,\n\nJSPM's Bit Library."
        
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        try:
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, "Account created successfully! A welcome email has been sent.")
        except Exception as e:
            messages.warning(request, "Account created successfully, but email failed to send.")



        messages.success(request, "Account created successfully!")
        return redirect('/login/')
    
    context = {
        'page': 'Register'
    }

    return render(request, 'register.html', context)


@login_required(login_url="/login/")
def student_info(request):
    user = request.user
    first_name = request.user.first_name
    last_name = request.user.last_name

    profile, created = StudentProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        if request.user.is_authenticated and request.user.is_superuser:
            profile.full_name = request.POST.get('full_name')
            profile.student_image = request.FILES.get('student_image') if request.FILES.get('student_image') else profile.student_image
            profile.phone = request.POST.get('phone')
            profile.gender = request.POST.get('gender')
        else: 
            profile.full_name = request.POST.get('full_name')
            profile.student_image = request.FILES.get('student_image') if request.FILES.get('student_image') else profile.student_image
            profile.phone = request.POST.get('phone')
            profile.gender = request.POST.get('gender')
            profile.education_type = request.POST.get('education_type')
            profile.select_branch = request.POST.get('select_branch')
            pursuing_year = request.POST.get('pursuing_year')
            if pursuing_year:
                profile.pursuing_year = int(pursuing_year)
            profile.books_obtained = request.POST.get('books_obtained') or ''
        
        profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('/profile/')
    
    context = {
        'page': 'Update Profile',
        'first_name': first_name,
        'last_name': last_name,
        'full_name': profile.full_name,
        'email': user.email,
        'phone': profile.phone,
        'gender':profile.gender,
        'education_type': profile.education_type,
        'select_branch': profile.select_branch,
        'pursuing_year': profile.pursuing_year,
        'books_obtained': profile.books_obtained,
        'student_image': profile.student_image
    }

    return render(request, 'homee/profile.html', context)


@login_required(login_url="/login/")
def my_profile(request):
    try:
        profile = StudentProfile.objects.get(user=request.user)

        first_name = request.user.first_name
        last_name = request.user.last_name
        email = request.user.email
        full_name = profile.full_name
        phone = profile.phone
        gender = profile.gender
        education_type = profile.education_type
        branch = profile.select_branch
        pursuing_year = profile.pursuing_year
        student_image = profile.student_image

    except StudentProfile.DoesNotExist:
        profile = None
        first_name = request.user.first_name
        last_name = request.user.last_name
        email = request.user.email
        full_name = ""
        phone = ""
        gender = ""
        education_type = ""
        branch = ""
        pursuing_year = ""
        student_image = None

    context = {
        'page': 'My Profile',
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'full_name': full_name,
        'phone': phone,
        'gender': gender,
        'education_type': education_type,
        'select_branch': branch,
        'pursuing_year': pursuing_year,
        'student_image': student_image
    }

    return render(request, 'homee/myProfile.html', context)




class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_message = "if an account exists with the email you entered. You should receive them shortly." \
    
    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse_lazy('my_profile')
        else:
            return reverse_lazy('login_page')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            user = self.request.user
            context['email'] = user.email
        return context