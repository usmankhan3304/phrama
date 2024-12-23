from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'confg_django.settings')

app = Celery('confg_django')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
