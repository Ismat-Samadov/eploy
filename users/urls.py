# users/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from .views import create_profile, edit_profile, user_dashboard, user_profile, add_work_experience, add_education, add_project, add_skill, add_language, add_certification, delete_work_experience, delete_education, delete_project, delete_skill, delete_language, delete_certification
from . import views
from django.contrib.auth.views import LoginView



urlpatterns = [
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('profile/', user_profile, name='user_profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('create-profile/', views.create_profile, name='create_profile'),  
    path('add-work-experience/', add_work_experience, name='add_work_experience'),
    path('add-education/', add_education, name='add_education'),
    path('add-project/', add_project, name='add_project'),
    path('add-skill/', add_skill, name='add_skill'),
    path('add-language/', add_language, name='add_language'),
    path('add-certification/', add_certification, name='add_certification'),
    path('delete-work-experience/<int:pk>/', delete_work_experience, name='delete_work_experience'),
    path('delete-education/<int:pk>/', delete_education, name='delete_education'),
    path('delete-project/<int:pk>/', delete_project, name='delete_project'),
    path('delete-skill/<int:pk>/', delete_skill, name='delete_skill'),
    path('delete-language/<int:pk>/', delete_language, name='delete_language'),
    path('delete-certification/<int:pk>/', delete_certification, name='delete_certification'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
