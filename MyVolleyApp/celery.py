import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyVolleyApp.settings')

app = Celery('MyVolleyApp')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-temp-files-every-night': {
        'task': 'video.tasks.cleanup_temp_files_task',
        'schedule': crontab(minute=0, hour=3),
    },
}