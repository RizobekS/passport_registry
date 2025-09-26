import os
from pathlib import Path

from dotenv import load_dotenv

from .template import  THEME_LAYOUT_DIR, THEME_VARIABLES

load_dotenv()  # take environment variables from .env.

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", default="")

DEBUG = os.environ.get("DEBUG", 'True').lower() in ['true', 'yes', '1']


ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
CSRF_TRUSTED_ORIGINS = [u.strip() for u in os.environ.get("CSRF_TRUSTED_ORIGINS","").split(",") if u.strip()]

# Current DJANGO_ENVIRONMENT
ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", default="local")


# Application definition

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "widget_tweaks",

    # local apps
    "apps.common",
    "apps.horses",
    "apps.parties",
    "apps.passports",
    "apps.vet",
    "apps.pages",
    "apps.authentication",
    "apps.dashboards"

]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
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
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.my_setting",
                "config.context_processors.environment",
            ],
            "libraries": {
                "theme": "web_project.template_tags.theme",
            },
            "builtins": [
                "django.templatetags.static",
                "web_project.template_tags.theme",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE"),
        "NAME": os.environ.get("DB_NAME", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {"connect_timeout": 5},

    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

ANONYMOUS_USER_NAME = "anonymous"

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "ru"

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True

USE_TZ = True

LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/auth/login/"


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default URL on which Django application runs for specific environment
BASE_URL = os.environ.get("BASE_URL", default="http://127.0.0.1:8000")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:8000")

QR_TEXT_FONT_PATH = BASE_DIR / "static" / "fonts" / "DejaVuSans.ttf"
QR_TEXT_ROTATE = 270
# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Template Settings
# ------------------------------------------------------------------------------

THEME_LAYOUT_DIR = THEME_LAYOUT_DIR
THEME_VARIABLES = THEME_VARIABLES



JAZZMIN_SETTINGS = {
    "site_title": "Реестр паспортов лошадей",
    "site_header": "Реестр паспортов",
    "site_brand": "Реестр паспортов",
    "welcome_sign": "Добро пожаловать в панель управления",
    "copyright": "WEBadiko",

    # Логотипы/иконки (положи свои файлы в STATIC)
    "site_logo": "img/logo.png",   # 256x256 или SVG
    "site_logo_classes": "img-fluid",
    "login_logo": "img/logo.png",
    "login_logo_dark": None,                          # или логотип под тёмную тему
    "site_icon": "img/logo.png",                      # 32x32

    # Язык и время
    "language_chooser": False,   # у тебя сайт многоязычный — если надо, поставь True
    # "search_model": "passports.Passport",  # глобальный поиск по модели (опционально)

    # Верхнее меню (быстрые ссылки)
    "topmenu_links": [
        {"name": "Дашборд", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"app": "passports"},  # пункт «Паспорта» (все модели app)
        {"model": "horses.Horse"},
        {"name": "Реестр (список)", "url": "passports:list", "new_window": False},
        # Пример внешней ссылки:
        # {"name": "Документация", "url": "https://docs.yoursite.tld", "new_window": True},
    ],

    # Левое меню (структура и порядок)
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "passports", "horses", "vet", "parties", "common", "auth", "admin",
    ],

    # Иконки приложений
    "icons": {
        "passports": "fas fa-id-card",
        "horses": "fas fa-horse",
        "vet": "fas fa-stethoscope",
        "parties": "fas fa-users",
        "common": "fas fa-database",

        # модели
        "passports.Passport": "fas fa-id-card",
        "horses.Horse": "fas fa-horse",
        "horses.IdentificationEvent": "fas fa-barcode",
        "horses.Ownership": "fas fa-handshake",
        "horses.HorseMeasurements": "fas fa-ruler",
        "horses.HorseDocs": "fas fa-file-medical",
        "horses.DiagnosticCheck": "fas fa-vial",
        "horses.SportAchievement": "fas fa-trophy",
        "horses.ExhibitionEntry": "fas fa-certificate",
        "horses.Offspring": "fas fa-seedling",

        "vet.Vaccination": "fas fa-syringe",
        "vet.LabTest": "fas fa-microscope",

        "parties.Person": "fas fa-user",
        "parties.Organization": "fas fa-building",
        "parties.Veterinarian": "fas fa-user-md",
        "parties.Owner": "fas fa-id-badge",

        "common.Region": "fas fa-map-marked-alt",
        "common.Breed": "fas fa-paw",
        "common.Color": "fas fa-palette",
        "common.Vaccine": "fas fa-syringe",
        "common.LabTestType": "fas fa-flask",
        "common.NumberSequence": "fas fa-sort-numeric-up",
    },

    # Пользовательское меню (справа в хедере)
    "usermenu_links": [
        {"name": "Профиль", "url": "admin:password_change", "icon": "fas fa-user-cog"},
        {"model": "auth.user"},
    ],

    # Форматы форм редактирования
    # 'horizontal_tabs' — удобно для сложных моделей (Horse, Passport)
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "horses.Horse": "horizontal_tabs",
        "passports.Passport": "collapsible",  # пример: сворачиваемые секции
    },

    # Экспериментальные опции
    "related_modal_active": False,   # добавлять связанные объекты в модальном окне
    "show_ui_builder": False,       # в проде лучше выключить
}


JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",  # базовая тема (можно 'cerulean', 'cosmo', 'flatly', 'pulse', и др.)
    "dark_mode_theme": None,  # или 'darkly'
    "navbar": "navbar-light",     # или 'navbar-dark'
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "footer_fixed": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar_class": "navbar navbar-expand navbar-light bg-white shadow-sm",
    "sidebar_class": "sidebar sidebar-dark bg-dark",
    "button_classes": {
        "primary": "btn btn-primary",
        "secondary": "btn btn-outline-secondary",
        "success": "btn btn-success",
        "info": "btn btn-info",
        "warning": "btn btn-warning",
        "danger": "btn btn-danger",
        "light": "btn btn-light",
        "dark": "btn btn-dark",
        "link": "btn btn-link",
    },
    "actions_sticky_top": True,
}
