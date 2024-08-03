from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs.users'  # Update the name to reflect the combined app structure
