from django.urls import path
from .views import scraped_jobs

urlpatterns = [
    path('', scraped_jobs, name='scraped_jobs'),
]
