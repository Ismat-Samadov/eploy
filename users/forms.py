from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile, WorkExperience, Education, Project, Skill, Language, Certification

# Ensure you're using the correct user model
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type'] 
        
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'birth_date', 
            'gender', 
            'nationality', 
            'address', 
            'phone_number', 
            'social_network_profile', 
            'about'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'about': forms.Textarea(attrs={'rows': 4}),
        }

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ['company', 'job_title', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['university', 'degree', 'speciality', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['project_name', 'project_link']

class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['skill_name', 'skill_level']

class LanguageForm(forms.ModelForm):
    class Meta:
        model = Language
        fields = ['language', 'language_level']

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['certificate_name', 'certification_date', 'certificate_link']
        widgets = {
            'certification_date': forms.DateInput(attrs={'type': 'date'}),
        }
