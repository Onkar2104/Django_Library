from django.contrib import admin
from .models import *
from accounts.models import *

# Register your models here.
class ExistingAdminClass(admin.ModelAdmin):
    search_fields = ['full_name', 'phone', 'select_branch', 'education_type', 'books_obtained']
    list_filter = ('education_type', 'select_branch', 'pursuing_year')

admin.site.register(StudentProfile, ExistingAdminClass)

class ExistBooks(admin.ModelAdmin):
    pass
admin.site.register(Book, ExistBooks)

class ExistBorrow(admin.ModelAdmin):
    search_fields = ['book__title', 'user__first_name', 'user__last_name']
    list_display = ('book', 'get_user_full_name', 'user', 'borrowed_date', 'current_fine')

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    get_user_full_name.short_description = 'Name' 

admin.site.register(Borrow, ExistBorrow)