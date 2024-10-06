from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

User = get_user_model()
# Create your models here.

class StudentProfile(models.Model):

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = User.first_name
    last_name = User.last_name
    full_name = models.CharField(max_length=35, blank=True, default='')
    student_image = models.ImageField(upload_to='student_info/', default=None)
    phone = models.CharField(max_length=12)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    education_type = models.CharField(max_length=10)
    select_branch = models.CharField(max_length=30, null=True, blank=True)
    pursuing_year = models.IntegerField(null=False, blank=False, default='1')
    books_obtained = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.full_name:
            return self.full_name
        else:
            return f"{self.user.first_name} {self.user.last_name}"
        

class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.CharField(max_length=50)
    total_copies = models.IntegerField()
    available_copies = models.IntegerField()
    book_image = models.ImageField(upload_to='books/', null=True, blank=True)
    borrowed_by = models.ManyToManyField(User, through='Borrow', related_name='borrowed_books')

    def is_available(self):
        return self.available_copies > 0
    
    def __str__(self):
        return self.title
    
class Borrow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrowed_date = models.DateTimeField()
    returned_date = models.DateTimeField(null=True, blank=True)

    @property
    def current_fine(self):
        return self.calculate_fine()

    def calculate_fine(self):
        due_date = self.borrowed_date + timedelta(days=7)
        today = timezone.now()

        if self.returned_date:
            overdue_days = (self.returned_date - due_date).days
        else:
            overdue_days = (today - due_date).days

        if overdue_days > 0:
            return overdue_days * 3

        return 0
    
    def __str__(self):
        return self.book.title