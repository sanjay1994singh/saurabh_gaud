"""
Django settings for the Dharm Raksha Sangh project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-replace-this-key-before-production")

DEBUG = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes", "on")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "social_django",
    "home",
    "accounts",
    "banners",
    "events",
    "seva_prakalp",
    "hamare_stambh",
    "patrika",
    "subscriptions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "dharm_raksha_sangh.middleware.NoCacheHtmlMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dharm_raksha_sangh.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "home.language.language_context",
            ],
        },
    },
]

WSGI_APPLICATION = "dharm_raksha_sangh.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.mysql"),
        "NAME": os.environ.get("DB_NAME", "dharm_raksha_sangh"),
        "USER": os.environ.get("DB_USER", "saurabh_gaud"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "hi"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static'
]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "dharm_raksha_sangh.staticfiles.VersionedStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

SITE_NAME = "Dharm Raksha Sangh"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "accounts:profile"
LOGOUT_REDIRECT_URL = "home:index"
LOGIN_ERROR_URL = "login"

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

SITE_URL = os.environ.get("SITE_URL", "https://dharmrakshasangh.com").rstrip("/")
ORGANIZATION_NAME = os.environ.get("ORGANIZATION_NAME", SITE_NAME)
ORGANIZATION_ADDRESS = os.environ.get(
    "ORGANIZATION_ADDRESS", "Shri Dham Vrindavan, Mathura, Uttar Pradesh, India"
)
ORGANIZATION_PHONE = os.environ.get("ORGANIZATION_PHONE", "+91 98371 647 90")
ORGANIZATION_EMAIL = os.environ.get("ORGANIZATION_EMAIL", "info@dharmrakshasangh.com")
ORGANIZATION_GSTIN = os.environ.get("ORGANIZATION_GSTIN", "")

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "accounts.backends.EmailPhoneUsernameBackend",
)

SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ["email", "profile"]
SOCIAL_AUTH_LOGIN_ERROR_URL = LOGIN_ERROR_URL
SOCIAL_AUTH_RAISE_EXCEPTIONS = False
SOCIAL_AUTH_PROTECTED_USER_FIELDS = [
    "first_name",
    "last_name",
    "email",
    "phone",
    "address",
    "city",
    "photo",
]


# Django Email Configuration
# Add the following entries to the project .env file (without the leading #):
# EMAIL_HOST_USER=your-gmail-address@gmail.com
# EMAIL_HOST_PASSWORD=your-new-16-character-google-app-password
# DEFAULT_FROM_EMAIL=your-gmail-address@gmail.com
#
# Do not paste the real Gmail password or App Password in settings.py.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "").replace(" ", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "webmaster@localhost")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_TIMEOUT = 20


# HTTPS/security defaults are enabled whenever DEBUG=False. If TLS terminates
# at a reverse proxy, it must forward X-Forwarded-Proto correctly.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "https://dharmrakshasangh.com,https://www.dharmrakshasangh.com",
    ).split(",")
    if origin.strip()
]
