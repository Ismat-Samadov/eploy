from pathlib import Path
import os
from decouple import config
from dotenv import load_dotenv
from os import getenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Helper function for loading environment variables
def get_secret(secret_name):
    return os.environ.get(secret_name) or config(secret_name)

# Security settings
SECRET_KEY = get_secret('SECRET_KEY')
DEBUG = get_secret('DEBUG') == 'True'

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '*.onrender.com',
    'eploy.io',
    'www.eploy.io',
]

CSRF_TRUSTED_ORIGINS = [
    'https://www.eploy.io',
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
    'users',
    'storages',
    'whitenoise.runserver_nostatic',
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

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': getenv('PGDATABASE'),
        'USER': getenv('PGUSER'),
        'PASSWORD': getenv('PGPASSWORD'),
        'HOST': getenv('PGHOST'),
        'PORT': getenv('PGPORT', 5432),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
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

# Wasabi configuration for media storage
AWS_ACCESS_KEY_ID = get_secret('R_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = get_secret('R_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = get_secret('R_SPACES_NAME')
AWS_S3_ENDPOINT_URL = 'https://s3.eu-central-2.wasabisys.com'
AWS_S3_CUSTOM_DOMAIN = f's3.eu-central-2.wasabisys.com/{AWS_STORAGE_BUCKET_NAME}'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/resumes/'

# Email settings
EMAIL_BACKEND = get_secret('EMAIL_BACKEND')
EMAIL_HOST = get_secret('EMAIL_HOST')
EMAIL_PORT = int(get_secret('EMAIL_PORT'))
EMAIL_USE_TLS = get_secret('EMAIL_USE_TLS') == 'True'
EMAIL_HOST_USER = get_secret('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_secret('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = get_secret('DEFAULT_FROM_EMAIL')

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# Login settings
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_REDIRECT_URL = 'job_list'
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# OpenAI API Key
OPENAI_API_KEY = get_secret('OPENAI_API_KEY')

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
