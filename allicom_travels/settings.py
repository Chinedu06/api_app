import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-dev-key")
DEBUG = os.environ.get("DEBUG") == "True"

ALLOWED_HOSTS = [
    "api.allicomtourism.com",
    "www.api.allicomtourism.com",
    "127.0.0.1",
    "localhost",
]

# APPLICATIONS
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    'django_extensions',

    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",

    # Local apps
    "users",
    "services",
    "bookings",
    "payments",

    "drf_spectacular",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "allicom_travels.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "allicom_travels.wsgi.application"

# DATABASE (MySQL / MariaDB)
DATABASES = {
    "default": {
        "ENGINE": os.environ.get(
            "DB_ENGINE",
            "django.db.backends.sqlite3"
        ),
        "NAME": os.environ.get(
            "DB_NAME",
            BASE_DIR / "db.sqlite3"
        ),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
        "OPTIONS": {
            "charset": "utf8mb4",
        } if os.environ.get("DB_ENGINE") else {},
    }
}


# PASSWORDS
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

# INTERNATIONALIZATION
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

# STATIC & MEDIA
STATIC_URL = "/static/"
STATIC_ROOT = "/home/allicomt/domains/api.allicomtourism.com/public_html/static"


MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# CUSTOM USER MODEL
AUTH_USER_MODEL = "users.User"

# DJANGO REST FRAMEWORK
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
}


# SIMPLE JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# FLUTTERWAVE
FLW_SECRET_KEY = os.environ.get("FLW_SECRET_KEY")
FLW_PUBLIC_KEY = os.environ.get("FLW_PUBLIC_KEY")
FLW_REDIRECT_URL = os.environ.get("FLW_REDIRECT_URL")

# DEFAULT PK FIELD
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CSRF_TRUSTED_ORIGINS = [
    "https://api.allicomtourism.com",
    "https://www.api.allicomtourism.com",
]

SPECTACULAR_SETTINGS = {
    "TITLE": "Allicom Tourism API",
    "DESCRIPTION": "Backend API for Allicom Tourism & Travel Services",
    "VERSION": "1.0.0",

    "SERVE_INCLUDE_SCHEMA": False,

    # 👇 THIS IS THE IMPORTANT PART
    "DEFAULT_GENERATOR_CLASS": "drf_spectacular.generators.SchemaGenerator",

    "SECURITY": [
        {
            "bearerAuth": [],
        }
    ],
}
