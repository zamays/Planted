"""
Task Scheduling and Care Reminder Service

Provides automated task scheduling, care reminders, and notification
system for garden management activities.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Callable
import threading
import time
import sqlite3
from garden_manager.config import get_logger

logger = get_logger(__name__)


class TaskScheduler:
    """
    Generic task scheduler for running recurring and one-time tasks.

    Manages task execution in a background thread with configurable
    intervals and execution times.
    """

    def __init__(self):
        """Initialize the task scheduler with empty task list."""
        self.scheduled_tasks = []
        self.running = False
        self.scheduler_thread = None

    def add_recurring_task(
        self,
        name: str,
        callback: Callable,
        interval_hours: int,
        start_immediately: bool = True,
    ):
        """
        Add a recurring task that runs at specified intervals.

        Args:
            name: Descriptive name for the task
            callback: Function to call when task runs
            interval_hours: Hours between task executions
            start_immediately: If True, run task immediately on first check
        """
        task = {
            "name": name,
            "callback": callback,
            "interval_hours": interval_hours,
            "next_run": datetime.now()
            if start_immediately
            else datetime.now() + timedelta(hours=interval_hours),
            "last_run": None,
        }
        self.scheduled_tasks.append(task)

    def add_one_time_task(self, name: str, callback: Callable, run_at: datetime):
        """
        Add a one-time task that runs at a specific datetime.

        Args:
            name: Descriptive name for the task
            callback: Function to call when task runs
            run_at: Datetime when task should execute
        """
        task = {
            "name": name,
            "callback": callback,
            "interval_hours": None,
            "next_run": run_at,
            "last_run": None,
        }
        self.scheduled_tasks.append(task)

    def start_scheduler(self):
        """
        Start the scheduler in a background thread.

        Begins checking for and executing scheduled tasks.
        Does nothing if scheduler is already running.
        """
        if self.running:
            return

        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler, daemon=True
        )
        self.scheduler_thread.start()

    def stop_scheduler(self):
        """
        Stop the scheduler and wait for thread to finish.

        Sets running flag to False and waits for scheduler thread to complete.
        """
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()

    def _run_scheduler(self):
        """
        Internal scheduler loop that runs in background thread.

        Checks for due tasks every minute and executes them.
        Handles recurring task rescheduling and one-time task removal.
        """
        while self.running:
            now = datetime.now()
            tasks_to_run = []

            for task in self.scheduled_tasks:
                if task["next_run"] <= now:
                    tasks_to_run.append(task)

            for task in tasks_to_run:
                try:
                    task["callback"]()
                    task["last_run"] = now

                    if task["interval_hours"] is not None:
                        task["next_run"] = now + timedelta(hours=task["interval_hours"])
                    else:
                        self.scheduled_tasks.remove(task)

                except (sqlite3.Error, AttributeError, KeyError, ValueError, TypeError) as e:
                    logger.error("Error running scheduled task '%s': %s", task['name'], e, exc_info=True)

            time.sleep(60)  # Check every minute

    def get_upcoming_tasks(self, hours_ahead: int = 24) -> List[Dict]:
        """
        Get list of tasks scheduled to run within specified timeframe.

        Args:
            hours_ahead: Number of hours to look ahead (default 24)

        Returns:
            List[Dict]: Upcoming tasks sorted by next_run time
        """
        cutoff = datetime.now() + timedelta(hours=hours_ahead)
        upcoming = []

        for task in self.scheduled_tasks:
            if task["next_run"] <= cutoff:
                upcoming.append(
                    {
                        "name": task["name"],
                        "next_run": task["next_run"],
                        "type": "recurring" if task["interval_hours"] else "one-time",
                    }
                )

        return sorted(upcoming, key=lambda x: x["next_run"])


class CareReminder:
    """
    Garden care reminder system for automated notifications.

    Manages daily care checks, weather-based recommendations, and
    weekly planning summaries using the TaskScheduler.
    """

    def __init__(self, garden_db, weather_service):
        """
        Initialize care reminder system.

        Args:
            garden_db: GardenDatabase instance for accessing tasks and plants
            weather_service: WeatherService instance for weather-based alerts
        """
        self.garden_db = garden_db
        self.weather_service = weather_service
        self.scheduler = TaskScheduler()
        self.setup_reminders()

    def setup_reminders(self):
        """
        Configure recurring reminder tasks.

        Sets up daily care checks, weather updates, and weekly planning
        tasks with appropriate intervals.
        """
        self.scheduler.add_recurring_task(
            "daily_care_check",
            self.check_daily_care_tasks,
            24,  # Every 24 hours
        )

        self.scheduler.add_recurring_task(
            "weather_update",
            self.update_weather_recommendations,
            6,  # Every 6 hours
        )

        self.scheduler.add_recurring_task(
            "weekly_planning",
            self.generate_weekly_recommendations,
            168,  # Every 7 days (168 hours)
        )

    def check_daily_care_tasks(self):
        """
        Check for garden tasks due today and send notifications.

        Retrieves tasks due within 24 hours and sends reminders
        for each task with plant information.
        """
        due_tasks = self.garden_db.get_care_tasks(due_within_days=1)

        if due_tasks:
            self.send_notification(f"You have {len(due_tasks)} garden tasks due today!")

            for task in due_tasks:
                plant_info = self.garden_db.get_plant_by_id(
                    self.garden_db.get_planted_item(task.planted_item_id).plant_id
                )
                message = f"Time to {task.task_type} your {plant_info.name}"
                self.send_notification(message)

    def update_weather_recommendations(self):
        """
        Check weather conditions and send alerts for extreme conditions.

        Monitors temperature and frost warnings to protect plants.
        """
        current_weather = self.weather_service.current_weather
        if current_weather:
            if current_weather["temperature"] > 90:
                self.send_notification("Hot weather alert! Check plant watering needs.")

            if self.weather_service.check_frost_warning():
                self.send_notification("Frost warning! Protect sensitive plants.")

    def generate_weekly_recommendations(self):
        """
        Generate weekly garden summary with overdue tasks and upcoming harvests.

        Compiles recommendations for garden maintenance and planning.
        """
        recommendations = []

        overdue_tasks = self.garden_db.get_care_tasks(
            due_within_days=-7
        )  # Overdue tasks
        if overdue_tasks:
            recommendations.append(f"{len(overdue_tasks)} overdue tasks need attention")

        upcoming_harvests = self.garden_db.get_care_tasks(due_within_days=14)
        harvest_tasks = [
            task for task in upcoming_harvests if task.task_type == "harvesting"
        ]
        if harvest_tasks:
            recommendations.append(
                f"{len(harvest_tasks)} plants ready for harvest soon"
            )

        if recommendations:
            message = "Weekly garden summary: " + "; ".join(recommendations)
            self.send_notification(message)

    def send_notification(self, message: str):
        """
        Send a notification message to the user.

        Currently logs notification. Can be extended for email, SMS, or push notifications.

        Args:
            message: Notification message to send
        """
        logger.info("Garden Reminder: %s", message)

    def start(self):
        """Start the care reminder system."""
        self.scheduler.start_scheduler()

    def stop(self):
        """Stop the care reminder system."""
        self.scheduler.stop_scheduler()
