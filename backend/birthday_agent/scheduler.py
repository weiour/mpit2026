from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger


@dataclass
class ReminderScheduler:
    timezone: str

    def __post_init__(self) -> None:
        self._scheduler = BackgroundScheduler(timezone=self.timezone)
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._scheduler.start()
            self._started = True

    def shutdown(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False

    def schedule_once(
        self,
        *,
        run_at: datetime,
        job_id: str,
        func: Callable[[], None],
        replace_existing: bool = True,
    ) -> None:
        self.start()
        self._scheduler.add_job(
            func,
            trigger=DateTrigger(run_date=run_at),
            id=job_id,
            replace_existing=replace_existing,
        )

    def schedule_console_reminder(
        self,
        *,
        run_at: datetime,
        job_id: str,
        message: str,
        printer: Callable[[str], None],
    ) -> None:
        def _job() -> None:
            printer(message)

        self.schedule_once(run_at=run_at, job_id=job_id, func=_job)

