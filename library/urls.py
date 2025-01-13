"""
URL configuration for library project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from home.views import *
from django.conf import settings
from django.conf.urls.static import static
from home.views import ResetPasswordView, custom_logout
from django.contrib.auth import views as auth_views
# from . import views

urlpatterns = [
    # path('', index_page, name="index_page"),
    path('', home_page, name="home_page"),
    path('books/<int:book_id>/', books, name='books_with_id'),
    path('books/pay_fine/', books, name='pay_fine'),
    path('books/', books, name="books"),
    path('guest-login/', guest_login, name='guest_login'),
    path('logout/', custom_logout, name='logout'),
    path('login/', login_page, name="login_page"),
    path('register/', register, name="register"),
    path('logout/', logout_page, name="logout"),
    path('profile/', student_info, name="student_info"),
    path('myprofile/', my_profile, name="my_profile"),
    path('show_books/', show_books, name="show_books"),

    path('chat/', include('home.urls')),

    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
         name='password_reset_complete'),

    path('admin/', admin.site.urls),

    path('health/', health),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)