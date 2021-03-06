import os
from celery import Celery

BROKER_URL = os.environ.setdefault('BROCKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.setdefault('CELERY_RESULT_BACKEND',
                                              'redis://redis:6379/0')

app = Celery(
    'routine-jobs', broker=BROKER_URL, backend=CELERY_RESULT_BACKEND)
app.conf.update(task_soft_time_limit=30, task_time_limit=120)
app.autodiscover_tasks([
    'celery_work_farm.tasks.hello',
    'celery_work_farm.tasks.system.data_collector.influxdb',
    'celery_work_farm.tasks.system.event_collector.actions.redis'
])
