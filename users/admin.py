from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from .models import CustomUser

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('user_type', 'phone_number')}),
    )
    ordering = ['email']  # Update this to order by email instead of username
    list_display = ['email', 'first_name', 'last_name', 'user_type']

admin.site.register(CustomUser, CustomUserAdmin)
