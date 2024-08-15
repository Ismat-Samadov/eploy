from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, UserUpdateForm, CustomPasswordChangeForm
from jobs.models import JobApplication
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
import logging
# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

User = get_user_model()

@login_required
def user_profile(request):
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'users/user_profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Your profile has been updated!')
                return redirect('edit_profile')
        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Your password has been updated!')
                return redirect('edit_profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(request.user)

    context = {
        'user_form': user_form,
        'password_form': password_form
    }

    return render(request, 'users/edit_profile.html', context)


def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # 'username' key is treated as email in the form
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('job_list')
            else:
                messages.error(request, 'Invalid email or password.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['password1'])
            if user is not None:
                login(request, user)
                return redirect('job_list')
            else:
                messages.error(request, 'Registration successful, but could not authenticate the user.')
        else:
            logger.error(f'Registration form errors: {form.errors}')
            messages.error(request, 'Error in form data.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


# Password reset views
class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'

@login_required
def user_dashboard(request):
    user = request.user
    job_applications = JobApplication.objects.filter(job__posted_by=user).order_by('-applied_at')
    template = 'users/hr_dashboard.html'

    paginator = Paginator(job_applications, 10)  # Paginate with 10 applications per page
    page = request.GET.get('page')
    applications = paginator.get_page(page)

    context = {
        'applications': applications,
    }
    return render(request, template, context)
