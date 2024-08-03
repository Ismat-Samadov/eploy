# jobsite/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from django.contrib.sitemaps.views import sitemap
from jobs.views import redirect_to_jobs, test_openai_api
from jobs.sitemaps import JobSitemap, StaticViewSitemap
from jobs.views import robots_txt  
from jobs.views import health_check, start_check

sitemaps = {
    'jobs': JobSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('', RedirectView.as_view(url='/jobs/', permanent=True)),
    path('admin/', admin.site.urls),
    path('jobs/', include('jobs.urls')),
    path('privacy-policy/', TemplateView.as_view(template_name='jobs/privacy_policy.html'), name='privacy_policy'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('test-openai/', test_openai_api, name='test_openai_api'),
    path('_ah/start', start_check),
    path('_ah/health', health_check),
    re_path(r'^ads.txt$', RedirectView.as_view(url=settings.STATIC_URL + 'ads.txt', permanent=False)),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
