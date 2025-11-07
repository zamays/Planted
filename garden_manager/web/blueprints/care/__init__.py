"""
Care blueprint for Planted application.

Handles care schedule viewing and task management.
"""

import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request
import logging

care_bp = Blueprint('care', __name__, url_prefix='/care')


def init_blueprint(services):
    """
    Initialize the blueprint with required services.
    
    Args:
        services: Dictionary containing service instances
    """
    global garden_db, weather_service
    garden_db = services.get('garden_db')
    weather_service = services.get('weather_service')


@care_bp.route("")
def index():
    """
    Display care schedule with upcoming and overdue tasks.

    Shows care tasks grouped by date with filtering options. Includes
    weather information to help with care decisions.

    Query Parameters:
        filter (str): Filter tasks by timeframe (today, week, overdue, month)

    Returns:
        str: Rendered care schedule HTML template or error message
    """
    try:
        filter_type = request.args.get("filter", "week")

        if garden_db is None:
            tasks = []
        else:
            if filter_type == "today":
                tasks = [
                    t
                    for t in garden_db.get_care_tasks(due_within_days=1)
                    if t.due_date.date() == datetime.now().date()
                ]
            elif filter_type == "week":
                tasks = garden_db.get_care_tasks(due_within_days=7)
            elif filter_type == "overdue":
                all_tasks = garden_db.get_care_tasks(due_within_days=-365)
                tasks = [
                    t
                    for t in all_tasks
                    if t.due_date < datetime.now() and not t.completed
                ]
            else:
                tasks = garden_db.get_care_tasks(due_within_days=30)

        # Group care tasks by relative date for better organization
        grouped_tasks = {}
        now = datetime.now()

        for task in tasks:
            task_date = task.due_date.date()

            # Create human-friendly date labels
            if task_date == now.date():
                date_key = "Today"
            elif task_date == (now.date() + timedelta(days=1)):
                date_key = "Tomorrow"
            elif task_date < now.date():
                # Calculate how many days overdue
                days_ago = (now.date() - task_date).days
                date_key = f"{days_ago} days ago (Overdue)"
            else:
                # Future dates get full date formatting
                date_key = task_date.strftime("%B %d, %Y")

            # Group tasks under their date labels
            if date_key not in grouped_tasks:
                grouped_tasks[date_key] = []
            grouped_tasks[date_key].append(task)

        current_weather = (
            weather_service.current_weather if weather_service is not None else None
        )
        return render_template(
            "care.html",
            grouped_tasks=grouped_tasks,
            filter_type=filter_type,
            weather=current_weather,
        )
    except (sqlite3.Error, AttributeError, KeyError, ValueError) as e:
        logging.error("Care schedule error", exc_info=True)
        return "<h1>Care Schedule Error</h1><p>An internal error has occurred.</p>"
