"""
Celery Application

Creates and configures the Celery instance used by background workers.

Responsibilities:
- Redis broker
- Redis result backend
- Task discovery
- Serialization
- Reliability configuration
"""

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "research_assistant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks",
    ],
)


celery_app.conf.update(

    #
    # Serialization
    #
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    #
    # Time
    #
    timezone="UTC",
    enable_utc=True,

    #
    # Task Tracking
    #
    task_track_started=True,
    task_ignore_result=False,

    #
    # Reliability
    #
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    #
    # Retry on broker startup
    #
    broker_connection_retry_on_startup=True,

    #
    # Result expiration (24 hours)
    #
    result_expires=86400,

    #
    # Worker limits
    #
    worker_max_tasks_per_child=100,

    #
    # Events
    #
    worker_send_task_events=True,
    task_send_sent_event=True,
)


celery_app.autodiscover_tasks(
    [
        "app.workers",
    ]
)