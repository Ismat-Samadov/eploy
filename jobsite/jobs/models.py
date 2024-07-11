# jobs/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('HR', 'HR/Recruiter'),
        ('Candidate', 'Candidate'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

class JobPost(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField()
    company = models.CharField(max_length=500)
    location = models.CharField(max_length=500)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    posted_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    is_scraped = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    premium_days = models.IntegerField(default=0)
    priority_level = models.IntegerField(default=0)
    apply_link = models.URLField(max_length=1000, default='')

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField()
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.applicant.username} - {self.job.title}'
