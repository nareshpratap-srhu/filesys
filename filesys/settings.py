from pathlib import Path
import os
import socket

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

import pprint

print("\n🔍 BASE_DIR Debug:")
pprint.pprint(BASE_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-(v-ghyluz#4h25*e+ud0v)!x4&599&&@o2yrj88f+s3eu^p)04'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*'
    # 'medcap.srhu.edu.in',
    # '.medcap.srhu.edu.in',
    # '10.10.2.25',               # Local IP
    # '115.247.224.231',          # Public IP
]# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'members',
    'capture',
    'echs',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'filesys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'template'),  # Project-level base template
            os.path.join(BASE_DIR, 'members', 'template'),  # Members app templates
            os.path.join(BASE_DIR, 'capture', 'template'),  # Capture app templates
            os.path.join(BASE_DIR, 'echs', 'template'),  # echs app templates
        ],
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

WSGI_APPLICATION = 'filesys.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Use PostgreSQL engine
        'NAME': 'filesys_db',                       # Replace with your database name
        'USER': 'postgres',                     # Replace with your PostgreSQL username
        'PASSWORD': 'root',                     # Replace with your PostgreSQL password
        'HOST': 'localhost',                        # Use 'localhost' if running locally
        'PORT': '5433',                             # Default PostgreSQL port
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [

]
# Using  new user model

AUTH_USER_MODEL = 'members.CustomUser'

X_FRAME_OPTIONS = 'SAMEORIGIN'



# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-IN'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Project-level static folder
    os.path.join(BASE_DIR, 'members', 'static'),  # Members app static folder
    os.path.join(BASE_DIR, 'capture', 'static'),  # Capture app static folder
]

print("\n🔍 STATICFILES_DIRS Debug:")
pprint.pprint(STATICFILES_DIRS)

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configurations
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False  # Ensure SSL is not used when TLS is enabled
EMAIL_HOST_USER = 'medcap.srhu@gmail.com'
EMAIL_HOST_PASSWORD = 'evmnfzpytagyjael'  # <-- No spaces
DEFAULT_FROM_EMAIL = 'medcap.srhu@gmail.com'

# Admin email for error notifications or internal use
ADMIN_EMAIL = 'medcap.srhu@gmail.com'


# Redirect unauthenticated users to the correct login page
LOGIN_URL = 'members:login'   

# Redirect users to home page after successful login
LOGIN_REDIRECT_URL = 'capture:uhid_capture_camera'

# Redirect users to login page after logout
LOGOUT_REDIRECT_URL = 'members:login'

GOOGLE_MAPS_API_KEY = "your api key"

# Media Storage
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Disable HTTPS enforcement in local development
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Session timeout in seconds (e.g., 5 minutes of inactivity before logout)
SESSION_COOKIE_AGE = 300000  # 5 minutes in seconds

# Expire session when browser is closed
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expire the session when the browser is closed

# Save the session data on every request to reset the expiration timer
SESSION_SAVE_EVERY_REQUEST = True

# Logging configuration for Email sending
import logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}







