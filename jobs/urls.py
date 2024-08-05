# jobs/urls.py
from django.urls import path
from .views import (
    hr_applicants,
    job_list,
    post_job,
    apply_job,
    job_applicants,
    edit_job,
    delete_job,
    test_openai_api,
    job_search,
    search_jobs_for_cv,
    parse_cv_page,
    about,
    JobDetailView
)
from . import views

urlpatterns = [
    path('', job_list, name='job_list'),
    path('post/<int:id>/', JobDetailView.as_view(), name='job_detail'),
    path('company/<int:company_id>/', views.company_description, name='company_description'),
    path('about/', about, name='about'),
    path('post-job/', post_job, name='post_job'),
    path('apply-job/<int:job_id>/', apply_job, name='apply_job'),
    path('congrats/', views.congrats, name='congrats'),
    path('job-applicants/<int:job_id>/', job_applicants, name='job_applicants'),
    path('edit-job/<int:job_id>/', edit_job, name='edit_job'),
    path('delete-job/<int:job_id>/', delete_job, name='delete_job'),
    path('hr-applicants/', hr_applicants, name='hr_applicants'),
    path('test-openai-api/', test_openai_api, name='test_openai_api'),
    path('job-search/', job_search, name='job_search'),
    path('search-jobs-for-cv/', search_jobs_for_cv, name='search_jobs_for_cv'),
    path('parse-cv/', parse_cv_page, name='parse_cv_page'),
]
