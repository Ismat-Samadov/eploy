from django.urls import path
from .views import job_list, post_job, apply_job, job_applicants

urlpatterns = [
    path('', job_list, name='job_list'),
    path('post/', post_job, name='post_job'),
    path('apply/<int:job_id>/', apply_job, name='apply_job'),
    path('applicants/<int:job_id>/', job_applicants, name='job_applicants'),
]
