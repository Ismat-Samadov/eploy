from pathlib import Path
import os
from decouple import config
import dj_database_url
from google.oauth2 import service_account
from google.cloud import secretmanager
import logging
from pathlib import Path

def get_secret(secret_name):
    """
    Access the secret value from Google Cloud Secret Manager.
    """
    project_id = "jobs-428816"
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

    
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = get_secret('SECRET_KEY')
DEBUG = get_secret('DEBUG') == 'True'
 
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'careerhorizon.llc',
    'www.careerhorizon.llc',
    '.appspot.com',
]

CSRF_TRUSTED_ORIGINS = [
    'https://www.careerhorizon.llc',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'jobs',
    'whitenoise.runserver_nostatic',
    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jobsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'jobsite.wsgi.application'

# Database configuration
DATABASES = {
    'default': dj_database_url.config(default=config('DATABASE_URL'), conn_max_age=600)
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email settings
EMAIL_BACKEND = get_secret('EMAIL_BACKEND')  # Update the secret name to match
EMAIL_HOST = get_secret('EMAIL_HOST')
EMAIL_PORT = int(get_secret('EMAIL_PORT'))
EMAIL_USE_TLS = get_secret('EMAIL_USE_TLS') == 'True'
EMAIL_HOST_USER = get_secret('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_secret('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = get_secret('DEFAULT_FROM_EMAIL')

# Custom user model
AUTH_USER_MODEL = 'jobs.CustomUser'

# Login settings
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_REDIRECT_URL = 'job_list'
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Google Cloud Storage
GS_BUCKET_NAME = get_secret('GS_BUCKET_NAME')
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_CREDENTIALS = service_account.Credentials.from_service_account_info({
    "type": get_secret('GCS_TYPE'),
    "project_id": get_secret('GCS_PROJECT_ID'),
    "private_key_id": get_secret('GCS_PRIVATE_KEY_ID'),
    "private_key": get_secret('GCS_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": get_secret('GCS_CLIENT_EMAIL'),
    "client_id": get_secret('GCS_CLIENT_ID'),
    "auth_uri": get_secret('GCS_AUTH_URI'),
    "token_uri": get_secret('GCS_TOKEN_URI'),
    "auth_provider_x509_cert_url": get_secret('GCS_AUTH_PROVIDER_CERT_URL'),
    "client_x509_cert_url": get_secret('GCS_CLIENT_CERT_URL')
})

# OpenAI API Key
OPENAI_API_KEY = get_secret('OPENAI_API_KEY')
ACCESS_TOKEN = get_secret('ACCESS_TOKEN')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
