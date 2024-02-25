import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snakie_bot.settings')

app = Celery('celery', broker=settings.CELERY_BROKER, backend=settings.CELERY_BACKEND)
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(settings.INSTALLED_APPS)
