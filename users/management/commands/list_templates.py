# users/management/commands/list_templates.py

import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'List available templates'

    def handle(self, *args, **kwargs):
        template_name = 'users/login.html'
        self.stdout.write(f"Checking for template: {template_name}")

        # Check in the custom template directories
        for template_dir in settings.TEMPLATES[0]['DIRS']:
            path = os.path.join(template_dir, template_name)
            if os.path.exists(path):
                self.stdout.write(f"Found template at: {path}")
            else:
                self.stdout.write(f"Template not found at: {path}")

        # Check in app directories if APP_DIRS is enabled
        if settings.TEMPLATES[0]['APP_DIRS']:
            self.stdout.write("Checking app directories:")
            for app_config in settings.INSTALLED_APPS:
                app_path = os.path.join(settings.BASE_DIR, app_config, 'templates', template_name)
                if os.path.exists(app_path):
                    self.stdout.write(f"Found template in app at: {app_path}")
                else:
                    self.stdout.write(f"Template not found in app at: {app_path}")
