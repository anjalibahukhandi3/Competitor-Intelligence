"""Celery application factory for the Competitor Intelligence platform.

Design decisions
----------------
1.  **Single Celery instance, imported everywhere** — `celery_app` is the
    singleton Celery object. Both the FastAPI process (which enqueues tasks
    via `.delay()`) and the Celery worker process import this exact module.

2.  **Redis as both broker and result backend** — The broker is the message
    bus (Celery sends task payloads there; workers consume from it). The
    result backend stores task state and return values so callers can do
    `AsyncResult(task_id).get()` if they need to poll.

3.  **`task_track_started=True`** — Celery immediately writes a STARTED
    state to the result backend when a worker picks up a task. Without this,
    the state jumps directly from PENDING to SUCCESS/FAILURE and you lose
    observability of in-flight tasks.

4.  **`task_acks_late=True`** — The task message is acknowledged AFTER the
    worker finishes (not when it receives the message). If the worker crashes
    mid-task, Redis still has the message and another worker can retry.

5.  **`worker_prefetch_multiplier=1`** — Each worker fetches only one task at
    a time. Critical for long-running AI tasks: without this, a worker could
    reserve many tasks from the queue while processing one, starving other
    workers and making retry/timeout logic unreliable.

6.  **Result expiry of 24 h** — Task results are pruned from Redis after
    24 hours. The canonical source of truth is the `reports` DB table, not
    Celery's result backend.

7.  **`include=["src.jobs.tasks"]`** — Explicitly registers the tasks module
    so the worker process auto-discovers all `@celery_app.task` decorators
    on start-up without requiring manual registration.
"""

from datetime import timedelta

from celery import Celery
from celery.schedules import crontab

from src.config import settings

celery_app = Celery(
    "competitor_intelligence",       # Application name — appears in worker logs
    broker=settings.redis.url,       # redis://localhost:6379/0
    backend=settings.redis.url,      # same Redis DB for result storage
    include=[
        "src.jobs.tasks",            # Report generation pipeline
    ],
)

celery_app.conf.update(
    # ── Serialisation ────────────────────────────────────────────────────────
    task_serializer="json",          # task payloads are JSON dicts
    result_serializer="json",        # stored results are JSON
    accept_content=["json"],         # reject any non-JSON content type

    # ── Time zone ────────────────────────────────────────────────────────────
    timezone="UTC",
    enable_utc=True,

    # ── Reliability ──────────────────────────────────────────────────────────
    task_acks_late=True,             # ack AFTER completion, not on receipt
    task_reject_on_worker_lost=True, # re-queue if worker dies mid-task
    worker_prefetch_multiplier=1,    # one task per worker at a time

    # ── Observability ────────────────────────────────────────────────────────
    task_track_started=True,         # emit STARTED state to result backend
    result_expires=86_400,           # prune results after 24 h (seconds)

    # ── Beat schedules ────────────────────────────────────────────────────────
    # Daily competitor monitoring at 02:00 UTC.
    # Celery Beat must be running alongside the worker for this to fire:
    #   celery -A src.jobs.celery_app beat --loglevel=info
    beat_schedule={
        "daily-competitor-monitoring": {
            "task": "tasks.trigger_monitoring_polling",
            "schedule": crontab(hour=2, minute=0),  # every day at 02:00 UTC
            "options": {"expires": 3600},           # discard if not consumed within 1 h
        },
        # Weekly intelligence report + email delivery, every 7 days.
        # Generates a fresh report (agents -> SWOT -> PDF) for every active
        # competitor and emails the PDF to that competitor's owner — reuses
        # the exact same generate_report_task pipeline triggered manually via
        # POST /reports/trigger/{competitor_id}.
        "weekly-report-email-delivery": {
            "task": "tasks.trigger_weekly_report_emails",
            "schedule": timedelta(days=7),
            "options": {"expires": 3600},           # discard if not consumed within 1 h
        },
    },
)

