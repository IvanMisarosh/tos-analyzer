from app.config import settings

from celery import Celery


celery = Celery(__name__)
celery.conf.broker_url = settings.CELERY_BROKER_URL
celery.conf.result_backend = settings.CELERY_RESULT_BACKEND

celery.autodiscover_tasks(['app.tasks'])
