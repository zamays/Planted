#!/usr/bin/env python3
"""
Planted - Garden Management System

A Flask-based web application for managing garden plots, plant care schedules,
and gardening activities. Provides interfaces for tracking plants, weather conditions,
and care tasks with automated scheduling and reminders.
"""

import sys
import os
from pathlib import Path
import threading
from datetime import datetime, timedelta
import webbrowser
import time
import sqlite3
import traceback

from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
from garden_manager.database.plant_data import PlantDatabase
from garden_manager.database.garden_db import GardenDatabase
from garden_manager.database.models import (
    PlantingInfo,
    PlantSpec,
    PlantGrowingInfo,
    PlantCareRequirements,
    PlantCompatibility,
)
from garden_manager.services.weather_service import WeatherService
from garden_manager.services.location_service import LocationService
from garden_manager.services.scheduler import CareReminder
from garden_manager.utils.date_utils import SeasonCalculator

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Create Flask app with proper template and static directories
template_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "garden_manager", "web", "templates"
)
static_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "garden_manager", "web", "static"
)
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "garden_manager_secret_key")

# Global service instances - initialized in initialize_services()
# pylint: disable=invalid-name
plant_db = None
garden_db = None
location_service = None
weather_service = None
care_reminder = None
# pylint: enable=invalid-name


def initialize_services():
    """
    Initialize all application services including databases, location, weather, and care reminders.

    Sets up global service instances and starts background threads for location detection
    and weather data retrieval. Falls back to default location if automatic detection fails.

    Raises:
        Exception: If critical service initialization fails
    """
    # pylint: disable=global-statement
    global plant_db, garden_db, location_service, weather_service, care_reminder

    print("🔧 Initializing services...")

    try:
        # Initialize core database services
        plant_db = PlantDatabase()
        garden_db = GardenDatabase()
        location_service = LocationService()
        weather_service = WeatherService()

        print("   ✅ Database services initialized")

        # Set default location (New York) as fallback
        location_service.set_manual_location(
            40.7128, -74.0060, {"city": "New York", "state": "NY", "country": "USA"}
        )

        # Try to get actual location in background to avoid blocking startup
        def load_location():
            """Background task to load user's actual location and weather data."""
            try:
                if location_service is not None:
                    location_service.get_location_by_ip()
                    if location_service.current_location:
                        lat = location_service.current_location["latitude"]
                        lon = location_service.current_location["longitude"]
                        if weather_service is not None:
                            weather_service.get_current_weather(lat, lon)
                            weather_service.get_forecast(lat, lon)
                print("   ✅ Location and weather data loaded")
            except (OSError, KeyError, ValueError, ConnectionError) as e:
                print(f"   ⚠️ Location/weather loading failed: {e}")

        threading.Thread(target=load_location, daemon=True).start()

        # Initialize care reminder system
        try:
            care_reminder = CareReminder(garden_db, weather_service)
            care_reminder.start()
            print("   ✅ Care reminder system started")
        except (sqlite3.Error, ValueError, AttributeError, OSError) as e:
            print(f"   ⚠️ Care reminder failed: {e}")

    except (OSError, sqlite3.Error, ValueError, ImportError) as e:
        print(f"   ❌ Service initialization failed: {e}")
        raise


@app.route("/")
def dashboard():
    """
    Display the main dashboard with garden overview statistics.

    Shows garden plots count, active plants, upcoming care tasks, current location,
    season information, and weather conditions.

    Returns:
        str: Rendered dashboard HTML template or error message
    """
    try:
        plots = garden_db.get_garden_plots() if garden_db is not None else []
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

        stats = {"plots": len(plots), "active_plants": 0, "tasks_due": len(due_tasks)}

        return render_template(
            "dashboard.html",
            stats=stats,
            location=location_text,
            season=current_season.title(),
            weather=weather_service.current_weather
            if weather_service is not None
            else None,
        )
    except (sqlite3.Error, AttributeError, KeyError) as e:
        print(f"Dashboard error: {e}")
        return (
            f"<h1>Dashboard Error</h1><p>{str(e)}</p><p>Check console for details.</p>"
        )


@app.route("/plants")
def plants():
    """
    Display plant catalog with filtering and search capabilities.

    Supports filtering by season, plant type, and search terms. Shows plants
    suitable for the current climate zone with seasonal recommendations.

    Query Parameters:
        season (str): Filter by planting season (current, spring, summer, fall, winter, all)
        type (str): Filter by plant type (vegetable, fruit, herb, all)
        search (str): Search plants by name or scientific name

    Returns:
        str: Rendered plants catalog HTML template or error message
    """
    # pylint: disable=too-many-branches
    try:
        season_filter = request.args.get("season", "current")
        type_filter = request.args.get("type", "all")
        search = request.args.get("search", "")

        if plant_db is not None:
            if season_filter == "current":
                current_season = SeasonCalculator.get_current_season()
                plants_list = plant_db.get_plants_by_season(current_season.lower())
            elif season_filter == "all":
                # Get all plants
                all_plants = []
                for season in ["spring", "summer", "fall", "winter"]:
                    all_plants.extend(plant_db.get_plants_by_season(season))
                plants_list = all_plants
            else:
                plants_list = plant_db.get_plants_by_season(season_filter.lower())
        else:
            plants_list = []

        # Apply plant type filter (vegetable, fruit, herb)
        if type_filter != "all":
            plants_list = [
                p for p in plants_list if p.plant_type.lower() == type_filter.lower()
            ]

        # Apply search filter (matches name or scientific name)
        if search:
            plants_list = [
                p
                for p in plants_list
                if search.lower() in p.name.lower()
                or search.lower() in p.scientific_name.lower()
            ]

        # Filter plants by climate zone compatibility
        climate_zone = (
            location_service.get_climate_zone()
            if location_service is not None
            else "Unknown"
        )
        suitable_plants = []
        for plant in plants_list:
            # Include plant if it matches current climate zone or has no zone restrictions
            if (
                climate_zone in plant.compatibility.climate_zones
                or not plant.compatibility.climate_zones
            ):
                suitable_plants.append(plant)

        current_season = SeasonCalculator.get_current_season()
        # Ensure climate_zone is an int for recommendations
        if isinstance(climate_zone, int):
            recommendations = SeasonCalculator.get_seasonal_recommendations(
                current_season, climate_zone
            )
        else:
            # Default zone 7 for unknown locations
            recommendations = SeasonCalculator.get_seasonal_recommendations(
                current_season, 7
            )

        return render_template(
            "plants.html",
            plants=suitable_plants,
            current_season=current_season.title(),
            climate_zone=climate_zone,
            recommendations=recommendations,
            filters={"season": season_filter, "type": type_filter, "search": search},
        )
    except (sqlite3.Error, AttributeError, KeyError, ValueError) as e:
        print(f"Plants error: {e}")
        return f"<h1>Plants Error</h1><p>{str(e)}</p>"


@app.route("/plants/add", methods=["GET", "POST"])
def add_plant():
    """
    Add a custom plant to the database.

    GET: Display the add plant form
    POST: Process form data and create a new custom plant

    Form Data (POST):
        name (str): Common name of the plant
        scientific_name (str): Scientific/botanical name
        plant_type (str): Category (vegetable, fruit, herb)
        season (str): Optimal planting season
        planting_method (str): How to plant (seed, transplant, bulb)
        days_to_germination (int): Days from planting to germination
        days_to_maturity (int): Days from planting to harvest
        spacing_inches (int): Required spacing in inches
        sun_requirements (str): Light needs (full_sun, partial_shade, shade)
        water_needs (str): Water requirements (low, medium, high)
        companion_plants (str): Comma-separated list of companion plants
        avoid_plants (str): Comma-separated list of plants to avoid
        climate_zones (str): Comma-separated list of USDA zones
        care_notes (str): Additional care instructions

    Returns:
        str: Redirect to plants page on success, or form on GET/error
    """
    # pylint: disable=too-many-locals
    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            scientific_name = request.form.get("scientific_name", "").strip()
            plant_type = request.form.get("plant_type", "vegetable")
            season = request.form.get("season", "spring")
            planting_method = request.form.get("planting_method", "seed")
            days_to_germination = int(request.form.get("days_to_germination", 7))
            days_to_maturity = int(request.form.get("days_to_maturity", 60))
            spacing_inches = int(request.form.get("spacing_inches", 12))
            sun_requirements = request.form.get("sun_requirements", "full_sun")
            water_needs = request.form.get("water_needs", "medium")
            care_notes = request.form.get("care_notes", "").strip()

            # Parse comma-separated lists
            companion_plants_str = request.form.get("companion_plants", "").strip()
            companion_plants = [
                p.strip() for p in companion_plants_str.split(",") if p.strip()
            ]

            avoid_plants_str = request.form.get("avoid_plants", "").strip()
            avoid_plants = [p.strip() for p in avoid_plants_str.split(",") if p.strip()]

            climate_zones_str = request.form.get("climate_zones", "").strip()
            climate_zones = []
            if climate_zones_str:
                try:
                    climate_zones = [
                        int(z.strip())
                        for z in climate_zones_str.split(",")
                        if z.strip()
                    ]
                except ValueError:
                    return (
                        "<h1>Error</h1><p>Climate zones must be numbers separated by commas "
                        "(e.g., 5,6,7)</p>"
                    )

            if plant_db is None:
                return "<h1>Error</h1><p>Plant database is not initialized.</p>"

            growing = PlantGrowingInfo(
                season=season,
                planting_method=planting_method,
                days_to_germination=days_to_germination,
                days_to_maturity=days_to_maturity,
                spacing_inches=spacing_inches,
            )

            care = PlantCareRequirements(
                sun_requirements=sun_requirements,
                water_needs=water_needs,
                care_notes=care_notes,
            )

            compatibility = PlantCompatibility(
                companion_plants=companion_plants,
                avoid_plants=avoid_plants,
                climate_zones=climate_zones,
            )

            plant_spec = PlantSpec(
                name=name,
                scientific_name=scientific_name,
                plant_type=plant_type,
                growing=growing,
                care=care,
                compatibility=compatibility,
            )
            plant_db.add_custom_plant(plant_spec)
            return redirect(url_for("plants"))

        return render_template("add_plant.html")
    except (sqlite3.Error, ValueError, KeyError) as e:
        print(f"Add plant error: {e}")
        return f"<h1>Add Plant Error</h1><p>{str(e)}</p>"


@app.route("/plants/<int:plant_id>")
def plant_detail(plant_id):
    """
    Display detailed information about a specific plant.

    Args:
        plant_id: ID of the plant to display

    Returns:
        str: Rendered plant detail HTML template or error message
    """
    try:
        plant = plant_db.get_plant_by_id(plant_id) if plant_db is not None else None
        if not plant:
            return "<h1>Plant Not Found</h1><p>The requested plant does not exist.</p>"

        return render_template("plant_detail.html", plant=plant)
    except (sqlite3.Error, AttributeError) as e:
        print(f"Plant detail error: {e}")
        return f"<h1>Plant Detail Error</h1><p>{str(e)}</p>"


@app.route("/garden")
def garden_layout():
    """
    Display garden layout with all created garden plots.

    Shows a visual representation of all garden plots with their dimensions
    and planted items.

    Returns:
        str: Rendered garden layout HTML template or error message
    """
    try:
        plots = garden_db.get_garden_plots() if garden_db is not None else []
        return render_template("garden.html", plots=plots)
    except (sqlite3.Error, AttributeError) as e:
        print(f"Garden error: {e}")
        return f"<h1>Garden Error</h1><p>{str(e)}</p>"


@app.route("/garden/<int:plot_id>")
def view_plot(plot_id):
    """
    Display detailed view of a specific garden plot.

    Shows the plot grid with planted items and allows for plant management.

    Args:
        plot_id: ID of the plot to display

    Returns:
        str: Rendered plot detail HTML template or error message
    """
    try:
        if garden_db is None:
            return "<h1>Error</h1><p>Garden database is not initialized.</p>"

        plot = garden_db.get_garden_plot(plot_id)
        if not plot:
            return "<h1>Plot Not Found</h1><p>The requested garden plot does not exist.</p>"

        planted_items = garden_db.get_planted_items(plot_id)

        # Get plant details for each planted item
        items_with_plants = []
        for item in planted_items:
            plant = (
                plant_db.get_plant_by_id(item.plant_id)
                if plant_db is not None
                else None
            )
            if plant:
                items_with_plants.append({"item": item, "plant": plant})

        return render_template(
            "view_plot.html", plot=plot, planted_items=items_with_plants
        )
    except (sqlite3.Error, AttributeError, KeyError) as e:
        print(f"View plot error: {e}")
        return f"<h1>View Plot Error</h1><p>{str(e)}</p>"


@app.route("/garden/<int:plot_id>/delete", methods=["POST"])
def delete_plot(plot_id):
    """
    Delete a garden plot and all its associated data.

    Args:
        plot_id: ID of the plot to delete

    Returns:
        str: Redirect to garden layout page
    """
    try:
        if garden_db is None:
            return "<h1>Error</h1><p>Garden database is not initialized.</p>"

        success = garden_db.delete_garden_plot(plot_id)
        if not success:
            return "<h1>Plot Not Found</h1><p>The requested garden plot does not exist.</p>"

        return redirect(url_for("garden_layout"))
    except (sqlite3.Error, ValueError) as e:
        print(f"Delete plot error: {e}")
        return f"<h1>Delete Plot Error</h1><p>{str(e)}</p>"


@app.route("/garden/<int:plot_id>/plant", methods=["GET", "POST"])
def plant_to_plot(plot_id):
    """
    Add a plant to a specific position in the garden plot.

    GET: Display plant selection form with position
    POST: Process form and add plant to the plot

    Query Parameters (GET):
        x (int): X coordinate in the plot grid
        y (int): Y coordinate in the plot grid

    Form Data (POST):
        plant_id (int): ID of the plant to add
        x_position (int): X coordinate in the plot grid
        y_position (int): Y coordinate in the plot grid
        notes (str, optional): Notes about this planting

    Returns:
        str: Redirect to plot view on success, or form on GET/error
    """
    # pylint: disable=too-many-locals,too-many-return-statements,too-many-branches
    try:
        if garden_db is None or plant_db is None:
            return "<h1>Error</h1><p>Database is not initialized.</p>"

        plot = garden_db.get_garden_plot(plot_id)
        if not plot:
            return "<h1>Plot Not Found</h1><p>The requested garden plot does not exist.</p>"

        if request.method == "POST":
            plant_id_str = request.form.get("plant_id")
            if not plant_id_str:
                return "<h1>Error</h1><p>Plant ID is required.</p>"
            plant_id = int(plant_id_str)
            try:
                x_position = int(request.form.get("x_position", "0"))
                y_position = int(request.form.get("y_position", "0"))
            except ValueError:
                return "<h1>Error</h1><p>Position coordinates must be integers.</p>"
            notes = request.form.get("notes", "").strip()

            # Validate position is within plot bounds
            if (
                x_position < 0
                or x_position >= plot.width
                or y_position < 0
                or y_position >= plot.height
            ):
                return "<h1>Error</h1><p>Position is outside plot bounds.</p>"

            # Check if position is already occupied
            existing_items = garden_db.get_planted_items(plot_id)
            for item in existing_items:
                if item.position.x == x_position and item.position.y == y_position:
                    return (
                        "<h1>Error</h1><p>This position is already occupied. "
                        "Please choose another square.</p>"
                    )

            # Get plant details for days_to_maturity
            plant = plant_db.get_plant_by_id(plant_id)
            if not plant:
                return "<h1>Error</h1><p>Plant not found.</p>"

            # Add the planted item
            planting_info = PlantingInfo(
                plant_id=plant_id,
                plot_id=plot_id,
                x_pos=x_position,
                y_pos=y_position,
                notes=notes,
                planted_date=datetime.now(),
                days_to_maturity=plant.growing.days_to_maturity,
            )
            garden_db.add_planted_item(planting_info)

            return redirect(url_for("view_plot", plot_id=plot_id))

        # GET request - show plant selection form
        x = int(request.args.get("x", 0))
        y = int(request.args.get("y", 0))

        # Validate position
        if x < 0 or x >= plot.width or y < 0 or y >= plot.height:
            return "<h1>Error</h1><p>Invalid position.</p>"

        # Check if position is already occupied
        existing_items = garden_db.get_planted_items(plot_id)
        for item in existing_items:
            if item.position.x == x and item.position.y == y:
                return redirect(url_for("view_plot", plot_id=plot_id))

        # Get all available plants
        all_plants = []
        for season in ["spring", "summer", "fall", "winter"]:
            all_plants.extend(plant_db.get_plants_by_season(season))

        # Remove duplicates and sort
        seen_ids = set()
        unique_plants = []
        for plant in all_plants:
            if plant.id not in seen_ids:
                seen_ids.add(plant.id)
                unique_plants.append(plant)

        unique_plants.sort(key=lambda p: p.name)

        return render_template(
            "plant_to_plot.html", plot=plot, plants=unique_plants, x=x, y=y
        )

    except (sqlite3.Error, ValueError, KeyError, AttributeError) as e:
        print(f"Plant to plot error: {e}")

        traceback.print_exc()
        return f"<h1>Plant to Plot Error</h1><p>{str(e)}</p>"


@app.route("/garden/create", methods=["GET", "POST"])
def create_plot():
    """
    Create a new garden plot.

    GET: Display the plot creation form
    POST: Process form data and create a new garden plot

    Form Data (POST):
        name (str): Name for the new garden plot
        width (int): Width of the plot in grid units
        height (int): Height of the plot in grid units
        location (str): Physical location description
        add_plants (str): If 'yes', redirect to plot view to add plants

    Returns:
        str: Redirect to garden layout or plot view on success, or creation form on GET/error
    """
    try:
        if request.method == "POST":
            name = request.form.get("name", "New Garden Plot")
            width = int(request.form.get("width", 4))
            height = int(request.form.get("height", 4))
            location = request.form.get("location", "Garden")
            add_plants = request.form.get("add_plants", "no")

            if garden_db is not None:
                plot_id = garden_db.create_garden_plot(name, width, height, location)

                # If user wants to add plants immediately, redirect to plot view
                if add_plants == "yes":
                    return redirect(url_for("view_plot", plot_id=plot_id))
                return redirect(url_for("garden_layout"))

            return "<h1>Error</h1><p>Garden database is not initialized.</p>"

        return render_template("create_plot.html")
    except (sqlite3.Error, ValueError, KeyError) as e:
        print(f"Create plot error: {e}")
        return f"<h1>Create Plot Error</h1><p>{str(e)}</p>"


@app.route("/care")
def care_schedule():
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
        print(f"Care schedule error: {e}")
        return f"<h1>Care Schedule Error</h1><p>{str(e)}</p>"


@app.route("/weather")
def weather():
    """
    Display current weather conditions and forecast.

    Shows current weather data, multi-day forecast, and location information
    to help with gardening decisions.

    Returns:
        str: Rendered weather information HTML template or error message
    """
    try:
        current_weather = (
            weather_service.current_weather if weather_service is not None else None
        )
        forecast = (
            weather_service.forecast
            if weather_service is not None and weather_service.forecast
            else []
        )
        location_text = (
            location_service.get_location_display()
            if location_service is not None
            else "Unknown Location"
        )

        return render_template(
            "weather.html",
            current_weather=current_weather,
            forecast=forecast,
            location=location_text,
        )
    except (AttributeError, KeyError) as e:
        print(f"Weather error: {e}")
        current_weather = (
            weather_service.current_weather
            if weather_service is not None
            else "Unavailable"
        )
        return f"<h1>Weather Error</h1><p>{str(e)}</p><p>Current weather: {current_weather}</p>"


@app.route("/help")
def help_page():
    """
    Display help and user guide for the Planted application.
    
    Provides comprehensive documentation on how to use all features of the
    garden management system, including keyboard shortcuts and tips.
    
    Returns:
        str: Rendered help page HTML template
    """
    return render_template("help.html")


@app.route("/test")
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


@app.route("/api/complete_task", methods=["POST"])
def complete_task():
    """
    Mark a care task as completed via AJAX API.

    Accepts JSON data with task ID and optional completion notes.

    JSON Data:
        task_id (int): ID of the task to mark as completed
        notes (str, optional): Additional notes about task completion

    Returns:
        JSON: Success/error status with message
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided."})
        task_id = data.get("task_id")
        notes = data.get("notes", "Completed via web app")

        if garden_db is None:
            return jsonify(
                {"status": "error", "message": "Garden database is not initialized."}
            )

        garden_db.complete_care_task(task_id, notes)
        return jsonify({"status": "success"})
    except (sqlite3.Error, ValueError, KeyError, AttributeError) as e:
        return jsonify({"status": "error", "message": str(e)})


def run_app():
    """
    Initialize services and start the Flask development server.

    Sets up all application services, opens web browser automatically,
    and starts the Flask server on localhost:5000.

    The function handles service initialization failures gracefully and
    provides fallback functionality.
    """
    print("🌱 Starting Planted Web App...")

    try:
        initialize_services()
        print("   ✅ All services initialized successfully")
    except (OSError, sqlite3.Error, ValueError, ImportError) as e:
        print(f"   ❌ Service initialization failed: {e}")
        print("   🔧 Starting with limited functionality...")

    print("   🌐 Opening browser...")

    # Open browser after a short delay to ensure server is ready
    def open_browser():
        """Background task to open web browser after server startup delay."""
        time.sleep(2)
        try:
            webbrowser.open("http://127.0.0.1:5000")
            print("   ✅ Browser opened")
        except (OSError, webbrowser.Error) as e:
            print(f"   ⚠️ Could not open browser: {e}")
            print("   📱 Please manually open: http://127.0.0.1:5000")

    threading.Thread(target=open_browser, daemon=True).start()

    print("   🚀 Server starting at http://127.0.0.1:5000")
    print("   📄 Test page available at: http://127.0.0.1:5000/test")

    try:
        app.run(debug=False, host="127.0.0.1", port=5000, use_reloader=False)
    except (OSError, RuntimeError) as e:
        print(f"   ❌ Flask server error: {e}")


if __name__ == "__main__":
    run_app()
