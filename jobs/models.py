# jobs/models.py

from django.db import models
from users.models import CustomUser
from django.conf import settings

class JobPost(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField()
    company = models.CharField(max_length=500)
    location = models.CharField(max_length=500)
    function = models.CharField(max_length=500, blank=True, null=True)
    schedule = models.CharField(max_length=500, blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    posted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
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
    cover_letter = models.TextField(blank=True, null=True)  
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.applicant.username} - {self.job.title}'