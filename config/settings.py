"""
Django settings for the ANJUMANEFAIZANERABBANI website.

All secrets and environment-specific values are read from environment
variables (a local `.env` file is loaded automatically in development).
"""
import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
DEBUG = env_bool("DEBUG", False)

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-change-me"
    else:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is off.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
if DEBUG:
    # Local development only: trust any port on this computer (IDE/browser previews use random ports).
    CSRF_TRUSTED_ORIGINS += [f"http://{host}:{port}" for host in ("127.0.0.1", "localhost")
                             for port in range(1024, 65536)]

SITE_NAME = "ANJUMANEFAIZANERABBANI"
SITE_DISPLAY_NAME = "Anjuman-e-Faizan-e-Rabbani"
SITE_URDU_NAME = "انجمنِ فیضانِ ربانی"
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8000").rstrip("/")
YOUTUBE_CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID", "")

USE_CLOUDINARY = bool(os.environ.get("CLOUDINARY_URL"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    # Local apps
    "core",
    "videos",
    "events",
    "gallery",
    "contact",
]
if USE_CLOUDINARY:
    INSTALLED_APPS += ["cloudinary_storage", "cloudinary"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------------------------------
# Database: SQLite locally, DATABASE_URL (PostgreSQL) in production
# --------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL", "").strip() or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "admin:login"

# --------------------------------------------------------------------------
# I18N
# --------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static and media files
# --------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
if USE_CLOUDINARY:
    # CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name> is read from the environment.
    STORAGES["default"] = {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"}

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB

# --------------------------------------------------------------------------
# Cache (used for the home page, site settings and contact rate limiting)
# --------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "anjuman-cache",
    }
}
HOME_CACHE_SECONDS = int(os.environ.get("HOME_CACHE_SECONDS", "120"))

# --------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "webmaster@localhost")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
CONTACT_NOTIFY_EMAIL = os.environ.get("CONTACT_NOTIFY_EMAIL", "")

# --------------------------------------------------------------------------
# Security
# --------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "SAMEORIGIN"
SECURE_CONTENT_TYPE_NOSNIFF = True
# YouTube embeds need the page origin in the Referer header (otherwise "Error 153").
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": os.environ.get("DJANGO_LOG_LEVEL", "WARNING"), "propagate": False},
    },
}
