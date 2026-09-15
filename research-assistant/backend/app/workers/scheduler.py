"""
Celery Beat Scheduler

Defines periodic background jobs.

Examples:
- Cache cleanup
- Health check
- Index maintenance
- Evaluation jobs
"""

from celery.schedules import crontab

from app.workers.celery_app import celery_app


celery_app.conf.beat_schedule = {

    #
    # Every 10 minutes
    #
    "worker-health-check": {
        "task": "workers.health_check",
        "schedule": 600.0,
    },

    #
    # Every day at 2:00 AM UTC
    #
    "daily-cache-cleanup": {
        "task": "workers.clear_cache",
        "schedule": crontab(
            hour=2,
            minute=0,
        ),
    },

    #
    # Every Sunday at 3:00 AM UTC
    #
    "weekly-index-maintenance": {
        "task": "workers.index_document",
        "schedule": crontab(
            day_of_week="sun",
            hour=3,
            minute=0,
        ),
        "args": ("maintenance",),
    },

    #
    # Every Monday at 4:00 AM UTC
    #
    "weekly-evaluation": {
        "task": "workers.run_evaluation",
        "schedule": crontab(
            day_of_week="mon",
            hour=4,
            minute=0,
        ),
        "args": ("default",),
    },
}

celery_app.conf.timezone = "UTC"