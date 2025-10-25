from datetime import datetime, timedelta
from typing import List, Dict, Callable
import threading
import time

class TaskScheduler:
    def __init__(self):
        self.scheduled_tasks = []
        self.running = False
        self.scheduler_thread = None
    
    def add_recurring_task(self, name: str, callback: Callable, 
                          interval_hours: int, start_immediately: bool = True):
        task = {
            'name': name,
            'callback': callback,
            'interval_hours': interval_hours,
            'next_run': datetime.now() if start_immediately else datetime.now() + timedelta(hours=interval_hours),
            'last_run': None
        }
        self.scheduled_tasks.append(task)
    
    def add_one_time_task(self, name: str, callback: Callable, run_at: datetime):
        task = {
            'name': name,
            'callback': callback,
            'interval_hours': None,
            'next_run': run_at,
            'last_run': None
        }
        self.scheduled_tasks.append(task)
    
    def start_scheduler(self):
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
    
    def _run_scheduler(self):
        while self.running:
            now = datetime.now()
            tasks_to_run = []
            
            for task in self.scheduled_tasks:
                if task['next_run'] <= now:
                    tasks_to_run.append(task)
            
            for task in tasks_to_run:
                try:
                    task['callback']()
                    task['last_run'] = now
                    
                    if task['interval_hours'] is not None:
                        task['next_run'] = now + timedelta(hours=task['interval_hours'])
                    else:
                        self.scheduled_tasks.remove(task)
                
                except Exception as e:
                    print(f"Error running scheduled task '{task['name']}': {e}")
            
            time.sleep(60)  # Check every minute
    
    def get_upcoming_tasks(self, hours_ahead: int = 24) -> List[Dict]:
        cutoff = datetime.now() + timedelta(hours=hours_ahead)
        upcoming = []
        
        for task in self.scheduled_tasks:
            if task['next_run'] <= cutoff:
                upcoming.append({
                    'name': task['name'],
                    'next_run': task['next_run'],
                    'type': 'recurring' if task['interval_hours'] else 'one-time'
                })
        
        return sorted(upcoming, key=lambda x: x['next_run'])

class CareReminder:
    def __init__(self, garden_db, weather_service):
        self.garden_db = garden_db
        self.weather_service = weather_service
        self.scheduler = TaskScheduler()
        self.setup_reminders()
    
    def setup_reminders(self):
        self.scheduler.add_recurring_task(
            "daily_care_check",
            self.check_daily_care_tasks,
            24  # Every 24 hours
        )
        
        self.scheduler.add_recurring_task(
            "weather_update",
            self.update_weather_recommendations,
            6   # Every 6 hours
        )
        
        self.scheduler.add_recurring_task(
            "weekly_planning",
            self.generate_weekly_recommendations,
            168  # Every 7 days (168 hours)
        )
    
    def check_daily_care_tasks(self):
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
        current_weather = self.weather_service.current_weather
        if current_weather:
            if current_weather['temperature'] > 90:
                self.send_notification("Hot weather alert! Check plant watering needs.")
            
            if self.weather_service.check_frost_warning():
                self.send_notification("Frost warning! Protect sensitive plants.")
    
    def generate_weekly_recommendations(self):
        recommendations = []
        
        overdue_tasks = self.garden_db.get_care_tasks(due_within_days=-7)  # Overdue tasks
        if overdue_tasks:
            recommendations.append(f"{len(overdue_tasks)} overdue tasks need attention")
        
        upcoming_harvests = self.garden_db.get_care_tasks(due_within_days=14)
        harvest_tasks = [task for task in upcoming_harvests if task.task_type == "harvesting"]
        if harvest_tasks:
            recommendations.append(f"{len(harvest_tasks)} plants ready for harvest soon")
        
        if recommendations:
            message = "Weekly garden summary: " + "; ".join(recommendations)
            self.send_notification(message)
    
    def send_notification(self, message: str):
        print(f"🌱 Garden Reminder: {message}")
    
    def start(self):
        self.scheduler.start_scheduler()
    
    def stop(self):
        self.scheduler.stop_scheduler()