from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'what9033kn03'

DEBUG = True


ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'ava-nvqb.onrender.com',  # ✅ your Render subdomain
]

# Installed Apps
INSTALLED_APPS = [
    # Default Django apps
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    'django.contrib.humanize',

    # Third-party apps
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "crispy_forms",
    "formtools",
    "channels",
    "django_countries",

    # my apps
    "chat",
    "myapp",
    "notifications",
    "swipes",
]

# Crispy Forms config
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Allauth config
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # Default
    "allauth.account.auth_backends.AuthenticationBackend",  # Allauth
]
# ✅ Updated Django 5.1 Authentication Settings
# Allow login with username or email
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*",
                         "password1*", "password2*"]  # Required signup fields
# Change to "mandatory" if you need email confirmation
ACCOUNT_EMAIL_VERIFICATION = "optional"


ACCOUNT_FORMS = {
    'signup': 'myapp.forms.CustomSignupForm',
}

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]
if os.getenv("RENDER"):
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
# URL & Templates
ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Optional if you have global templates
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # Required by Allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Localization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_CHARSET = 'utf-8'


# Email config
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "williamfocus12@gmail.com"
# Use Gmail App Password (not your real password!)
EMAIL_HOST_PASSWORD = "your-app-password"

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Optional custom user model (uncomment if you create one)
# AUTH_USER_MODEL = 'myapp.CustomUser'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
ASGI_APPLICATION = 'core.asgi.application'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATICFILES_DIRS = [BASE_DIR / 'static']

