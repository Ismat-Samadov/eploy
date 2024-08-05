from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('HR', 'HR'),
        ('Candidate', 'Candidate'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='Candidate')
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], null=True, blank=True)

    def __str__(self):
        return self.username
    
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='userprofile')
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    social_network_profile = models.URLField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class WorkExperience(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='work_experiences')
    company = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
class Education(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='educations')
    university = models.CharField(max_length=255)
    degree = models.CharField(max_length=100)
    speciality = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

class Project(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='projects')
    project_name = models.CharField(max_length=255)
    project_link = models.URLField()

class Skill(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    skill_level = models.CharField(max_length=100)

class Language(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='languages')
    language = models.CharField(max_length=100)
    language_level = models.CharField(max_length=100)

class Certification(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='certifications')
    certificate_name = models.CharField(max_length=255)
    certification_date = models.DateField()
    certificate_link = models.URLField()
