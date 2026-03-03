from __future__ import annotations

from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-secret-key-change-me")
DEBUG = env.bool("DEBUG", default=False)

# Railway sets this sometimes; fallback to your own env var
RAILWAY_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")

# Hosts
ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",") if h.strip()]
if RAILWAY_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_DOMAIN)

# If you want a quick temporary "allow all" for debugging (NOT recommended long-term):
# ALLOWED_HOSTS = ["*"]

# CSRF / Proxy (important for Railway HTTPS)
CSRF_TRUSTED_ORIGINS = [
    "https://electrolvotingsystem-production.up.railway.app",
]
if RAILWAY_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RAILWAY_DOMAIN}")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "voting.apps.VotingConfig",

    "rest_framework",
    "axes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # keep right after SecurityMiddleware

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "nepal_voting.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "nepal_voting.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "voting" / "templates"],
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

WSGI_APPLICATION = "nepal_voting.wsgi.application"
ASGI_APPLICATION = "nepal_voting.asgi.application"

# Database
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Fernet key required for encrypted ballots
FERNET_KEY = env("FERNET_KEY", default="")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

# Static files (WhiteNoise)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Only keep STATICFILES_DIRS if the folder exists in your repo.
# If you don't have BASE_DIR/static, either create it or remove this line.
STATICFILES_DIRS = [BASE_DIR / "static"]

# ✅ Django 5+ correct way:
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "web_login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

# Cookies (set True in real production HTTPS)
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# django-axes: login throttling
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCK_OUT_AT_FAILURE = True
AXES_RESET_ON_SUCCESS = True
AXES_USERNAME_FORM_FIELD = "username"
AXES_LOCKOUT_TEMPLATE = None

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "voting.throttles.VoteRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "vote": "5/min",
    },
}

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]