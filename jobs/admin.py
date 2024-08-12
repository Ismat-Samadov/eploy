# jobs/admin.py

from django.contrib import admin
from .models import JobPost, JobApplication

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'posted_by', 'posted_at')
    search_fields = ('title', 'company', 'location', 'posted_by__username')
    list_filter = ('posted_at', 'location', 'company')

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'get_applicant_name', 'applied_at')
    search_fields = ('job__title', 'applicant__username')
    list_filter = ('applied_at', 'job__title')

    def get_applicant_name(self, obj):
        return obj.applicant.get_full_name() if obj.applicant.get_full_name() else obj.applicant.username
    get_applicant_name.short_description = 'Applicant'
