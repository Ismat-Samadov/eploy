# jobs/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import JobPost

class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return JobPost.objects.all()

    def location(self, obj):
        return reverse('job_detail', args=[obj.pk])
