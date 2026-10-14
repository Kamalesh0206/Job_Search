import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from main import run_job_search
import database

logger = logging.getLogger("cloud_scheduler")

class JobSearchScheduler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        self._running_task: Optional[asyncio.Task] = None
        self._is_executing = False
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self._last_summary: Dict[str, Any] = {}
        self._error_count = 0
        self._initialized = True

    def load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        return {}

    def is_enabled(self) -> bool:
        env_val = os.environ.get("SCHEDULE_ENABLED")
        if env_val is not None:
            return env_val.lower() in ("true", "1", "yes")
        conf = self.load_config()
        return conf.get("schedule", {}).get("enabled", False)

    def get_interval_hours(self) -> float:
        env_val = os.environ.get("SCHEDULE_INTERVAL_HOURS")
        if env_val:
            try:
                return float(env_val)
            except ValueError:
                pass
        return 12.0

    def get_status(self) -> Dict[str, Any]:
        return {
            "enabled": self.is_enabled(),
            "interval_hours": self.get_interval_hours(),
            "is_executing": self._is_executing,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "last_summary": self._last_summary,
            "error_count": self._error_count
        }

    async def execute_search_cycle(self) -> Dict[str, Any]:
        if self._is_executing:
            logger.warning("Scheduled cycle requested but another search is already executing.")
            return {"status": "skipped", "reason": "already_executing"}

        self._is_executing = True
        start_time = datetime.now()
        logger.info(f"=== Starting Automated Cloud Job Search Cycle at {start_time} ===")

        cycle_summary = {
            "timestamp": start_time.isoformat(),
            "ai_engineer": {},
            "test_engineer": {},
            "total_new_added": 0,
            "total_duplicates_skipped": 0,
            "errors": []
        }

        try:
            # 1. Search for AI Engineer jobs
            logger.info("Executing scheduled search for [AI_ENGINEER]...")
            loop = asyncio.get_running_loop()
            ai_res = await loop.run_in_executor(None, run_job_search, "AI_ENGINEER")
            cycle_summary["ai_engineer"] = ai_res
            cycle_summary["total_new_added"] += ai_res.get("new_relevant_added", 0)
            cycle_summary["total_duplicates_skipped"] += ai_res.get("duplicates_skipped", 0)
        except Exception as e:
            logger.exception("Scheduled AI Engineer search failed")
            cycle_summary["errors"].append(f"AI_ENGINEER: {str(e)}")
            self._error_count += 1

        try:
            # 2. Search for Automotive Test Engineer jobs
            logger.info("Executing scheduled search for [TEST_ENGINEER]...")
            loop = asyncio.get_running_loop()
            test_res = await loop.run_in_executor(None, run_job_search, "TEST_ENGINEER")
            cycle_summary["test_engineer"] = test_res
            cycle_summary["total_new_added"] += test_res.get("new_relevant_added", 0)
            cycle_summary["total_duplicates_skipped"] += test_res.get("duplicates_skipped", 0)
        except Exception as e:
            logger.exception("Scheduled Test Engineer search failed")
            cycle_summary["errors"].append(f"TEST_ENGINEER: {str(e)}")
            self._error_count += 1

        end_time = datetime.now()
        duration = round((end_time - start_time).total_seconds(), 2)
        cycle_summary["duration_seconds"] = duration
        cycle_summary["status"] = "completed" if not cycle_summary["errors"] else "completed_with_errors"

        self._last_run = end_time
        self._last_summary = cycle_summary
        self._is_executing = False

        logger.info(f"=== Automated Cloud Search Cycle finished in {duration}s: +{cycle_summary['total_new_added']} jobs added ===")
        return cycle_summary

    async def _scheduler_loop(self):
        logger.info("Background cloud job scheduler loop started.")
        while True:
            try:
                interval_hours = self.get_interval_hours()
                sleep_seconds = int(interval_hours * 3600)

                if self.is_enabled():
                    self._next_run = datetime.now() + timedelta(seconds=sleep_seconds)
                    logger.info(f"Next scheduled search scheduled for: {self._next_run}")
                    await asyncio.sleep(sleep_seconds)

                    if self.is_enabled():
                        await self.execute_search_cycle()
                else:
                    self._next_run = None
                    # Check every 60 seconds if scheduler was enabled
                    await asyncio.sleep(60)
            except asyncio.CancelledError:
                logger.info("Scheduler task cancelled.")
                break
            except Exception as e:
                logger.exception(f"Unhandled error in scheduler loop: {e}")
                await asyncio.sleep(60)

    def start(self):
        if self._running_task and not self._running_task.done():
            logger.info("Scheduler task is already running.")
            return
        self._running_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler background task created.")

    def stop(self):
        if self._running_task and not self._running_task.done():
            self._running_task.cancel()
            logger.info("Scheduler background task cancelled.")

scheduler_instance = JobSearchScheduler()
