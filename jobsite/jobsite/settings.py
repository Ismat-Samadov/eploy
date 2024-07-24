# settings.py
from pathlib import Path
import os
from decouple import config
import dj_database_url
from google.oauth2 import service_account
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ['.onrender.com', 
                 'careerhorizon.onrender.com', 
                 '127.0.0.1', 
                 'localhost',
                 'careerhorizon.llc',
                 'www.careerhorizon.llc']
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jobs',
    'blog',
    'channels',
    'chat',
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

ASGI_APPLICATION = 'jobsite.asgi.application'

WSGI_APPLICATION = 'jobsite.wsgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}


DATABASES = {
    'default': dj_database_url.config(default=config('DATABASE_URL'), conn_max_age=600)
}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_REDIRECT_URL = 'job_list'
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
AUTH_USER_MODEL = 'jobs.CustomUser'
GS_BUCKET_NAME = config('GS_BUCKET_NAME')
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_CREDENTIALS = service_account.Credentials.from_service_account_info({
    "type": config('GCS_TYPE'),
    "project_id": config('GCS_PROJECT_ID'),
    "private_key_id": config('GCS_PRIVATE_KEY_ID'),
    "private_key": config('GCS_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": config('GCS_CLIENT_EMAIL'),
    "client_id": config('GCS_CLIENT_ID'),
    "auth_uri": config('GCS_AUTH_URI'),
    "token_uri": config('GCS_TOKEN_URI'),
    "auth_provider_x509_cert_url": config('GCS_AUTH_PROVIDER_CERT_URL'),
    "client_x509_cert_url": config('GCS_CLIENT_CERT_URL')
})

OPENAI_API_KEY = config('OPENAI_API_KEY')

EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
