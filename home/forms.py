from django import forms
from .models import StudentProfile

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['student_image', 'full_name', 'phone', 'education_type', 'select_branch', 'pursuing_year', 'books_obtained']
        widgets = {
            'education_type': forms.Select,
            'select_branch': forms.Select,
        }
