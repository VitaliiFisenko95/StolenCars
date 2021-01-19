import os
from celery import Celery


BROKER_URL = os.environ['BROKER_URL']
# RESULT_BACKEND = os.environ['RESULT_BACKEND']


celery_app = Celery('wezom', broker=BROKER_URL, include=['stolen_cars.tasks'])
celery_app.autodiscover_tasks()

