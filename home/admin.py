from django.contrib import admin
from .models import *
from accounts.models import *

# Register your models here.
class ExistingAdminClass(admin.ModelAdmin):
    search_fields = ['full_name', 'phone', 'select_branch', 'education_type', 'books_obtained']
    list_filter = ('education_type', 'select_branch', 'pursuing_year')

admin.site.register(StudentProfile, ExistingAdminClass)