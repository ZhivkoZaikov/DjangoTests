from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Library_Rework.settings')
app = Celery('Library_Rework')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

# Create scheduled tasks
# run them in the console with 'beat'
# celery -A Library_Rework beat -l info
app.conf.beat_schedule = {
        'add-every-minute-contrab': {
        'task': 'multiply_two_numbers',
        'schedule': crontab(),
        'args': (16, 16),
    },
    'add-every-5-seconds': {
        'task': 'multiply_two_numbers',
        'schedule': 5.0,
        'args': (16, 16)
    },
    'add-every-30-seconds': {
        'task': 'add_two_numbers',
        'schedule': 30.0,
        'args': (16, 16)
    },
}
