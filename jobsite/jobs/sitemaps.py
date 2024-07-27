# jobs/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import JobPost

class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return JobPost.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('job_detail', args=[obj.id])

# Add more sitemaps if needed, for other models or static views
class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return ['about', 'job_list', 'home']

    def location(self, item):
        return reverse(item)
