# users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, WorkExperience, Education, Project, Skill, Language, Certification
from .forms import (
    UserProfileForm, WorkExperienceForm, EducationForm, ProjectForm, 
    SkillForm, LanguageForm, CertificationForm, CustomUserCreationForm
)
from django.core.paginator import Paginator
from django.contrib import messages
from jobs.models import JobApplication
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponse
from django.conf import settings
import logging
from django.contrib.auth import get_user_model
from .forms import UserUpdateForm, CustomPasswordChangeForm
from django.contrib.auth import update_session_auth_hash

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
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Ensure the user has a UserProfile
                try:
                    profile = user.userprofile
                except UserProfile.DoesNotExist:
                    # Redirect to profile creation page if it doesn't exist
                    return redirect('create_profile')  # Ensure you have this URL pattern

                login(request, user)
                return redirect('job_list')
            else:
                messages.error(request, 'Invalid username or password.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid username or password.')
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
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            if user is not None:
                login(request, user)
                return redirect('job_list')
            else:
                messages.error(request, 'Registration successful, but could not authenticate the user.')
        else:
            # Log errors for debugging
            logger.error(f'Registration form errors: {form.errors}')
            messages.error(request, 'Error in form data.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

# Password reset view
class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

# Password reset done view
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

# Password reset confirm view
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

# Password reset complete view
class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'



@login_required
def user_dashboard(request):
    user = request.user

    # Ensure the user has a UserProfile
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        # Create a user profile if it doesn't exist or redirect to a profile creation page
        messages.warning(request, "You need to complete your profile first.")
        return redirect('create_user_profile')  # Ensure this URL exists

    if user.user_type == 'HR':
        job_applications = JobApplication.objects.filter(job__posted_by=user).order_by('-applied_at')
        template = 'users/hr_dashboard.html'
    else:
        job_applications = JobApplication.objects.filter(applicant=user).order_by('-applied_at')
        template = 'users/candidate_dashboard.html'

    paginator = Paginator(job_applications, 10)  # Paginate with 10 applications per page
    page = request.GET.get('page')
    applications = paginator.get_page(page)

    context = {
        'profile': profile,
        'applications': applications,
    }
    return render(request, template, context)

@login_required
def create_profile(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('user_dashboard')  # Or wherever you want to redirect after saving
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'users/create_profile.html', {'form': form})

@login_required
def user_profile(request):
    user = request.user
    profile = user.userprofile

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=profile)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('user_profile')
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        profile_form = UserProfileForm(instance=profile)

    work_experience_form = WorkExperienceForm()
    education_form = EducationForm()
    project_form = ProjectForm()
    skill_form = SkillForm()
    language_form = LanguageForm()
    certification_form = CertificationForm()

    context = {
        'profile_form': profile_form,
        'work_experiences': profile.work_experiences.all(),
        'educations': profile.educations.all(),
        'projects': profile.projects.all(),
        'skills': profile.skills.all(),
        'languages': profile.languages.all(),
        'certifications': profile.certifications.all(),
        'work_experience_form': work_experience_form,
        'education_form': education_form,
        'project_form': project_form,
        'skill_form': skill_form,
        'language_form': language_form,
        'certification_form': certification_form,
    }

    return render(request, 'users/user_profile.html', context)


@login_required
def add_work_experience(request):
    if request.method == 'POST':
        form = WorkExperienceForm(request.POST)
        if form.is_valid():
            work_experience = form.save(commit=False)
            work_experience.profile = request.user.userprofile
            work_experience.save()
            messages.success(request, 'Work experience added successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    return redirect('user_profile')

@login_required
def add_education(request):
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            education = form.save(commit=False)
            education.profile = request.user.userprofile
            education.save()
            messages.success(request, 'Education added successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    return redirect('user_profile')

@login_required
def add_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.profile = request.user.userprofile
            project.save()
            messages.success(request, 'Project added successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    return redirect('user_profile')

@login_required
def add_skill(request):
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.profile = request.user.userprofile
            skill.save()
            messages.success(request, 'Skill added successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    return redirect('user_profile')

@login_required
def add_language(request):
    if request.method == 'POST':
        form = LanguageForm(request.POST)
        if form.is_valid():
            language = form.save(commit=False)
            language.profile = request.user.userprofile
            language.save()
            messages.success(request, 'Language added successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    return redirect('user_profile')

@login_required
def add_certification(request):
    if request.method == 'POST':
        form = CertificationForm(request.POST)
        if form.is_valid():
            certification = form.save(commit=False)
            certification.profile = request.user.userprofile
            certification.save()
            messages.success(request, 'Certification added successfully.')
        else:
            messages.error(request, 'Please correct the errors below.')

    return redirect('user_profile')

@login_required
def delete_work_experience(request, pk):
    work_experience = get_object_or_404(WorkExperience, pk=pk, profile=request.user.userprofile)
    work_experience.delete()
    messages.success(request, 'Work experience deleted successfully.')
    return redirect('user_profile')

@login_required
def delete_education(request, pk):
    education = get_object_or_404(Education, pk=pk, profile=request.user.userprofile)
    education.delete()
    messages.success(request, 'Education deleted successfully.')
    return redirect('user_profile')

@login_required
def delete_project(request, pk):
    project = get_object_or_404(Project, pk=pk, profile=request.user.userprofile)
    project.delete()
    messages.success(request, 'Project deleted successfully.')
    return redirect('user_profile')

@login_required
def delete_skill(request, pk):
    skill = get_object_or_404(Skill, pk=pk, profile=request.user.userprofile)
    skill.delete()
    messages.success(request, 'Skill deleted successfully.')
    return redirect('user_profile')

@login_required
def delete_language(request, pk):
    language = get_object_or_404(Language, pk=pk, profile=request.user.userprofile)
    language.delete()
    messages.success(request, 'Language deleted successfully.')
    return redirect('user_profile')

@login_required
def delete_certification(request, pk):
    certification = get_object_or_404(Certification, pk=pk, profile=request.user.userprofile)
    certification.delete()
    messages.success(request, 'Certification deleted successfully.')
    return redirect('user_profile')