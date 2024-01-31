import os
from pathlib import Path

import dj_database_url
from environs import Env

env = Env()
env.read_env()

# Bot definition
TELEGRAM_TOKEN = env('BOT_TOKEN')
TG_BOT_URL = env('BOT_UTL', 'https://web.telegram.org/k/#@SnackieBirdSubscribeBot')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/'
TG_SEND_MESSAGE_URL = TELEGRAM_API_URL + 'sendMessage'
TG_SEND_PHOTO_URL = TELEGRAM_API_URL + 'sendPhoto'
TG_BAN_URL = TELEGRAM_API_URL + 'kickChatMember'
TG_UNBAN_URL = TELEGRAM_API_URL + 'unbanChatMember'
BOT_MODE = env('BOT_MODE', 'polling')
LOG_LEVEL = env.int('LOG_LEVEL', 10)

# Payment system definition
YOO_TOKEN = env('YOO_TOKEN')
YOO_SHOP_ID = env('SHOP_ID')
PAYMENT_LINK_TTL = 60  # min

# for requests
HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                  "(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Django definition
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-9jl7kzg2q2-u#aof5c)6db403cw%d8(b)hfj399)k&49dz%u*o'

DEBUG = env.bool('DJ_DEBUG', True)

ALLOWED_HOSTS = env.list('DJ_ALLOWED_HOSTS', ['*'])
CSRF_TRUSTED_ORIGINS = env.list('DJ_CSRF_TRUSTED_ORIGINS', ['https://yookassa.ru/'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # custom
    # https://github.com/silentsokolov/django-admin-rangefilter
    "rangefilter",

    # bot
    'user',
    'payment',
    'subscription',
    'message_templates',
    'bot_parts',
    "product",
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

ROOT_URLCONF = 'snakie_bot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = 'snakie_bot.wsgi.application'

DATABASES = {
    'default': dj_database_url.parse(
        env('DJ_DB_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_DIR = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    STATIC_DIR,
]
STATIC_ROOT = './assets/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
