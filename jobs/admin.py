from django.contrib import admin
from .models import CustomUser, JobPost, JobApplication
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('user_type',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'posted_by', 'posted_at')
    search_fields = ('title', 'company', 'location', 'posted_by__username')
    list_filter = ('posted_at', 'location', 'company')

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'applied_at')
    search_fields = ('job__title', 'applicant__username')
    list_filter = ('applied_at', 'job__title')
