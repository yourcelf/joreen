import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joreen.settings')

app = Celery('joreen')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
