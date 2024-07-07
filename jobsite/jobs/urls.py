# jobs/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from .views import job_list, post_job, apply_job, job_applicants, register, custom_login, custom_logout

urlpatterns = [
    path('', job_list, name='job_list'),
    path('post/', post_job, name='post_job'),
    path('apply/<int:job_id>/', apply_job, name='apply_job'),
    path('applicants/<int:job_id>/', job_applicants, name='job_applicants'),
    path('register/', register, name='register'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
]
