"""APScheduler implementation of the SchedulerGateway protocol."""

from collections.abc import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class APSchedulerImpl:
    """Local APScheduler implementation.

    Uses AsyncIOScheduler for compatibility with the async FastAPI event loop.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def add_job(
        self,
        job_id: str,
        func: Callable,
        trigger: str,
        **trigger_args,
    ) -> None:
        """Add a scheduled job.

        trigger: "cron" or "interval"
        trigger_args: passed to CronTrigger or IntervalTrigger
        """
        if trigger == "cron":
            t = CronTrigger(**trigger_args)
        elif trigger == "interval":
            t = IntervalTrigger(**trigger_args)
        else:
            raise ValueError(f"Unknown trigger type: {trigger}")

        self.scheduler.add_job(func, t, id=job_id, replace_existing=True)

    def remove_job(self, job_id: str) -> bool:
        try:
            self.scheduler.remove_job(job_id)
            return True
        except Exception:
            return False

    def pause_job(self, job_id: str) -> bool:
        try:
            self.scheduler.pause_job(job_id)
            return True
        except Exception:
            return False

    def resume_job(self, job_id: str) -> bool:
        try:
            self.scheduler.resume_job(job_id)
            return True
        except Exception:
            return False

    def get_job_status(self, job_id: str) -> dict | None:
        job = self.scheduler.get_job(job_id)
        if job is None:
            return None
        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "pending": job.pending,
        }

    def get_all_jobs(self) -> list[dict]:
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": j.id,
                "name": j.name,
                "next_run_time": str(j.next_run_time) if j.next_run_time else None,
                "pending": j.pending,
            }
            for j in jobs
        ]

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
