import random
import string
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import requests
from .models import *
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone
from django.db.models import Q
import random

# Create your views here.

User = get_user_model()

def home_page(request):
    context={'page':"The Scholar's Haven"}
    return render(request, 'homee/index.html', context)

def fetch_news(source=None, language='en'):
    api_key = 'Mbwe-jRAP_awuPU-_FIC9Tf_OU8kFqLHld0s9sYZEm7Iknu-' 
    base_url = 'https://api.currentsapi.services/v1/latest-news?'

    if source:
        url = f'{base_url}domain={source}&apiKey={api_key}'
    else:
        url = f'{base_url}language={language}&apiKey={api_key}'


    response = requests.get(url)

    if response.status_code == 200:
        news_data = response.json()
        print("Raw news data:", news_data) 

        if 'news' in news_data:
            return news_data['news'] 
        else:
            print("No 'news' key in the response.")  
            return []
    else:
        print("Failed to fetch news:", response.status_code, response.content)
        return []

    


@login_required(login_url="/login/")
def books(request, book_id=None):

    # if not request.user.has_perm('required_permission_name'):
    #     return redirect('register')

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
        default_avatar = settings.STATIC_URL + 'photos/boy.avif'
        gender = 'male'

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
        student_image = settings.STATIC_URL + 'photos/user.jpg'
        default_avatar = settings.STATIC_URL + 'photos/guest.avif'


    borrowed_books = []
    if request.user.is_authenticated:
        # Check if the user has borrowed books
        borrowed_books = Borrow.objects.filter(user=request.user).exists()
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
            branch = request.POST.get('branch')
            total_copies = int(request.POST.get('total_copies', 0)) 
            book_image = request.FILES.get('book_image')  

            if not title or not author or total_copies <= 0:
                messages.error(request, "All fields are required.")
                return redirect('books')
            
            book = Book(
                title=title, 
                author=author, 
                branch=branch,
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
    read = ReadOnline.objects.all()
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all') 

    if search_query:
        books_list = books_list.filter(Q(title__icontains=search_query) | Q(author__icontains=search_query))
        read = read.filter(Q(title__icontains=search_query) | Q(author__icontains=search_query))
        
        newspapers = [paper for paper in newspapers if search_query.lower() in paper['name'].lower()]

    if filter_type == 'books':
        books_list = books_list 
        newspapers = []
        read = []

    elif filter_type == 'newspaper':
        books_list = []
        read = []
        newspapers = newspapers

    elif filter_type == 'read':
        book_title = []
        read = read
        newspapers = []

    try:
        student = StudentProfile.objects.get(user=request.user)
        branch_books = Book.objects.filter(branch=student.select_branch)
    except StudentProfile.DoesNotExist:
        student = None
        branch_books = Book.objects.all()

    
    #read online
    if request.method == "POST":
        if 'add_pdf' in request.POST:
            title = request.POST.get('title')
            author = request.POST.get('author')
            branch = request.POST.get('branch')
            pdf_image = request.FILES.get('pdf_image')
            book_pdf = request.FILES.get('book_pdf')

            if not title or not author or not book_pdf:
                messages.error(request, "All Fields are required.")
                return redirect('books')

            pdf = ReadOnline(
                title = title,
                author = author,
                branch = branch,
                pdf_image = pdf_image,
                book_pdf = book_pdf
            )
            try:
                pdf.save()
            except Exception as e:
                messages.error(request, f"Error saving pdf: {str(e)}")

            messages.success(request, f"{title} added successfully.!")
            return redirect('books')
        
    bookpdf = ReadOnline.objects.all()

    ##get profile##
    profile_count = StudentProfile.objects.all()
    user_count = profile_count.count()

    ##physical books count##
    available_books = Book.objects.all()
    total_books = available_books.count()

    ## digital books count##
    read_online = ReadOnline.objects.all()
    online_count = read_online.count()



    context = {
        'page': 'Books',
        'user_count': user_count,
        'total_books': total_books,
        'online_count': online_count,
        'first_name': first_name,
        'last_name': last_name,
        'full_name': full_name,
        'student_image': student_image,
        'default_avatar': default_avatar,
        'gender': gender,
        'books': books_list,
        'read': read,
        'borrowed_book_ids': borrowed_book_ids,
        'borrowed_books_status': borrowed_books_status,
        'overdue_ids': overdue_ids,
        'newspapers': newspapers,
        'selected_newspaper': selected_newspaper,
        'news_articles': news_articles,
        'search_query': search_query,
        'filter_type': filter_type, 
        'student': student,
        'branch_books': branch_books,
        'borrowed_books': borrowed_books,

        'pdfs': bookpdf,
    }

    # return render(request, 'homee/BookSec.html', context)
    return render(request, 'homee/booksec2.html', context)


def custom_logout(request):
    user = request.user
    if user.is_authenticated:
        if getattr(user, 'is_guest', False):
            print(f"Logging out user: {user.email}, ID: {user.id}")  # Debug logging
            if user.id is not None:
                try:
                    user.delete()  # Attempt to delete the user
                    print("Guest user deleted successfully.")
                except ValueError as e:
                    print(f"Error deleting user: {e}")  # Catch and log the error
            else:
                print("User cannot be deleted: ID is None")
        logout(request)  # Log out the user
    return redirect('home_page')

def guest_login(request):
    if not request.user.is_authenticated:
        # guest_username = 'guest' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        guest_username = 'guest_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        guest_email = guest_username + "@guest.com"  # Placeholder email
        print(guest_email)

        # Create a new guest user with the placeholder email
        guest_user = User.objects.create_user(email=guest_email, password=None)
        guest_user.is_guest = True
        guest_user.is_active = True  # Optional: set guest user as inactive
        guest_user.save()

        if guest_user.id is not None:
            login(request, guest_user)
            print("Guest user created and logged in:", guest_user)
        else:
            print("User creation failed: ID is None")

        login(request, guest_user)
        # print("Is authenticated:", request.user.is_authenticated)
    return redirect('home_page')

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
            
    context = {'page': "Login"}

    return render(request, 'login_page.html', context)

def logout_page(request):
    logout(request)
    return redirect('/login/')   

def register(request):
    # User = get_user_model()

    if request.method == "POST":
        if 'send_otp' in request.POST:
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
            

            otp = random.randint(1000, 9999)
            request.session['otp'] = otp
            request.session['register_data'] = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': password,
                'confirm_password': confirm_password,
            }


            subject = "Your Verification code for Scholar's Haven"
            message = f"Hello {first_name},\nYour Verification code for Scholar's Haven {otp}"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]

            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, "Verification code sended to your mail")
            except Exception as e:
                messages.warning(request, "Unable to send Verification code to your mail.")

                return redirect('/register/')
            
            return render(request, "register.html", {"step": "verify_otp"})

        
        elif 'verify_otp' in request.POST:
            otp_input = request.POST.get('otp')
            otp = request.session.get('otp')
            register_data = request.session.get('register_data')

            if not register_data or not otp:
                message.error(request, "Session expired.!")

                return redirect('/register/')
            
            if str(otp_input) == str(otp):
                user = User.objects.create_user(
                    first_name=register_data['first_name'],
                    last_name=register_data['last_name'],
                    email=register_data['email'],
                    password=register_data['password'],
                )

            # Clear session data
                del request.session['otp']
                del request.session['register_data']

                messages.success(request, "Registration successful! Please log in.")

                #welcome email
                subject = "Welcome to 'EcoMart'! "
                message = f"Hello {register_data['first_name']},\nWelcome to The Scholar's Haven! We're glad to have you.\n\nLast Name: {register_data['last_name']}\nEmail: {register_data['email']}\n\nWarm regards,\nScholar's Haven."
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [register_data['email']]

                try:
                    send_mail(subject, message, from_email, recipient_list)
                except Exception as e:
                    messages.success("Account created successfully, but email failed to send.")

                return redirect('/login/')
            
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                
                return render(request, "register.html", {"step": "verify_otp"})
    
    context = {
        'page': 'Register',
        'step': "register",
    }

    return render(request, 'register.html', context)



@login_required(login_url="/login/")
def student_info(request):
    user = request.user
    first_name = user.first_name
    last_name = user.last_name

    profile, created = StudentProfile.objects.get_or_create(user=user)

    if not profile.email_verified:
        if not profile.otp: 
            otp = random.randint(1000, 9999)
            profile.otp = otp 
            profile.save()

        subject = "Email Verification for 'The Scholar's Haven'"
        message = f"Hello {first_name},\n\nYour verification code is {profile.otp}.\n\nThank you!"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user.email]

        try:
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, "Verification code sent to your email.")
        except Exception as e:
            messages.warning(request, "Failed to send email. Please try again.")
            print(f"Error sending email: {e}")



    if request.method == "POST":
        if not profile.email_verified:
            input_otp = request.POST.get('otp')
            if str(profile.otp) == input_otp:
                profile.email_verified = True 
                profile.otp = None
                profile.save()
                messages.success(request, "Email successfully verified!")
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return redirect('/profile/')
            
        if request.user.is_authenticated and request.user.is_superuser:
            profile.full_name = request.POST.get('full_name')
            profile.student_image = request.FILES.get('student_image') if request.FILES.get('student_image') else profile.student_image
            profile.phone = request.POST.get('phone')
            profile.gender = request.POST.get('gender')
        else: 
            profile.full_name = request.POST.get('full_name')
            profile.email_verification = request.POST.get('otp')
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
        return redirect('/myprofile/')
    
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
        'student_image': profile.student_image,
        'email_verified': profile.email_verified,
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
    


def show_books(request):
    first_name = request.user.first_name
    last_name = request.user.last_name

    if request.user.is_authenticated:
        profile = get_object_or_404(StudentProfile, user=request.user)

    profile_count = StudentProfile.objects.all()
    user_count = profile_count.count()

    available_books = Book.objects.all()
    total_books = available_books.count()

    read_online = ReadOnline.objects.all()
    online_count = read_online.count()

    search_query = request.GET.get('search', '')
    if search_query:
        available_books = available_books.filter(Q(title__icontains=search_query) | Q(author__icontains=search_query))

    
    context = {
        "page": "All Books",
        "books": available_books,
        "profile": profile,
        "first_name": first_name,
        "last_name": last_name,
        "total_books": total_books,
        "online_count": online_count,
        "user_count": user_count,
        "search_query": search_query,
        "read_online": read_online,
    }

    return render(request, 'homee/books.html', context)



def chat(request):
    return render(request, 'homee/chat.html')

def room(request, room_name):
    user = request.user
    email = request.user.email

    context = {
        'page': "Chat Room",
        'email': email,
        'user': user,
    }
    return render(request, 'homee/room.html', {"room_name": room_name}, context)

def health(request):
    context = {'Page': "Health"}
    return render(request, "homee/health.html", context)