from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .forms import LoginForm, UserProfileForm
from django.core.files.base import ContentFile
import base64
import uuid

def register_view(request):
    """
    View for new user registration.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:user_dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Login view for users
    """
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            if request.user.profile.user_type == 'admin' or request.user.is_superuser:
                return redirect('dashboard:admin_dashboard')
            elif request.user.profile.user_type == 'user':
                return redirect('dashboard:user_dashboard')
            else:
                return redirect('dashboard:staff_dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', None)

                if next_url:
                    return redirect(next_url)

                if hasattr(user, 'profile'):
                    if user.profile.user_type == 'admin' or user.is_superuser:
                        return redirect('dashboard:admin_dashboard')
                    elif user.profile.user_type == 'user':
                        return redirect('dashboard:user_dashboard')
                    else:
                        return redirect('dashboard:staff_dashboard')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """
    Logout view for users
    """
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """
    Profile view for users to update their information
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            signature_data = form.cleaned_data.get('signature_data')

            if signature_data and 'data:image/png;base64,' in signature_data:
                signature_data = signature_data.split('data:image/png;base64,')[1]
                image_data = base64.b64decode(signature_data)
                filename = f"signature_{request.user.username}_{uuid.uuid4().hex[:8]}.png"
                request.user.profile.signature.save(filename, ContentFile(image_data), save=False)

            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user.profile)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def toggle_auto_sign(request):
    """
    Toggle auto-sign mode for staff and users
    """
    if request.method == 'POST':
        if request.user.profile.user_type in ['staff', 'user']:
            request.user.profile.auto_sign = not request.user.profile.auto_sign
            request.user.profile.save()
            status = "enabled" if request.user.profile.auto_sign else "disabled"
            messages.success(request, f'Auto-sign mode has been {status}.')

    return redirect('accounts:profile')
