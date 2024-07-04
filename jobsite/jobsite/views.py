from django.shortcuts import redirect

def redirect_to_jobs(request):
    return redirect('job_list')
