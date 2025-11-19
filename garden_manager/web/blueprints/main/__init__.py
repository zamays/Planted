"""
Main blueprint for Planted application.

Handles dashboard, weather, help pages, and test page.
"""

import sqlite3
from flask import Blueprint, render_template, request
import logging
from garden_manager.utils.date_utils import SeasonCalculator
from garden_manager.web.blueprints.utils import get_current_user_id

main_bp = Blueprint('main', __name__)


def init_blueprint(services):
    """
    Initialize the blueprint with required services.
    
    Args:
        services: Dictionary containing service instances
    """
    global garden_db, plant_db, location_service, weather_service, auth_service
    garden_db = services.get('garden_db')
    plant_db = services.get('plant_db')
    location_service = services.get('location_service')
    weather_service = services.get('weather_service')
    auth_service = services.get('auth_service')


@main_bp.route("/")
def dashboard():
    """
    Display the main dashboard with garden overview statistics.

    Shows garden plots count, active plants, upcoming care tasks, current location,
    season information, and weather conditions.

    Returns:
        str: Rendered dashboard HTML template or error message
    """
    try:
        user_id = get_current_user_id()
        plots = garden_db.get_garden_plots(user_id) if garden_db is not None else []
        due_tasks = (
            garden_db.get_care_tasks(due_within_days=7) if garden_db is not None else []
        )

        location_text = (
            location_service.get_location_display()
            if location_service is not None
            else "Unknown Location"
        )
        current_season = SeasonCalculator.get_current_season(
            location_service.current_location["latitude"]
            if location_service is not None and location_service.current_location
            else 40.0
        )

        active_plants_count = (
            garden_db.get_planted_items_count(user_id) if garden_db is not None else 0
        )
        stats = {"plots": len(plots), "active_plants": active_plants_count, "tasks_due": len(due_tasks)}

        # Check if user has location set in database
        user_has_location = False
        if user_id and auth_service:
            user = auth_service.get_user_by_id(user_id)
            user_has_location = user and user.get('location') is not None

        # Check if using default location
        is_default_location = (
            location_service.is_default_location
            if location_service is not None
            else True
        )

        return render_template(
            "dashboard.html",
            stats=stats,
            location=location_text,
            season=current_season.title(),
            weather=weather_service.current_weather
            if weather_service is not None
            else None,
            user_has_location=user_has_location,
            is_default_location=is_default_location,
        )
    except (sqlite3.Error, AttributeError, KeyError) as e:
        logging.error("Dashboard error: %s", e)
        return (
            "<h1>Dashboard Error</h1><p>An internal error occurred. Please try again later.</p>"
        )


@main_bp.route("/weather")
def weather():
    """
    Display current weather conditions and forecast.

    Shows current weather data, multi-day forecast, and location information
    to help with gardening decisions.

    Query Parameters:
        refresh (str): If 'true', bypass cache and fetch fresh weather data

    Returns:
        str: Rendered weather information HTML template or error message
    """
    try:
        # Check if user requested a cache refresh
        refresh = request.args.get("refresh", "false").lower() == "true"

        # Get location
        location_text = (
            location_service.get_location_display()
            if location_service is not None
            else "Unknown Location"
        )

        # Fetch weather data with optional cache bypass
        if weather_service is not None and location_service is not None:
            lat = location_service.current_location.get("latitude", 40.7128)
            lon = location_service.current_location.get("longitude", -74.0060)

            current_weather = weather_service.get_current_weather(lat, lon, bypass_cache=refresh)
            forecast = weather_service.get_forecast(lat, lon, bypass_cache=refresh)
        else:
            current_weather = None
            forecast = []

        # Get cache statistics
        cache_stats = weather_service.get_cache_stats() if weather_service is not None else None

        # Check if using default location
        is_default_location = (
            location_service.is_default_location
            if location_service is not None
            else True
        )

        return render_template(
            "weather.html",
            current_weather=current_weather,
            forecast=forecast,
            location=location_text,
            cache_stats=cache_stats,
            is_default_location=is_default_location,
        )
    except (AttributeError, KeyError) as e:
        logging.error("Weather error", exc_info=True)
        current_weather = (
            weather_service.current_weather
            if weather_service is not None
            else "Unavailable"
        )
        return (
            "<h1>Weather Error</h1>"
            "<p>An internal error has occurred while retrieving weather data.</p>"
            f"<p>Current weather: {current_weather}</p>"
        )


@main_bp.route("/help")
def help_page():
    """
    Display help and user guide for the Planted application.

    Provides comprehensive documentation on how to use all features of the
    garden management system, including keyboard shortcuts and tips.

    Returns:
        str: Rendered help page HTML template
    """
    return render_template("help.html")


@main_bp.route("/test")
def test_page():
    """Simple test page to verify Flask is working"""
    return """
    <h1>🌱 Planted Test Page</h1>
    <p>If you can see this, Flask is working!</p>
    <ul>
        <li><a href="/">Dashboard</a></li>
        <li><a href="/plants">Plants</a></li>
        <li><a href="/garden">Garden</a></li>
        <li><a href="/care">Care</a></li>
    </ul>
    """
