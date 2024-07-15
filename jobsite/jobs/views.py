# jobs/views.py

import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from .models import JobPost, JobApplication
from .forms import JobPostForm, JobApplicationForm, CustomUserCreationForm, JobSearchForm, ResumeUploadForm
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta
from django.db import models
from django.db.models import Q
from .utils import extract_info, check_similarity
import openai
import PyPDF2
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

def redirect_to_jobs(request):
    return redirect('job_list')

@login_required
def hr_applicants(request):
    if request.user.user_type != 'HR':
        return HttpResponseForbidden("You are not authorized to view this page.")

    applications = JobApplication.objects.filter(job__posted_by=request.user)
    applications_page = request.GET.get('applications_page', 1)
    applications_paginator = Paginator(applications, 5)

    try:
        applications = applications_paginator.page(applications_page)
    except PageNotAnInteger:
        applications = applications_paginator.page(1)
    except EmptyPage:
        applications = applications_paginator.page(applications_paginator.num_pages)

    return render(request, 'jobs/hr_applicants.html', {'applications': applications})

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
                return redirect('login')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    else:
        form = AuthenticationForm()
    return render(request, 'jobs/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('login')

def job_list(request):
    job_title = request.GET.get('job_title', '')
    company = request.GET.get('company', '')
    query = Q(deleted=False)

    if job_title:
        query &= Q(title__icontains=job_title)
    if company:
        query &= Q(company__icontains(company))

    now = timezone.now()
    scraped_time_threshold = now - timedelta(hours=6)
    non_scraped_time_threshold = now - timedelta(days=10)

    jobs = JobPost.objects.filter(
        query,
        Q(is_scraped=True, posted_at__gte=scraped_time_threshold) | 
        Q(is_scraped=False, posted_at__gte=non_scraped_time_threshold)
    ).order_by('is_scraped', '-posted_at')

    paginator = Paginator(jobs, 10)
    page = request.GET.get('page', 1)

    try:
        jobs_page = paginator.page(page)
    except PageNotAnInteger:
        jobs_page = paginator.page(1)
    except EmptyPage:
        jobs_page = paginator.page(paginator.num_pages)

    return render(request, 'jobs/job_list.html', {'jobs': jobs_page, 'job_title': job_title, 'company': company})

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

@csrf_exempt
def test_openai_api(request):
    openai.api_key = settings.OPENAI_API_KEY

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say this is a test"}
            ]
        )
        return JsonResponse({'response': response['choices'][0]['message']['content']})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def job_search(request):
    query = request.GET.get('query', '')
    if query:
        jobs = JobPost.objects.filter(title__icontains=query, deleted=False)[:10]
        job_list = [{'id': job.id, 'title': job.title, 'company': job.company} for job in jobs]
    else:
        job_list = []
    return JsonResponse(job_list, safe=False)

@login_required
def user_dashboard(request):
    try:
        if request.user.user_type == 'HR':
            jobs = JobPost.objects.filter(posted_by=request.user, deleted=False)
            applications = JobApplication.objects.filter(job__posted_by=request.user)

            # Pagination for jobs
            jobs_page = request.GET.get('jobs_page', 1)
            jobs_paginator = Paginator(jobs, 5)
            try:
                jobs = jobs_paginator.page(jobs_page)
            except PageNotAnInteger:
                jobs = jobs_paginator.page(1)
            except EmptyPage:
                jobs = jobs_paginator.page(jobs_paginator.num_pages)

            # Pagination for applications
            applications_page = request.GET.get('applications_page', 1)
            applications_paginator = Paginator(applications, 5)
            try:
                applications = applications_paginator.page(applications_page)
            except PageNotAnInteger:
                applications = applications_paginator.page(1)
            except EmptyPage:
                applications = applications_paginator.page(applications_paginator.num_pages)

            logger.info(f'HR {request.user.username} accessed the dashboard with {jobs_paginator.count} jobs and {applications_paginator.count} applications.')
            return render(request, 'jobs/hr_dashboard.html', {'jobs': jobs, 'applications': applications})
        
        elif request.user.user_type == 'Candidate':
            applications = JobApplication.objects.filter(applicant=request.user)
            jobs = JobPost.objects.filter(deleted=False)
            
            # Pagination for applications
            applications_page = request.GET.get('applications_page', 1)
            applications_paginator = Paginator(applications, 5)
            try:
                applications = applications_paginator.page(applications_page)
            except PageNotAnInteger:
                applications = applications_paginator.page(1)
            except EmptyPage:
                applications = applications_paginator.page(applications_paginator.num_pages)

            logger.info(f'Candidate {request.user.username} accessed the dashboard with {applications_paginator.count} applications.')
            return render(request, 'jobs/candidate_dashboard.html', {'applications': applications, 'jobs': jobs})
        else:
            logger.warning(f'Unauthorized access attempt by {request.user.username}')
            return HttpResponseForbidden("You are not authorized to view this page.")
    except Exception as e:
        logger.error(f'Error in user_dashboard for user {request.user.username}: {e}', exc_info=True)
        raise

def parse_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    num_pages = len(pdf_reader.pages)
    full_text = []
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        full_text.append(page.extract_text())
    return '\n'.join(full_text)

def get_openai_analysis(prompt):
    openai.api_key = settings.OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

@login_required
def parse_cv_and_check_similarity(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        logger.debug(f'Form data: {request.POST}')
        logger.debug(f'File data: {request.FILES}')
        if form.is_valid():
            job_id = form.cleaned_data['job_id']
            resume_file = request.FILES['resume']
            logger.debug(f'Job ID: {job_id}')
            logger.debug(f'Resume file: {resume_file.name}')

            try:
                job = get_object_or_404(JobPost, id=job_id)
            except ValueError:
                logger.error(f'Invalid job ID: {job_id}')
                return JsonResponse({'error': 'Invalid job ID'}, status=400)

            # Parse the uploaded CV file
            file_ext = resume_file.name.split('.')[-1].lower()
            if file_ext == 'pdf':
                cv_text = parse_pdf(resume_file)
            else:
                return JsonResponse({'error': 'Unsupported file format. Only PDF is supported at this moment.'}, status=400)

            # Create prompts for OpenAI
            cv_prompt = f"Extract the key skills and experience from this CV: {cv_text}"
            job_prompt = f"Extract the key skills and experience from this job description: {job.description}"

            try:
                cv_skills = get_openai_analysis(cv_prompt)
                job_skills = get_openai_analysis(job_prompt)

                # Calculate similarity score (this is a placeholder; you might want to use a more sophisticated method)
                similarity_score = "Similarity score calculation is not implemented yet."

                return JsonResponse({
                    'cv_skills': cv_skills,
                    'job_skills': job_skills,
                    'similarity_score': similarity_score
                })
            except Exception as e:
                logger.error(f"Error analyzing CV or job description with OpenAI: {e}")
                return JsonResponse({'error': 'Error analyzing CV or job description with OpenAI.'}, status=500)
        else:
            logger.error(f'Form is not valid: {form.errors}')
            return JsonResponse({'error': 'Invalid form data.'}, status=400)

    form = ResumeUploadForm()
    return render(request, 'jobs/parse_cv.html', {'form': form})
