from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from jobs.views import redirect_to_jobs, test_openai_api

urlpatterns = [
    path('', redirect_to_jobs, name='home'),
    path('admin/', admin.site.urls),
    path('jobs/', include('jobs.urls')),
    path('test-openai/', test_openai_api, name='test_openai_api'),
    re_path(r'^ads.txt$', RedirectView.as_view(url=settings.STATIC_URL + 'ads.txt', permanent=False)),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
