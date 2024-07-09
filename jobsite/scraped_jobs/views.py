# scraped_jobs/views.py

import requests
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render

FASTAPI_URL = "https://job-scraper-api-n1wx.onrender.com"

def scraped_jobs(request):
    page = request.GET.get('page', 1)
    page_size = 25  # Set page size to 25

    try:
        response = requests.get(f"{FASTAPI_URL}/data/", params={'page': page, 'page_size': page_size})
        response.raise_for_status()
        jobs_data = response.json()
    except requests.exceptions.RequestException as e:
        jobs_data = []
        return render(request, 'scraped_jobs/error.html', {'error': str(e)})

    paginator = Paginator(jobs_data, page_size)

    try:
        jobs_page = paginator.page(page)
    except PageNotAnInteger:
        jobs_page = paginator.page(1)
    except EmptyPage:
        jobs_page = paginator.page(paginator.num_pages)

    return render(request, 'scraped_jobs/scraped_jobs.html', {'jobs': jobs_page})