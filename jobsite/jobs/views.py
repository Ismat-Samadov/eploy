# jobs/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import JobPost, JobApplication
from .forms import JobPostForm, JobApplicationForm
from django.http import HttpResponseForbidden
from django.contrib.auth import login, authenticate
from .forms import HRUserCreationForm
import logging

logger = logging.getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = HRUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('job_list')
    else:
        form = HRUserCreationForm()
    return render(request, 'jobs/register.html', {'form': form})


def job_list(request):
    jobs = JobPost.objects.all()
    return render(request, 'jobs/job_list.html', {'jobs': jobs})



# @login_required
# def post_job(request):
#     if request.method == 'POST':
#         form = JobPostForm(request.POST)
#         if form.is_valid():
#             job = form.save(commit=False)
#             job.posted_by = request.user
#             job.save()
#             return redirect('job_list')
#     else:
#         form = JobPostForm()
#     return render(request, 'jobs/post_job.html', {'form': form})


# @login_required
# def post_job(request):
#     if request.method == 'POST':
#         form = JobPostForm(request.POST)
#         if form.is_valid():
#             job = form.save(commit=False)
#             job.posted_by = request.user
#             job.save()
#             return redirect('job_list')
#     else:
#         form = JobPostForm()
#     return render(request, 'jobs/post_job.html', {'form': form})


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

# @login_required
# def apply_job(request, job_id):
#     job = get_object_or_404(JobPost, id=job_id)
#     if request.method == 'POST':
#         form = JobApplicationForm(request.POST, request.FILES)
#         if form.is_valid():
#             application = form.save(commit=False)
#             application.job = job
#             application.applicant = request.user
#             application.save()
#             return redirect('job_list')
#     else:
#         form = JobApplicationForm()
#     return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})


# @login_required
# def apply_job(request, job_id):
#     job = get_object_or_404(JobPost, id=job_id)
#     if request.method == 'POST':
#         form = JobApplicationForm(request.POST, request.FILES)
#         if form.is_valid():
#             application = form.save(commit=False)
#             application.job = job
#             application.applicant = request.user
#             application.save()
#             return redirect('job_list')
#     else:
#         form = JobApplicationForm()
#     return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})



@login_required
def apply_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id)
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

# @login_required
# def job_applicants(request, job_id):
#     job = get_object_or_404(JobPost, id=job_id)
#     if request.user != job.posted_by:
#         return redirect('job_list')  # Optional: Redirect if the user is not the job poster
#     applications = JobApplication.objects.filter(job=job)
#     return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})


# @login_required
# def job_applicants(request, job_id):
#     job = get_object_or_404(JobPost, id=job_id)
#     if request.user != job.posted_by:
#         return HttpResponseForbidden("You do not have permission to view these applicants.")
#     applications = JobApplication.objects.filter(job=job)
#     return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})


@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(JobPost, id=job_id)
    if request.user != job.posted_by:
        return redirect('job_list')
    applications = JobApplication.objects.filter(job=job)
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})