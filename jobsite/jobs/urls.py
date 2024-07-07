# jobs/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from .views import job_list, post_job, apply_job, job_applicants, register, custom_login, custom_logout, edit_job, delete_job, user_dashboard

urlpatterns = [
    path('', job_list, name='job_list'),
    path('post-job/', post_job, name='post_job'),
    path('apply/<int:job_id>/', apply_job, name='apply_job'),
    path('job-applicants/<int:job_id>/', job_applicants, name='job_applicants'),
    path('register/', register, name='register'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('edit-job/<int:job_id>/', edit_job, name='edit_job'),
    path('delete-job/<int:job_id>/', delete_job, name='delete_job'),
    path('user-dashboard/', user_dashboard, name='user_dashboard'),  # Add this line
]
