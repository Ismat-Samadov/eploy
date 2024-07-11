# jobs/views.py
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import JobPost, JobApplication
from .forms import JobPostForm, JobApplicationForm
from users.forms import CustomUserCreationForm 
from django.http import HttpResponseForbidden
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

logger = logging.getLogger(__name__)

def redirect_to_jobs(request):
    return redirect('fetch_jobs_from_api')

@login_required
def user_dashboard(request):
    if request.user.user_type == 'HR':
        jobs = JobPost.objects.filter(posted_by=request.user, deleted=False)
        applications = JobApplication.objects.filter(job__posted_by=request.user)
        return render(request, 'jobs/hr_dashboard.html', {'jobs': jobs, 'applications': applications})
    elif request.user.user_type == 'Candidate':
        applications = JobApplication.objects.filter(applicant=request.user)
        return render(request, 'jobs/candidate_dashboard.html', {'applications': applications})
    else:
        return HttpResponseForbidden("You are not authorized to view this page.")

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
            messages.error(request, 'Error in form data.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'jobs/register.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('job_list')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'jobs/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('login')

# def job_list(request):
#     query = request.GET.get('q')
#     if query:
#         jobs = JobPost.objects.filter(title__icontains(query, deleted=False))
#     else:
#         jobs = JobPost.objects.filter(deleted=False)
#     return render(request, 'jobs/job_list.html', {'jobs': jobs})


def job_list(request):
    query = request.GET.get('q')
    page = request.GET.get('page', 1)

    if query:
        jobs = JobPost.objects.filter(title__icontains=query, deleted=False)
    else:
        jobs = JobPost.objects.filter(deleted=False)

    paginator = Paginator(jobs, 10)  # Show 10 jobs per page

    try:
        jobs_page = paginator.page(page)
    except PageNotAnInteger:
        jobs_page = paginator.page(1)
    except EmptyPage:
        jobs_page = paginator.page(paginator.num_pages)

    return render(request, 'jobs/job_list.html', {'jobs': jobs_page})


@login_required
def post_job(request):
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            return redirect('job_list')
    else:
        form = JobPostForm()
    return render(request, 'jobs/post_job.html', {'form': form})

@login_required
def apply_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, deleted=False)
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                application = form.save(commit=False)
                application.job = job
                application.applicant = request.user
                application.save()
                return redirect('job_list')
            except Exception as e:
                logger.error(f"Error applying for job {job_id}: {e}")
                return render(request, 'jobs/apply_job.html', {'form': form, 'job': job, 'error': 'An error occurred while applying. Please try again.'})
    else:
        form = JobApplicationForm()
    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})

@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, posted_by=request.user, deleted=False)
    applications = JobApplication.objects.filter(job=job)
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, posted_by=request.user, deleted=False)
    if request.method == 'POST':
        form = JobPostForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('job_list')
    else:
        form = JobPostForm(instance=job)
    return render(request, 'jobs/edit_job.html', {'form': form, 'job': job})

@login_required
def delete_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, posted_by=request.user)
    if request.method == 'POST':
        job.deleted = True
        job.save()
        return redirect('job_list')
    return render(request, 'jobs/confirm_delete.html', {'job': job})
