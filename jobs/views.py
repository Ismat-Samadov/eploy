import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from .models import JobPost, JobApplication
from .forms import JobPostForm, JobApplicationForm, JobSearchForm, ResumeUploadForm
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
import logging
from datetime import timedelta
from django.db.models import Q
import openai
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from django.views.generic import DetailView
from users.models import UserProfile, WorkExperience, Education, Project, Skill, Language, Certification
from .utils import calculate_similarity, get_openai_analysis
import matplotlib
matplotlib.use('Agg')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


@login_required
def apply_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, deleted=False)

    try:
        profile = request.user.userprofile
    except ObjectDoesNotExist:
        messages.error(request, "Please complete your profile before applying for a job.")
        return redirect('create_user_profile')  # Redirect to profile creation page

    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, "Application submitted successfully.")
            return redirect('congrats')  # Redirect to a success page
    else:
        form = JobApplicationForm()

    context = {
        'form': form,
        'job': job,
        'profile': profile,  # Include profile data
    }

    return render(request, 'jobs/apply_job.html', context)
 

def redirect_to_jobs(request):
    return redirect('job_list')


class JobDetailView(DetailView):
    model = JobPost
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(JobPost, id=id_)


@login_required
def hr_dashboard(request):
    if request.user.user_type != 'HR':
        return HttpResponseForbidden("You are not authorized to view this page.")

    # Fetch jobs posted by the logged-in HR user
    jobs = JobPost.objects.filter(posted_by=request.user, deleted=False)

    # Check if jobs are being fetched
    print(f"Jobs found: {jobs.count()}")  # Debugging: Check if jobs are found

    # Pagination setup
    jobs_page = request.GET.get('jobs_page', 1)
    jobs_paginator = Paginator(jobs, 5)
    try:
        jobs = jobs_paginator.page(jobs_page)
    except PageNotAnInteger:
        jobs = jobs_paginator.page(1)
    except EmptyPage:
        jobs = jobs_paginator.page(jobs_paginator.num_pages)

    return render(request, 'jobs/hr_dashboard.html', {'jobs': jobs})


@login_required
def hr_applicants(request, job_id):
    if request.user.user_type != 'HR':
        return HttpResponseForbidden("You are not authorized to view this page.")

    # Filter applications for the specific job
    job = get_object_or_404(JobPost, id=job_id, posted_by=request.user)
    applications = JobApplication.objects.filter(job=job).order_by('-applied_at')

    # Pagination setup (optional)
    applications_page = request.GET.get('applications_page', 1)
    applications_paginator = Paginator(applications, 5)
    try:
        applications = applications_paginator.page(applications_page)
    except PageNotAnInteger:
        applications = applications_paginator.page(1)
    except EmptyPage:
        applications = applications_paginator.page(applications_paginator.num_pages)

    # Calculate similarity scores and gather profile data
    application_data = []
    for application in applications:
        # Get applicant profile data
        applicant_profile = application.applicant.userprofile
        profile_text = " ".join(
            [
                f"{exp.company} {exp.job_title}" for exp in applicant_profile.work_experiences.all()
            ] + [
                f"{edu.degree} {edu.speciality} {edu.university}" for edu in applicant_profile.educations.all()
            ] + [
                f"{skill.skill_name} {skill.skill_level}" for skill in applicant_profile.skills.all()
            ]
        )

        # Calculate similarity score using your custom utility
        job_text = application.job.description
        similarity_score = calculate_similarity(profile_text, job_text)

        application_data.append({
            'application': application,
            'similarity_score': similarity_score,
            'applicant_profile': applicant_profile
        })

    return render(request, 'jobs/hr_applicants.html', {'applications': application_data, 'job': job})

def job_list(request):
    job_title = request.GET.get('job_title', '')
    company = request.GET.get('company', '')
    query = Q(deleted=False)

    if job_title:
        query &= Q(title__icontains=job_title)
    if company:
        query &= Q(company__icontains=company)

    now = timezone.now()
    time_threshold = now - timedelta(days=30)

    non_scraped_jobs = JobPost.objects.filter(
        query,
        is_scraped=False,
        posted_at__gte=time_threshold
    ).order_by('-posted_at')

    scraped_jobs = JobPost.objects.filter(
        query,
        is_scraped=True,
        posted_at__gte=time_threshold
    ).order_by('-posted_at')

    for job in non_scraped_jobs:
        print(f"Non-scraped job: {job.title}, posted at: {job.posted_at}")
    for job in scraped_jobs:
        print(f"Scraped job: {job.title}, posted at: {job.posted_at}")

    # Combine the querysets and ensure uniqueness
    jobs = list(non_scraped_jobs) + list(scraped_jobs)
    unique_jobs = []
    seen_titles = set()
    for job in jobs:
        if job.title not in seen_titles:
            unique_jobs.append(job)
            seen_titles.add(job.title)

    paginator = Paginator(unique_jobs, 50)
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


def congrats(request):
    return render(request, 'jobs/congrats.html')


def about(request):
    return render(request, 'jobs/about.html')


def company_description(request, company_id):
    company_jobs = JobPost.objects.filter(company_id=company_id, deleted=False)
    company_name = company_jobs.first().company if company_jobs.exists() else "Unknown Company"
    return render(request, 'jobs/company_description.html', {'company_name': company_name, 'company_jobs': company_jobs})


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
    query = request.GET.get('query', '').lower()

    if query:
        now = timezone.now()
        non_scraped_time_threshold = now - timedelta(days=10)
        scraped_time_threshold = now - timedelta(hours=5)

        non_scraped_jobs = JobPost.objects.filter(
            title__icontains=query,
            deleted=False,
            is_scraped=False,
            posted_at__gte=non_scraped_time_threshold
        ).order_by('-posted_at')

        scraped_jobs = JobPost.objects.filter(
            title__icontains=query,
            deleted=False,
            is_scraped=True,
            posted_at__gte=scraped_time_threshold
        ).order_by('-posted_at')

        jobs = list(non_scraped_jobs) + list(scraped_jobs)
        unique_jobs = []
        seen_titles = set()
        for job in jobs:
            if (job.title, job.company) not in seen_titles:
                unique_jobs.append({'id': job.id, 'title': job.title, 'company': job.company})
                seen_titles.add((job.title, job.company))

        unique_jobs = unique_jobs[:20]
    else:
        unique_jobs = []

    return JsonResponse(unique_jobs, safe=False)


def parse_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    num_pages = len(pdf_reader.pages)
    full_text = []
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        full_text.append(page.extract_text())
    return '\n'.join(full_text)


def calculate_similarity(cv_text, job_text):
    vectorizer = TfidfVectorizer().fit_transform([cv_text, job_text])
    vectors = vectorizer.toarray()
    return cosine_similarity(vectors)[0, 1]


def create_similarity_chart(score):
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    ax[0].pie([score, 1 - score], labels=['Similarity', 'Difference'], colors=['blue', 'gray'], autopct='%1.1f%%')
    ax[0].set_title('CV and Job Description Similarity')

    labels = ['Overall Similarity']
    values = [score]
    x = np.arange(len(labels))

    ax[1].bar(x, values, color='blue', alpha=0.7)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(labels)
    ax[1].set_ylim(0, 1)
    ax[1].set_ylabel('Score')
    ax[1].set_title('Detailed Similarity Breakdown')

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = 'data:image/png;base64,' + string.decode('utf-8')
    buf.close()

    return uri


@login_required
def search_jobs_for_cv(request):
    query = request.GET.get('query', '').lower()
    if query:
        now = timezone.now()
        time_threshold = now - timedelta(days=10)

        non_scraped_jobs = JobPost.objects.filter(
            Q(title__icontains=query) &
            Q(deleted=False) &
            Q(is_scraped=False) &
            Q(description__isnull=False) &
            Q(description__gt='') &
            Q(posted_at__gte=time_threshold)
        ).order_by('-posted_at')

        unique_jobs = []
        seen_titles = set()
        for job in non_scraped_jobs:
            if (job.title, job.company) not in seen_titles:
                unique_jobs.append({'id': job.id, 'title': job.title, 'company': job.company})
                seen_titles.add((job.title, job.company))

        unique_jobs = unique_jobs[:20]
    else:
        unique_jobs = []

    return JsonResponse(unique_jobs, safe=False)


@login_required
def parse_cv_page(request):
    job_search_form = JobSearchForm()
    resume_upload_form = ResumeUploadForm()

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

            file_ext = resume_file.name.split('.')[-1].lower()
            if file_ext == 'pdf':
                cv_text = parse_pdf(resume_file)
            else:
                return JsonResponse({'error': 'Unsupported file format. Only PDF is supported at this moment.'}, status=400)

            cv_prompt = f"Extract the key skills and experience from this CV: {cv_text}"
            job_prompt = f"Extract the key skills and experience from this job description: {job.description}"
            advice_prompt = f"Give some advice to improve this CV for the job at {job.company}: {cv_text}"
            cover_letter_prompt = f"Generate a personalized cover letter for the job description: {job.description} at {job.company} based on the following CV: {cv_text}"

            try:
                cv_skills = get_openai_analysis(cv_prompt)
                job_skills = get_openai_analysis(job_prompt)
                advice = get_openai_analysis(advice_prompt)
                cover_letter = get_openai_analysis(cover_letter_prompt)
                similarity_score = calculate_similarity(cv_skills, job_skills)
                chart_uri = create_similarity_chart(similarity_score)

                logger.debug(f'CV Skills: {cv_skills}')
                logger.debug(f'Job Skills: {job_skills}')
                logger.debug(f'Similarity Score: {similarity_score}')

                return render(request, 'jobs/similarity_results.html', {
                    'cv_skills': cv_skills,
                    'job_skills': job_skills,
                    'similarity_score': similarity_score,
                    'chart_uri': chart_uri,
                    'advice': advice,
                    'cover_letter': cover_letter,
                    'job_title': job.title,
                    'company_name': job.company
                })
            except Exception as e:
                logger.error(f"Error analyzing CV or job description with OpenAI: {e}")
                return JsonResponse({'error': 'Error analyzing CV or job description with OpenAI.'}, status=500)
        else:
            logger.error(f'Form is not valid: {form.errors}')
            return JsonResponse({'error': 'Invalid form data.'}, status=400)

    return render(request, 'jobs/parse_cv.html', {
        'job_search_form': job_search_form,
        'resume_upload_form': resume_upload_form
     })
 

def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Sitemap: https://www.careerhorizon.llc/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
