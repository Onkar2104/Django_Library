from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()
# Create your models here.

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = User.first_name
    last_name = User.last_name
    full_name = models.CharField(max_length=35, blank=True, default='')
    student_image = models.ImageField(upload_to='student_info/', default=None)
    phone = models.CharField(max_length=12)
    education_type = models.CharField(max_length=10)
    select_branch = models.CharField(max_length=30, null=True, blank=True)
    pursuing_year = models.IntegerField(null=False, blank=False, default='1')
    books_obtained = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.full_name:
            return self.full_name
        else:
            return f"{self.user.first_name} {self.user.last_name}"