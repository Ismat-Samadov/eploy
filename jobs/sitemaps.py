# jobs/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import JobPost

class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return JobPost.objects.filter(deleted=False)

    def lastmod(self, obj):
        return obj.posted_at

    def location(self, obj):
        return reverse('job_detail', args=[obj.id])

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['job_list', 'about']  

    def location(self, item):
        return reverse(item)
