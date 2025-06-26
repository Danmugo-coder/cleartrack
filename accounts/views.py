from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .forms import LoginForm, UserProfileForm
from django.core.files.base import ContentFile
import base64
import uuid

from .forms import LoginForm, UserProfileForm, RegisterForm  # Ensure RegisterForm is imported

def register_view(request):
    """
    Handles new user registration using a custom form.
    Includes full name, email, password, and confirmation.
    """
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('dashboard:user_dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            messages.success(request, f"Welcome, {user.first_name}! Your account was created successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the highlighted errors.")
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'page_title': 'Create Account'
    })
