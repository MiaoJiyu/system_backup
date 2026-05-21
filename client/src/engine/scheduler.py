"""Backup task scheduler supporting cron, interval, and manual triggers."""
import threading
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BackupScheduler:
    def __init__(self, task_runner, policy: dict = None):
        self.task_runner = task_runner
        self.policy = policy or {}
        self.running = True
        self.thread: threading.Thread | None = None
        self._last_run = 0.0
        self._cron_parser = None

    def update_policy(self, policy: dict):
        self.policy = policy
        logger.info("Scheduler policy updated")

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def trigger_now(self):
        """Manually trigger a backup run."""
        logger.info("Manual backup triggered")
        threading.Thread(target=self.task_runner, daemon=True).start()

    def _run(self):
        schedule_type = self.policy.get("schedule_type", "manual")
        schedule_config = self.policy.get("schedule_config", {})

        if schedule_type == "manual":
            return  # Only manual triggers

        while self.running:
            try:
                if schedule_type == "interval":
                    interval = schedule_config.get("interval_seconds", 3600)
                    if time.time() - self._last_run >= interval:
                        self._last_run = time.time()
                        threading.Thread(target=self.task_runner, daemon=True).start()
                    time.sleep(10)
                elif schedule_type == "cron":
                    self._check_cron(schedule_config.get("cron", "0 */6 * * *"))
                else:
                    time.sleep(30)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

    def _check_cron(self, cron_expr: str):
        """Simple cron-like checking. Falls back to interval if croniter not available."""
        try:
            from croniter import croniter
            now = datetime.now()
            cron = croniter(cron_expr, now)
            next_run = cron.get_next(datetime)
            wait_seconds = (next_run - now).total_seconds()
            if wait_seconds <= 0:
                self._last_run = time.time()
                threading.Thread(target=self.task_runner, daemon=True).start()
                time.sleep(60)
            else:
                time.sleep(min(wait_seconds, 30))
        except ImportError:
            # Fallback: run every 6 hours
            if time.time() - self._last_run >= 21600:
                self._last_run = time.time()
                threading.Thread(target=self.task_runner, daemon=True).start()
            time.sleep(60)
