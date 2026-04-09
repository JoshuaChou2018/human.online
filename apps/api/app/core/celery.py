"""
Celery 配置
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "humanonline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.parser.tasks",
        "app.services.distillation",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
