# scraped_jobs/views.py

import requests
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


FASTAPI_URL = "https://job-scraper-api-n1wx.onrender.com"


def scraped_jobs(request):
    page = request.GET.get('page', 1)
    page_size = 25  # Set page size to 25

    try:
        response = requests.get(f"{FASTAPI_URL}/data/", params={'page': page, 'page_size': page_size})
        response.raise_for_status()
        jobs_data = response.json()
        logger.info(f"Fetched {len(jobs_data)} jobs from the API.")
    except requests.exceptions.RequestException as e:
        jobs_data = []
        logger.error(f"Error fetching data from API: {e}")
        return render(request, 'scraped_jobs/error.html', {'error': str(e)})

    # Convert jobs_data to a list if it's not already
    if not isinstance(jobs_data, list):
        jobs_data = list(jobs_data)
        logger.info(f"Converted jobs_data to list: {jobs_data}")

    paginator = Paginator(jobs_data, page_size)

    try:
        jobs_page = paginator.page(page)
        logger.info(f"Paginated jobs: {jobs_page.object_list}")
    except PageNotAnInteger:
        jobs_page = paginator.page(1)
        logger.warning(f"PageNotAnInteger, defaulting to page 1.")
    except EmptyPage:
        jobs_page = paginator.page(paginator.num_pages)
        logger.warning(f"EmptyPage, defaulting to last page: {paginator.num_pages}")

    return render(request, 'scraped_jobs/scraped_jobs.html', {'jobs': jobs_page})
