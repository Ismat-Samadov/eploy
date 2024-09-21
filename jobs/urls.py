from django.urls import path
from . import views
from .views import (
    hr_applicants,
    job_list,
    post_job,
    apply_job,
    job_applicants,
    edit_job,
    delete_job,
    about,
    hr_dashboard,
    congrats
)

urlpatterns = [
    path('', job_list, name='job_list'),
    path('about/', about, name='about'),
    path('post-job/', post_job, name='post_job'),
    path('apply-job/<int:job_id>/', apply_job, name='apply_job'),
    path('congrats/', congrats, name='congrats'),
    path('job-applicants/<int:job_id>/', job_applicants, name='job_applicants'),
    path('edit-job/<int:job_id>/', edit_job, name='edit_job'),
    path('delete-job/<int:job_id>/', delete_job, name='delete_job'),
    path('hr-dashboard/', hr_dashboard, name='hr_dashboard'),
    path('download_applicants/<int:job_id>/', views.download_applicants_xlsx, name='download_applicants_xlsx'),
    path('hr-applicants/<int:job_id>/', hr_applicants, name='hr_applicants'),
    # path('post-job-payment/<int:job_id>/', views.post_job_payment, name='post_job_payment'),
]
