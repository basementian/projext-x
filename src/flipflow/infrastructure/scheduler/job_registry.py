"""Job registry — maps FlipFlow recurring tasks to scheduler jobs."""

from flipflow.core.config import FlipFlowConfig
from flipflow.infrastructure.scheduler.apscheduler_impl import APSchedulerImpl


def register_jobs(scheduler: APSchedulerImpl, config: FlipFlowConfig):
    """Register all recurring FlipFlow jobs with the scheduler.

    Jobs are placeholder functions until their services are fully wired.
    The actual job functions will be injected when the FlipFlowEngine is created.
    """
    # Zombie scan — daily at 6 AM ET
    scheduler.add_job(
        "zombie_scan",
        _placeholder_job,
        "cron",
        hour=6,
        minute=0,
        timezone=config.surge_window_timezone,
    )

    # Queue release — Sundays at 8:00, 8:30, 9:00, 9:30 PM ET
    for minute in [0, 30]:
        for hour in [20, 21]:
            job_id = f"queue_release_{hour}_{minute:02d}"
            scheduler.add_job(
                job_id,
                _placeholder_job,
                "cron",
                day_of_week="sun",
                hour=hour,
                minute=minute,
                timezone=config.surge_window_timezone,
            )

    # Store pulse — 1st of month at 3 AM ET
    scheduler.add_job(
        "store_pulse",
        _placeholder_job,
        "cron",
        day=config.store_pulse_day_of_month,
        hour=3,
        minute=0,
        timezone=config.surge_window_timezone,
    )

    # Photo shuffler — daily at 7 AM ET
    scheduler.add_job(
        "photo_shuffle",
        _placeholder_job,
        "cron",
        hour=7,
        minute=0,
        timezone=config.surge_window_timezone,
    )

    # Offer sniper — every hour
    scheduler.add_job(
        "offer_sniper",
        _placeholder_job,
        "interval",
        hours=config.offer_poll_interval_hours,
    )

    # Kickstarter cleanup — daily at midnight ET
    scheduler.add_job(
        "kickstarter_cleanup",
        _placeholder_job,
        "cron",
        hour=0,
        minute=0,
        timezone=config.surge_window_timezone,
    )


async def _placeholder_job():
    """Placeholder for unimplemented jobs."""
    pass
