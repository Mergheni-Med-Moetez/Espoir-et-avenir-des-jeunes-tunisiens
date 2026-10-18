"""
Tunisian Hope & Future — Django Settings
=========================================

# EXAM DEFENSE: Settings Module Design
# ======================================
# We use a single settings.py (not a settings/ package with base/dev/prod)
# because for a student project, one file is simpler to understand and defend.
# All sensitive values (SECRET_KEY, DB password) would use environment
# variables in production, but we hardcode defaults here for exam demo
# reproducibility — the professor needs to run this without .env setup.
"""

import os
from pathlib import Path

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
# EXAM DEFENSE: BASE_DIR points to the project root (where manage.py lives).
# We go up TWO levels: settings.py → config/ → project root.
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SECURITY
# =============================================================================
# EXAM DEFENSE: In production, SECRET_KEY must come from an environment
# variable. For this exam project, we use a hardcoded key for reproducibility.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'tunisian-hope-dev-key-change-in-production-2026'
)

# EXAM DEFENSE: DEBUG=True shows detailed error pages during development.
# In production, this MUST be False to avoid leaking sensitive info.
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================
# EXAM DEFENSE: Apps are organized into 3 groups:
# 1. Django built-in apps (admin, auth, sessions, etc.)
# 2. Third-party apps (DRF, Strawberry)
# 3. Our project apps (core, cases, education, health, digital, dashboard, api)

INSTALLED_APPS = [
    # --- Django Built-in ---
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # --- Third-Party ---
    'rest_framework',           # Django REST Framework for REST API
    'strawberry.django',        # Strawberry GraphQL integration

    # --- Project Apps ---
    'apps.core.apps.CoreConfig',            # Roles, UserProfile, AuditLog, state machine
    # 'apps.cases.apps.CasesConfig',        # TODO: Task 2 — Case workflow views
    'apps.education.apps.EducationConfig',   # Scenario 1 — Education Early Warning
    'apps.health.apps.HealthConfig',         # Scenario 2 — Health Follow-up
    # 'apps.dashboard.apps.DashboardConfig', # TODO: Task 2 — KPI dashboard
    'apps.dashboard.apps.DashboardConfig',   # Dashboard & HTML views
    'apps.api.apps.ApiConfig',               # API Layer — Strawberry GraphQL + future REST
]

# =============================================================================
# MIDDLEWARE
# =============================================================================
# EXAM DEFENSE: Middleware runs on EVERY request/response cycle, in order.
# SecurityMiddleware adds headers like X-Content-Type-Options.
# SessionMiddleware + AuthenticationMiddleware handle login state.
# We keep the default stack — it covers OWASP security basics.

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# =============================================================================
# TEMPLATES
# =============================================================================
# EXAM DEFENSE: We use a project-level 'templates/' directory (not per-app)
# for shared templates like base.html. App-specific templates go inside
# each app's own templates/ folder, following Django's template namespace
# convention (e.g., templates/core/user_profile.html).

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Project-level templates
        'APP_DIRS': True,                   # Also look in each app's templates/
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

WSGI_APPLICATION = 'config.wsgi.application'

# =============================================================================
# DATABASE — PostgreSQL
# =============================================================================
# EXAM DEFENSE: PostgreSQL vs SQLite
# ===================================
# SQLite is fine for prototypes, but PostgreSQL gives us:
# 1. JSONField with native JSON operators (used in AuditLog.old_value/new_value)
# 2. Better concurrency (SQLite locks the entire DB on writes)
# 3. Full-text search, array fields, and advanced indexing
# 4. Closer to production — shows engineering maturity (rubric B5)
#
# To switch to SQLite for quick testing, uncomment the SQLite block below.

# --- PostgreSQL (primary database) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'tunisian_hope_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'admin123'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# --- SQLite fallback (uncomment if PostgreSQL is not available) ---
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================
# EXAM DEFENSE: These validators enforce password strength. Django checks
# passwords against all of them when a user registers or changes password.
# This is a security best practice (rubric E1).

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Tunis'  # Tunisia's timezone (UTC+1)
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES (CSS, JavaScript, Images)
# =============================================================================
# EXAM DEFENSE: STATIC_URL is the URL prefix for static files.
# STATICFILES_DIRS tells Django where to find project-level static files
# (in addition to each app's static/ directory).

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# =============================================================================
# MEDIA FILES (User-uploaded files)
# =============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# DEFAULT PRIMARY KEY TYPE
# =============================================================================
# EXAM DEFENSE: BigAutoField is Django's default since 4.0.
# It uses 64-bit integers, supporting billions of records without overflow.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================
# EXAM DEFENSE: DRF global settings. We use session auth (for browsable API)
# and set pagination to 20 items per page to avoid returning huge datasets.

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# =============================================================================
# LOGGING
# =============================================================================
# EXAM DEFENSE: Structured logging is critical for debugging and audit trails.
# We log to the console in development. In production, you'd add file handlers.

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# =============================================================================
# LOGIN / LOGOUT REDIRECTS
# =============================================================================
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
