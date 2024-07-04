# jobs/urls.py

from django.urls import path
from .views import job_list, post_job, apply_job

urlpatterns = [
    path('', job_list, name='job_list'),
    path('post/', post_job, name='post_job'),
    path('apply/<int:job_id>/', apply_job, name='apply_job'),
]
