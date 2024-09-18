import requests
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from .models import JobPost, JobApplication
from .forms import JobPostForm, JobApplicationForm, JobSearchForm, ResumeUploadForm
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
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
from .utils import calculate_similarity, get_openai_analysis
import matplotlib
from botocore.exceptions import NoCredentialsError, ClientError
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import openpyxl
from openpyxl.utils import get_column_letter
from langdetect import detect
from googletrans import Translator
from payments.models import Order  # Import the Order model for payment
from django.urls import reverse  # To generate URL for redirect after payment



# Initialize s3_client with Wasabi configuration
s3_client = boto3.client(
    's3',
    endpoint_url='https://s3.eu-central-2.wasabisys.com', 
    aws_access_key_id=os.getenv('R_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R_SECRET_ACCESS_KEY')
)


matplotlib.use('Agg')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)




# candidate views

def job_list(request):
    job_title = request.GET.get('job_title', '')
    company = request.GET.get('company', '')
    query = Q(deleted=False)

    # Add filters for job title and company with case-insensitive search using icontains
    if job_title:
        query &= Q(title__icontains=job_title)  # Case-insensitive search for job title
    if company:
        query &= Q(company__icontains=company)  # Case-insensitive search for company

    now = timezone.now()

    # Define time thresholds for scraped and non-scraped jobs
    scraped_threshold = now - timedelta(days=10)
    non_scraped_threshold = now - timedelta(days=15)

    # Retrieve non-scraped jobs
    non_scraped_jobs = JobPost.objects.filter(
        query,
        is_scraped=False,
        posted_at__gte=non_scraped_threshold
    ).order_by('-posted_at')

    # Retrieve scraped jobs
    scraped_jobs = JobPost.objects.filter(
        query,
        is_scraped=True,
        posted_at__gte=scraped_threshold
    ).order_by('-posted_at')

    # Combine non-scraped and scraped jobs while ensuring no duplicates
    combined_jobs = list(non_scraped_jobs) + list(scraped_jobs)

    # Use a dictionary to remove duplicates based on (title, company, apply_link)
    unique_jobs = {(job.title.lower(), job.company.lower(), job.apply_link): job for job in combined_jobs}.values()

    # Final pagination for the combined unique result
    final_paginator = Paginator(list(unique_jobs), 10)  # Show 10 jobs per page
    page = request.GET.get('page', 1)

    try:
        jobs_page = final_paginator.page(page)
    except PageNotAnInteger:
        jobs_page = final_paginator.page(1)
    except EmptyPage:
        jobs_page = final_paginator.page(final_paginator.num_pages)

    # Render the page with the jobs
    return render(request, 'jobs/job_list.html', {'jobs': jobs_page, 'job_title': job_title, 'company': company})


def upload_file_to_wasabi(file_name, bucket_name):
    try:
        # Check if the bucket exists
        s3_client.head_bucket(Bucket=bucket_name)
        logger.debug(f"Bucket '{bucket_name}' exists. Uploading file...")

        # Upload the file with public-read ACL
        s3_client.upload_file(file_name, bucket_name, file_name, ExtraArgs={'ACL': 'public-read'})
        logger.debug(f"File '{file_name}' uploaded successfully.")
        # Generate the file URL
        file_url = f"https://.s3.eu-central-2.wasabisys.com/{bucket_name}/resumes/{file_name}"
        logger.debug(f"File URL: {file_url}")
        return file_url
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.error(f"Bucket '{bucket_name}' does not exist.")
        else:
            logger.error(f"Failed to upload file: {e}")
        return None
    except FileNotFoundError:
        logger.error("The file was not found.")
        return None
    except NoCredentialsError:
        logger.error("Credentials not available.")
        return None

def apply_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job

            if 'resume' in request.FILES:
                resume = request.FILES['resume']
                file_name = f'resumes/{resume.name}'
                bucket_name = os.getenv('R_SPACES_NAME')

                try:
                    file_ext = resume.name.split('.')[-1].lower()
                    if file_ext == 'pdf':
                        cv_text = parse_pdf(resume)  # Parse the resume before uploading
                    else:
                        logger.error(f"Unsupported file format: {file_ext}")
                        messages.error(request, "Unsupported file format. Only PDF is supported.")
                        return redirect('apply_job', job_id=job.id)

                    job_description = job.description
                    similarity_score = calculate_similarity(cv_text, job_description)
                    application.match_score = similarity_score if similarity_score is not None else 0.0

                    with resume.open('rb') as resume_file:
                        s3_client.upload_fileobj(
                            resume_file, 
                            bucket_name, 
                            file_name, 
                            ExtraArgs={'ACL': 'public-read'}
                        )
                        application.resume = file_name

                except ClientError as e:
                    logger.error(f"Failed to upload resume: {e}")
                    messages.error(request, "Failed to upload resume. Please try again.")
                    return redirect('apply_job', job_id=job.id)
                except Exception as e:
                    logger.error(f"Error processing resume: {e}")
                    messages.error(request, "Failed to process resume. Please try again.")
                    return redirect('apply_job', job_id=job.id)

            application.save()
            return redirect('congrats')
    else:
        form = JobApplicationForm()
    
    return render(request, 'jobs/apply_job.html', {'form': form, 'job': job})










# hr views
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

@login_required
def hr_dashboard(request):
    if request.user.user_type != 'HR':
        return HttpResponseForbidden("You are not authorized to view this page.")

    # Search functionality
    search_query = request.GET.get('q', '')
    jobs = JobPost.objects.filter(posted_by=request.user, deleted=False)
    
    if search_query:
        jobs = jobs.filter(title__icontains=search_query)

    # Pagination setup
    jobs_page = request.GET.get('jobs_page', 1)
    jobs_paginator = Paginator(jobs, 5)
    try:
        jobs = jobs_paginator.page(jobs_page)
    except PageNotAnInteger:
        jobs = jobs_paginator.page(1)
    except EmptyPage:
        jobs = jobs_paginator.page(jobs_paginator.num_pages)

    return render(request, 'jobs/hr_dashboard.html', {'jobs': jobs, 'search_query': search_query})

@login_required
def hr_applicants(request, job_id):
    if request.user.user_type != 'HR':
        return HttpResponseForbidden("You are not authorized to view this page.")

    job = get_object_or_404(JobPost, id=job_id, posted_by=request.user)
    applications = JobApplication.objects.filter(job=job).exclude(full_name__isnull=True).order_by('-match_score', '-applied_at')

    applications_page = request.GET.get('applications_page', 1)
    applications_paginator = Paginator(applications, 30)
    try:
        applications = applications_paginator.page(applications_page)
    except PageNotAnInteger:
        applications = applications_paginator.page(1)
    except EmptyPage:
        applications = applications_paginator.page(applications_paginator.num_pages)

    return render(request, 'jobs/hr_applicants.html', {'applications': applications, 'job': job})

@login_required
def download_applicants_xlsx(request, job_id):
    if request.user.user_type != 'HR':
        return HttpResponseForbidden("You are not authorized to view this page.")

    job = get_object_or_404(JobPost, id=job_id, posted_by=request.user)
    applications = JobApplication.objects.filter(job=job).exclude(full_name__isnull=True).order_by('-applied_at')

    # Create an Excel workbook and sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Applicants for {job.title}"

    # Define the headers
    headers = ['Full Name', 'Email', 'Phone Number', 'Applied At', 'Match Score', 'CV Download Link']
    ws.append(headers)

    # Write data to the sheet
    for application in applications:
        ws.append([
            application.full_name,
            application.email,
            application.phone,
            application.applied_at.strftime('%Y-%m-%d %H:%M'),
            application.match_score,
            f"{application.resume.url}" if application.resume else 'No CV Uploaded'
        ])

    # Set the width of the columns
    for col_num, column_title in enumerate(headers, 1):
        column_letter = get_column_letter(col_num)
        ws.column_dimensions[column_letter].width = 20

    # Prepare the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=applicants_{job_id}.xlsx'
    wb.save(response)
    return response

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
            # Create the job but don't save it yet
            job = form.save(commit=False)
            job.posted_by = request.user

            # Redirect to payment page
            amount = 20.00  # Set the job posting price (this can be dynamic)
            order = Order.objects.create(
                amount=amount,
                status='pending'
            )
            
            # Save the job post with a reference to the order but don't make it live until payment is done
            job.payment_order = order
            job.save()

            # Redirect to payment page
            payment_url = reverse('create_payment')  # Assuming 'create_payment' is your payment view
            return redirect(f"{payment_url}?order_id={order.order_id}&amount={amount}")
    else:
        form = JobPostForm()

    return render(request, 'jobs/post_job.html', {'form': form})


@login_required
def post_job_payment(request, job_id):
    # Get the job that needs payment
    job = get_object_or_404(JobPost, id=job_id, posted_by=request.user)

    # Check if the job is already paid
    if job.is_paid:
        messages.success(request, 'This job is already paid.')
        return redirect('job_list')

    # Create a new order for the payment
    amount = 20.00  # For example, this can be dynamic or based on the job type (e.g. premium or basic)
    order = Order.objects.create(
        order_id=str(uuid4()),
        amount=amount,
        status='pending'
    )

    # Associate the order with the job
    job.payment_order = order
    job.save()

    # Redirect to the payment system (this redirects to the payments app's create_payment view)
    payment_url = reverse('create_payment')  # Assuming you have this URL set up in the payments app
    return redirect(f"{payment_url}?amount={amount}&order_id={order.order_id}")


@login_required
def job_applicants(request, job_id):
    job = get_object_or_404(JobPost, id=job_id, posted_by=request.user, deleted=False)
    applications = JobApplication.objects.filter(job=job)
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applications': applications})








# apply and create match score based on resume and job description
def parse_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        full_text = []
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text:
                full_text.append(text)
            else:
                raise ValueError(f"Unable to extract text from page {page_num + 1}")
        return '\n'.join(full_text)
    except PyPDF2.errors.PdfReadError as e:
        logger.error(f"Error reading PDF file: {e}")
        raise ValueError("The PDF file is unreadable or corrupted.")
    except Exception as e:
        logger.error(f"Unexpected error while parsing PDF: {e}")
        raise ValueError("An unexpected error occurred while processing the PDF.")

def translate_text(text, target_lang='en'):
    translator = Translator()
    try:
        translation = translator.translate(text, dest=target_lang)
        return translation.text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return None

def calculate_similarity(cv_text, job_text):
    # Detect languages of the CV and job description
    cv_lang = detect(cv_text)
    job_lang = detect(job_text)
    
    # If the CV or job description is not in English, translate them to English
    if cv_lang != 'en':
        cv_text = translate_text(cv_text, target_lang='en')
        if cv_text is None:
            return None  # Handle the case where translation fails
    if job_lang != 'en':
        job_text = translate_text(job_text, target_lang='en')
        if job_text is None:
            return None  # Handle the case where translation fails
    
    # Use the translated text for similarity calculation
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
            job_id = request.POST.get('job_id')
            if not job_id:
                logger.error('Job ID is missing from the form data.')
                return JsonResponse({'error': 'Job ID is required.'}, status=400)

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

 
 
 
 
 
 

# instructions and common views
def redirect_to_jobs(request):
    return redirect('job_list')

def congrats(request):
    return render(request, 'jobs/congrats.html')

def about(request):
    return render(request, 'jobs/about.html')

def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Sitemap: https://www.careerhorizon.llc/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
