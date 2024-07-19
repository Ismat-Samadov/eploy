from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    hr_applicants,
    register,
    custom_login,
    custom_logout,
    job_list,
    post_job,
    apply_job,
    job_applicants,
    edit_job,
    delete_job,
    test_openai_api,
    job_search,
    user_dashboard,
    search_jobs_for_cv,
    parse_cv_page
)

urlpatterns = [
    path('', job_list, name='job_list'),
    path('register/', register, name='register'),
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('post-job/', post_job, name='post_job'),
    path('apply-job/<int:job_id>/', apply_job, name='apply_job'),
    path('job-applicants/<int:job_id>/', job_applicants, name='job_applicants'),
    path('edit-job/<int:job_id>/', edit_job, name='edit_job'),
    path('delete-job/<int:job_id>/', delete_job, name='delete_job'),
    path('hr-applicants/', hr_applicants, name='hr_applicants'),
    path('test-openai-api/', test_openai_api, name='test_openai_api'),
    path('job-search/', job_search, name='job_search'),
    path('user-dashboard/', user_dashboard, name='user_dashboard'),
    path('search-jobs-for-cv/', search_jobs_for_cv, name='search_jobs_for_cv'),
    path('parse-cv/', parse_cv_page, name='parse_cv_page'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(template_name='jobs/password_reset_form.html'), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='jobs/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='jobs/password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='jobs/password_reset_complete.html'), name='password_reset_complete')
]
