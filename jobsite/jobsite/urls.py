# jobsite/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import redirect_to_jobs

urlpatterns = [
    path('', redirect_to_jobs, name='home'),
    path('admin/', admin.site.urls),
    path('jobs/', include('jobs.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
