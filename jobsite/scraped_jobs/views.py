import requests
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.contrib import messages

def scraped_jobs(request):
    page = request.GET.get('page', 1)
    page_size = 10

    try:
        response = requests.get(f"https://job-scraper-api-n1wx.onrender.com/data/?page={page}&page_size={page_size}")
        response.raise_for_status()
        data = response.json()
        jobs = data.get('results', [])
        total_pages = data.get('total_pages', 1)

        paginator = Paginator(jobs, page_size)
        try:
            jobs_page = paginator.page(page)
        except PageNotAnInteger:
            jobs_page = paginator.page(1)
        except EmptyPage:
            jobs_page = paginator.page(paginator.num_pages)

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Error fetching data from API: {e}")
        jobs_page = Paginator([], page_size).page(1)
        total_pages = 1
    except ValueError as e:
        messages.error(request, f"Error parsing data from API: {e}")
        jobs_page = Paginator([], page_size).page(1)
        total_pages = 1

    context = {
        'jobs': jobs_page,
        'total_pages': total_pages,
        'has_next': jobs_page.has_next(),
        'has_previous': jobs_page.has_previous(),
        'page_obj': jobs_page,
        'paginator': paginator,
    }

    return render(request, 'scraped_jobs/scraped_jobs.html', context)
