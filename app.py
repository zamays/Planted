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

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
from garden_manager.services.auth_service import AuthService
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

# Initialize rate limiter with memory storage
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# Global service instances - initialized in initialize_services()
# pylint: disable=invalid-name
plant_db = None
garden_db = None
location_service = None
weather_service = None
care_reminder = None
auth_service = None
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
    global plant_db, garden_db, location_service, weather_service, care_reminder, auth_service

    print("🔧 Initializing services...")

    try:
        # Initialize core database services
        plant_db = PlantDatabase()
        garden_db = GardenDatabase()
        location_service = LocationService()
        weather_service = WeatherService()
        auth_service = AuthService()

        print("   ✅ Database services initialized")

        # Set default location (New York) as fallback - do NOT use server IP
        # Users will set their location via browser geolocation or account settings
        location_service.set_manual_location(
            40.7128, -74.0060, {"city": "New York", "state": "NY", "country": "USA"}
        )

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


def get_current_user_id():
    """
    Get the current user ID from session.

    Returns:
        Optional[int]: User ID if logged in, None if guest mode or not logged in
    """
    if session.get('is_guest'):
        return None
    return session.get('user_id')


def is_logged_in():
    """Check if user is logged in (not guest mode)."""
    return session.get('user_id') is not None and not session.get('is_guest')


def load_user_location():
    """Load location for the current user."""
    user_id = get_current_user_id()

    if user_id and auth_service:
        # Load user's saved location
        user = auth_service.get_user_by_id(user_id)
        if user and user.get('location'):
            loc = user['location']
            location_service.set_manual_location(
                loc['latitude'],
                loc['longitude'],
                {
                    'city': loc.get('city', ''),
                    'region': loc.get('region', ''),
                    'country': loc.get('country', '')
                }
            )
            # Also update weather for user's location
            if weather_service is not None:
                weather_service.get_current_weather(
                    loc['latitude'],
                    loc['longitude']
                )
                weather_service.get_forecast(
                    loc['latitude'],
                    loc['longitude']
                )
            return

    # For guest mode or users without location: use default location
    # DO NOT use server IP as this gives wrong location when app is hosted remotely


@app.errorhandler(429)
def ratelimit_handler(error):
    """
    Custom error handler for rate limit exceeded (429) errors.

    Provides clear messaging about rate limits and when users can retry.

    Args:
        error: The RateLimitExceeded error

    Returns:
        JSON response for API endpoints, HTML for web pages
    """
    # Check if this is an API request
    if request.path.startswith('/api/'):
        return jsonify({
            "status": "error",
            "message": "Rate limit exceeded. Please try again later.",
            "retry_after": error.description
        }), 429

    # For web pages, show a simple error page
    return render_template(
        "error.html",
        error_code=429,
        error_title="Too Many Requests",
        error_message="You have made too many requests. Please wait a moment and try again.",
        retry_after=error.description
    ), 429


@app.before_request
def check_auth():
    """Check authentication before each request."""
    # Public routes that don't require authentication
    public_routes = ['login', 'signup', 'guest_mode', 'static']

    if request.endpoint in public_routes:
        return None

    # Check if user is authenticated or in guest mode
    if not session.get('user_id') and not session.get('is_guest'):
        return redirect(url_for('login'))

    # Load user location once per session
    if not session.get('location_loaded'):
        load_user_location()
        session['location_loaded'] = True

    return None


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    """
    User login page and authentication handler.

    GET: Display login form
    POST: Authenticate user and create session
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", error="Please enter username and password")

        if auth_service is None:
            return render_template("login.html", error="Authentication service unavailable")

        user = auth_service.verify_login(username, password)

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_guest'] = False

            # Load user's location
            load_user_location()

            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for('dashboard'))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
@limiter.limit("3 per minute", methods=["POST"])
def signup():
    """
    User registration page and handler.

    GET: Display signup form
    POST: Create new user account
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not username or not email or not password:
            return render_template("signup.html", error="All fields are required")

        if password != confirm_password:
            return render_template("signup.html", error="Passwords do not match")

        if auth_service is None:
            return render_template("signup.html", error="Authentication service unavailable")

        try:
            user_id = auth_service.register_user(username, email, password)

            if user_id is None:
                return render_template("signup.html",
                                      error="Username or email already exists")

            # Auto-login after signup
            session['user_id'] = user_id
            session['username'] = username
            session['is_guest'] = False

            # Location will be detected via browser geolocation on first dashboard load
            # or user can set it in account settings

            flash(f"Welcome to Planted, {username}!", "success")
            return redirect(url_for('dashboard'))

        except ValueError as e:
            return render_template("signup.html", error=str(e))

    return render_template("signup.html")


@app.route("/guest-mode", methods=["GET", "POST"])
def guest_mode():
    """
    Guest mode warning and activation.

    GET: Display warning about guest mode
    POST: Activate guest mode session
    """
    if request.method == "POST":
        session['is_guest'] = True
        session['user_id'] = None
        session['username'] = 'Guest'

        # Use server location for guest mode
        if location_service:
            location_service.set_manual_location(
                40.7128, -74.0060,
                {"city": "New York", "state": "NY", "country": "USA"}
            )

        flash("⚠️ You are in Guest Mode. Your data will not be saved.", "warning")
        return redirect(url_for('dashboard'))

    return render_template("guest_mode.html")


@app.route("/logout")
def logout():
    """Log out current user and clear session."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))


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

        stats = {"plots": len(plots), "active_plants": 0, "tasks_due": len(due_tasks)}

        # Check if user has location set in database
        user_has_location = False
        if user_id and auth_service:
            user = auth_service.get_user_by_id(user_id)
            user_has_location = user and user.get('location') is not None

        return render_template(
            "dashboard.html",
            stats=stats,
            location=location_text,
            season=current_season.title(),
            weather=weather_service.current_weather
            if weather_service is not None
            else None,
            user_has_location=user_has_location,
        )
    except (sqlite3.Error, AttributeError, KeyError) as e:
        print(f"Dashboard error: {e}")
        return (
            f"<h1>Dashboard Error</h1><p>{str(e)}</p><p>Check console for details.</p>"
        )


def _get_plants_by_season_filter(season_filter, user_id=None):
    """Get plants based on season filter."""
    if plant_db is None:
        return []

    if season_filter == "current":
        current_season = SeasonCalculator.get_current_season()
        return plant_db.get_plants_by_season(current_season.lower(), user_id)

    if season_filter == "all":
        all_plants = []
        for season in ["spring", "summer", "fall", "winter"]:
            all_plants.extend(plant_db.get_plants_by_season(season, user_id))
        return all_plants

    return plant_db.get_plants_by_season(season_filter.lower(), user_id)


def _filter_plants_by_type(plants_list, type_filter):
    """Filter plants by type."""
    if type_filter == "all":
        return plants_list
    return [p for p in plants_list if p.plant_type.lower() == type_filter.lower()]


def _filter_plants_by_search(plants_list, search):
    """Filter plants by search term."""
    if not search:
        return plants_list
    return [
        p for p in plants_list
        if search.lower() in p.name.lower() or search.lower() in p.scientific_name.lower()
    ]


def _filter_plants_by_climate(plants_list, climate_zone):
    """Filter plants by climate zone compatibility."""
    suitable_plants = []
    for plant in plants_list:
        if climate_zone in plant.compatibility.climate_zones or not plant.compatibility.climate_zones:
            suitable_plants.append(plant)
    return suitable_plants


def _get_climate_recommendations(climate_zone, current_season):
    """Get seasonal recommendations for the climate zone."""
    if isinstance(climate_zone, int):
        return SeasonCalculator.get_seasonal_recommendations(current_season, climate_zone)
    # Default zone 7 for unknown locations
    return SeasonCalculator.get_seasonal_recommendations(current_season, 7)


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
    try:
        user_id = get_current_user_id()
        season_filter = request.args.get("season", "current")
        type_filter = request.args.get("type", "all")
        search = request.args.get("search", "")

        # Get and filter plants
        plants_list = _get_plants_by_season_filter(season_filter, user_id)
        plants_list = _filter_plants_by_type(plants_list, type_filter)
        plants_list = _filter_plants_by_search(plants_list, search)

        # Filter by climate zone
        climate_zone = location_service.get_climate_zone() if location_service is not None else "Unknown"
        suitable_plants = _filter_plants_by_climate(plants_list, climate_zone)

        # Get recommendations
        current_season = SeasonCalculator.get_current_season()
        recommendations = _get_climate_recommendations(climate_zone, current_season)

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


def _parse_comma_separated_list(form_field_name, form_data):
    """Parse comma-separated list from form data."""
    value_str = form_data.get(form_field_name, "").strip()
    return [item.strip() for item in value_str.split(",") if item.strip()]


def _parse_plant_form_data():
    """
    Parse plant form data from request and return a PlantSpec.

    Returns:
        tuple: (PlantSpec object, error_message or None)
    """
    try:
        # Parse comma-separated lists
        companion_plants = _parse_comma_separated_list("companion_plants", request.form)
        avoid_plants = _parse_comma_separated_list("avoid_plants", request.form)

        # Parse climate zones (must be integers)
        climate_zones_str = request.form.get("climate_zones", "").strip()
        climate_zones = []
        if climate_zones_str:
            try:
                climate_zones = [
                    int(z.strip()) for z in climate_zones_str.split(",") if z.strip()
                ]
            except ValueError:
                return None, "Climate zones must be numbers separated by commas (e.g., 5,6,7)"

        # Parse integer fields with validation
        try:
            days_to_germination = int(request.form.get("days_to_germination", 7))
            days_to_maturity = int(request.form.get("days_to_maturity", 60))
            spacing_inches = int(request.form.get("spacing_inches", 12))
        except ValueError:
            return None, "Days to germination, days to maturity, and spacing must be valid numbers"

        # Create data model objects
        growing = PlantGrowingInfo(
            season=request.form.get("season", "spring"),
            planting_method=request.form.get("planting_method", "seed"),
            days_to_germination=days_to_germination,
            days_to_maturity=days_to_maturity,
            spacing_inches=spacing_inches,
        )

        care = PlantCareRequirements(
            sun_requirements=request.form.get("sun_requirements", "full_sun"),
            water_needs=request.form.get("water_needs", "medium"),
            care_notes=request.form.get("care_notes", "").strip(),
        )

        compatibility = PlantCompatibility(
            companion_plants=companion_plants,
            avoid_plants=avoid_plants,
            climate_zones=climate_zones,
        )

        plant_spec = PlantSpec(
            name=request.form.get("name", "").strip(),
            scientific_name=request.form.get("scientific_name", "").strip(),
            plant_type=request.form.get("plant_type", "vegetable"),
            growing=growing,
            care=care,
            compatibility=compatibility,
        )

        return plant_spec, None
    except (ValueError, KeyError):
        return None, "Invalid form data. Please check your inputs and try again."


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
    try:
        if request.method == "POST":
            if plant_db is None:
                return "<h1>Error</h1><p>Plant database is not initialized.</p>"

            user_id = get_current_user_id()
            plant_spec, error = _parse_plant_form_data()
            if error:
                return f"<h1>Error</h1><p>{error}</p>"

            plant_db.add_custom_plant(plant_spec, user_id)
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


@app.route("/plants/<int:plant_id>/edit", methods=["GET", "POST"])
def edit_plant(plant_id):
    """
    Edit an existing plant.

    GET: Display the edit plant form with current values
    POST: Process form data and update the plant

    Args:
        plant_id: ID of the plant to edit

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
        str: Redirect to plant detail page on success, or form on GET/error
    """
    try:
        if plant_db is None:
            return "<h1>Error</h1><p>Plant database is not initialized.</p>"

        # Get the existing plant
        plant = plant_db.get_plant_by_id(plant_id)
        if not plant:
            return "<h1>Plant Not Found</h1><p>The requested plant does not exist.</p>"

        if request.method == "POST":
            plant_spec, error = _parse_plant_form_data()
            if error:
                return f"<h1>Error</h1><p>{error}</p>"

            plant_db.update_plant(plant_id, plant_spec)
            return redirect(url_for("plant_detail", plant_id=plant_id))

        return render_template("edit_plant.html", plant=plant)
    except (ValueError, sqlite3.Error, KeyError) as e:
        print(f"Edit plant error: {e}")
        error_msg = (
            "Invalid plant data. Please check your inputs and try again."
            if isinstance(e, ValueError)
            else "An error occurred while updating the plant. Please try again later."
        )
        return f"<h1>Edit Plant Error</h1><p>{error_msg}</p>"


@app.route("/plants/<int:plant_id>/delete", methods=["POST"])
def delete_plant(plant_id):
    """
    Delete a custom plant from the database.

    Args:
        plant_id: ID of the plant to delete

    Returns:
        str: Redirect to plants page on success, or error message on failure
    """
    try:
        if plant_db is None:
            return "<h1>Error</h1><p>Plant database is not initialized.</p>"

        success = plant_db.delete_plant(plant_id)
        if success:
            return redirect(url_for("plants"))
        return "<h1>Error</h1><p>Failed to delete plant.</p>"
    except ValueError as e:
        print(f"Delete plant validation error: {e}")
        return "<h1>Delete Plant Error</h1><p>Cannot delete default plants. Only custom plants can be deleted.</p>"
    except sqlite3.Error as e:
        print(f"Delete plant database error: {e}")
        return "<h1>Delete Plant Error</h1><p>An error occurred while deleting the plant. Please try again later.</p>"


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
        user_id = get_current_user_id()
        plots = garden_db.get_garden_plots(user_id) if garden_db is not None else []
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


def _validate_position_in_bounds(x_pos, y_pos, plot):
    """Validate that position is within plot bounds."""
    return (
        0 <= x_pos < plot.width and
        0 <= y_pos < plot.height
    )


def _is_position_occupied(x_pos, y_pos, plot_id):
    """Check if a position in the plot is already occupied."""
    existing_items = garden_db.get_planted_items(plot_id)
    for item in existing_items:
        if item.position.x == x_pos and item.position.y == y_pos:
            return True
    return False


def _get_all_unique_plants(user_id=None):
    """Get all unique plants across all seasons."""
    all_plants = []
    for season in ["spring", "summer", "fall", "winter"]:
        all_plants.extend(plant_db.get_plants_by_season(season, user_id))

    # Remove duplicates and sort
    seen_ids = set()
    unique_plants = []
    for plant in all_plants:
        if plant.id not in seen_ids:
            seen_ids.add(plant.id)
            unique_plants.append(plant)

    unique_plants.sort(key=lambda p: p.name)
    return unique_plants


def _handle_plant_to_plot_post(plot_id, plot):
    """Handle POST request for adding a plant to plot."""
    plant_id_str = request.form.get("plant_id")
    if not plant_id_str:
        return "<h1>Error</h1><p>Plant ID is required.</p>"

    # Parse and validate form data
    try:
        plant_id = int(plant_id_str)
        x_position = int(request.form.get("x_position", "0"))
        y_position = int(request.form.get("y_position", "0"))
    except ValueError:
        return "<h1>Error</h1><p>Plant ID and position coordinates must be valid numbers.</p>"

    notes = request.form.get("notes", "").strip()

    # Validate position is within plot bounds
    if not _validate_position_in_bounds(x_position, y_position, plot):
        return "<h1>Error</h1><p>Position is outside plot bounds.</p>"

    # Check if position is already occupied
    if _is_position_occupied(x_position, y_position, plot_id):
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


def _handle_plant_to_plot_get(plot_id, plot, user_id=None):
    """Handle GET request for plant selection form."""
    x = int(request.args.get("x", 0))
    y = int(request.args.get("y", 0))

    # Validate position
    if not _validate_position_in_bounds(x, y, plot):
        return "<h1>Error</h1><p>Invalid position.</p>"

    # Check if position is already occupied
    if _is_position_occupied(x, y, plot_id):
        return redirect(url_for("view_plot", plot_id=plot_id))

    # Get all available plants
    unique_plants = _get_all_unique_plants(user_id)

    return render_template(
        "plant_to_plot.html", plot=plot, plants=unique_plants, x=x, y=y
    )


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
    try:
        if garden_db is None or plant_db is None:
            return "<h1>Error</h1><p>Database is not initialized.</p>"

        plot = garden_db.get_garden_plot(plot_id)
        if not plot:
            return "<h1>Plot Not Found</h1><p>The requested garden plot does not exist.</p>"

        if request.method == "POST":
            return _handle_plant_to_plot_post(plot_id, plot)

        user_id = get_current_user_id()
        return _handle_plant_to_plot_get(plot_id, plot, user_id)

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
            location = request.form.get("location", "Garden")
            add_plants = request.form.get("add_plants", "no")

            try:
                width = int(request.form.get("width", 4))
                height = int(request.form.get("height", 4))
            except ValueError:
                return "<h1>Error</h1><p>Width and height must be valid numbers.</p>"

            if garden_db is not None:
                user_id = get_current_user_id()
                plot_id = garden_db.create_garden_plot(name, width, height, location, user_id)

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


@app.route("/settings", methods=["GET", "POST"])
@limiter.limit("3 per 10 minutes", methods=["POST"])
def settings():
    """
    User account settings page.

    GET: Display settings form with current user information
    POST: Update user settings (currently only location)

    Returns:
        str: Rendered settings page HTML template
    """
    # Require login
    if not is_logged_in():
        flash("Please log in to access settings.", "error")
        return redirect(url_for('login'))

    user_id = get_current_user_id()

    if auth_service is None:
        return "<h1>Error</h1><p>Authentication service unavailable.</p>"

    user = auth_service.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        # Handle manual location update
        try:
            latitude = float(request.form.get("latitude", ""))
            longitude = float(request.form.get("longitude", ""))
            city = request.form.get("city", "").strip()
            region = request.form.get("region", "").strip()
            country = request.form.get("country", "").strip()

            # Validate coordinates
            if not -90 <= latitude <= 90:
                flash("Latitude must be between -90 and 90", "error")
                return render_template("settings.html", user=user)

            if not -180 <= longitude <= 180:
                flash("Longitude must be between -180 and 180", "error")
                return render_template("settings.html", user=user)

            # Update location
            auth_service.update_user_location(
                user_id, latitude, longitude, city, region, country
            )

            # Update location service for this session
            if location_service is not None:
                location_service.set_manual_location(
                    latitude, longitude,
                    {"city": city, "region": region, "country": country}
                )

                # Update weather for new location
                if weather_service is not None:
                    weather_service.get_current_weather(latitude, longitude)
                    weather_service.get_forecast(latitude, longitude)

            flash("Location updated successfully!", "success")
            return redirect(url_for('settings'))

        except (ValueError, TypeError):
            flash("Invalid latitude or longitude. Please enter valid numbers.", "error")
            return render_template("settings.html", user=user)

    # GET request - display settings
    current_location = None
    climate_zone = None
    if location_service is not None and location_service.current_location:
        current_location = location_service.current_location
        climate_zone = location_service.get_climate_zone()

    return render_template("settings.html", user=user, current_location=current_location, climate_zone=climate_zone)


@app.route("/settings/change-password", methods=["POST"])
def change_password():
    """
    Change user password.

    POST: Process password change request

    Form Data:
        current_password (str): Current password for verification
        new_password (str): New password
        confirm_password (str): New password confirmation

    Returns:
        str: Redirect to settings page with success/error message
    """
    # Require login
    if not is_logged_in():
        flash("Please log in to change password.", "error")
        return redirect(url_for('login'))

    user_id = get_current_user_id()

    if auth_service is None:
        flash("Authentication service unavailable.", "error")
        return redirect(url_for('settings'))

    # Get form data
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Validate inputs
    if not current_password or not new_password or not confirm_password:
        flash("All password fields are required.", "error")
        return redirect(url_for('settings'))

    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for('settings'))

    try:
        # Attempt to change password
        success = auth_service.change_password(user_id, current_password, new_password)

        if success:
            flash("Password changed successfully!", "success")
        else:
            flash("Current password is incorrect.", "error")

    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for('settings'))


@app.route("/settings/update-email", methods=["POST"])
def update_user_email():
    """
    Update user email address.

    POST: Process email update request

    Form Data:
        new_email (str): New email address
        confirm_email (str): Email confirmation

    Returns:
        str: Redirect to settings page with success/error message
    """
    # Require login
    if not is_logged_in():
        flash("Please log in to update email.", "error")
        return redirect(url_for('login'))

    user_id = get_current_user_id()

    if auth_service is None:
        flash("Authentication service unavailable.", "error")
        return redirect(url_for('settings'))

    # Get form data
    new_email = request.form.get("new_email", "").strip()
    confirm_email = request.form.get("confirm_email", "").strip()

    # Validate inputs
    if not new_email or not confirm_email:
        flash("All email fields are required.", "error")
        return redirect(url_for('settings'))

    if new_email != confirm_email:
        flash("Email addresses do not match.", "error")
        return redirect(url_for('settings'))

    try:
        # Attempt to update email
        success = auth_service.update_email(user_id, new_email)

        if success:
            # Update session with new email
            user = auth_service.get_user_by_id(user_id)
            if user:
                session['email'] = user['email']
            flash("Email updated successfully!", "success")
        else:
            flash("This email address is already in use.", "error")

    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for('settings'))


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
@limiter.limit("100 per hour")
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


@app.route("/api/update_location", methods=["POST"])
@limiter.limit("100 per hour")
def update_location():
    """
    Update user location via AJAX API.

    Accepts JSON data with location coordinates and optional location details.
    Can be called from browser geolocation or manual entry.

    JSON Data:
        latitude (float): Geographic latitude
        longitude (float): Geographic longitude
        city (str, optional): City name
        region (str, optional): State/region name
        country (str, optional): Country name

    Returns:
        JSON: Success/error status with message
    """
    try:
        # Check if user is logged in
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "Must be logged in to save location"
            })

        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided."})

        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if latitude is None or longitude is None:
            return jsonify({
                "status": "error",
                "message": "Latitude and longitude are required"
            })

        # Validate coordinates
        try:
            latitude = float(latitude)
            longitude = float(longitude)

            if not (-90 <= latitude <= 90):
                return jsonify({
                    "status": "error",
                    "message": "Latitude must be between -90 and 90"
                })
            if not (-180 <= longitude <= 180):
                return jsonify({
                    "status": "error",
                    "message": "Longitude must be between -180 and 180"
                })
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "Invalid latitude or longitude"
            })

        city = data.get("city", "")
        region = data.get("region", "")
        country = data.get("country", "")

        # Update in database
        if auth_service is None:
            return jsonify({
                "status": "error",
                "message": "Authentication service unavailable"
            })

        auth_service.update_user_location(
            user_id, latitude, longitude, city, region, country
        )

        # Update location service for this session
        if location_service is not None:
            location_service.set_manual_location(
                latitude, longitude,
                {"city": city, "region": region, "country": country}
            )

            # Update weather for new location
            if weather_service is not None:
                weather_service.get_current_weather(latitude, longitude)
                weather_service.get_forecast(latitude, longitude)

        return jsonify({
            "status": "success",
            "message": "Location updated successfully"
        })

    except (sqlite3.Error, ValueError, KeyError, AttributeError) as e:
        print(f"Error updating location: {e}")  # Log for debugging
        return jsonify({"status": "error", "message": "Failed to update location"})


def get_app_configuration():
    """
    Determine application configuration based on environment variables.

    Detects production mode and configures host and port accordingly.
    Production mode is enabled when PORT environment variable is set
    (e.g., on Render.com) or RENDER is explicitly set to 'true'.

    Returns:
        tuple: (is_production, host, port) where:
            - is_production (bool): True if running in production mode
            - host (str): Host to bind to ('0.0.0.0' in production, '127.0.0.1' in dev)
            - port (int): Port to bind to (from PORT env var or 5000 default)

    Environment Variables:
        PORT: Port to bind to (default: 5000)
        RENDER: Set to 'true' for production mode on Render.com
    """
    is_production = os.getenv("RENDER") == "true" or os.getenv("PORT") is not None
    port = int(os.getenv("PORT", "5000"))
    host = "0.0.0.0" if is_production else "127.0.0.1"
    return is_production, host, port


def run_app():
    """
    Initialize services and start the Flask development server.

    Sets up all application services, opens web browser automatically in development,
    and starts the Flask server. Supports both development (local) and production modes.

    The function handles service initialization failures gracefully and
    provides fallback functionality.
    """
    print("🌱 Starting Planted Web App...")

    # Get application configuration
    is_production, host, port = get_app_configuration()

    try:
        initialize_services()
        print("   ✅ All services initialized successfully")
    except (OSError, sqlite3.Error, ValueError, ImportError) as e:
        print(f"   ❌ Service initialization failed: {e}")
        print("   🔧 Starting with limited functionality...")

    # Only open browser in development mode
    if not is_production:
        print("   🌐 Opening browser...")

        # Open browser after a short delay to ensure server is ready
        def open_browser():
            """Background task to open web browser after server startup delay."""
            time.sleep(2)
            try:
                webbrowser.open(f"http://127.0.0.1:{port}")
                print("   ✅ Browser opened")
            except (OSError, webbrowser.Error) as e:
                print(f"   ⚠️ Could not open browser: {e}")
                print(f"   📱 Please manually open: http://127.0.0.1:{port}")

        threading.Thread(target=open_browser, daemon=True).start()

    print(f"   🚀 Server starting at http://{host}:{port}")
    if not is_production:
        print(f"   📄 Test page available at: http://127.0.0.1:{port}/test")

    try:
        app.run(debug=False, host=host, port=port, use_reloader=False)
    except (OSError, RuntimeError) as e:
        print(f"   ❌ Flask server error: {e}")


if __name__ == "__main__":
    run_app()
