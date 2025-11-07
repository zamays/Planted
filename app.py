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
import webbrowser
import time
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from dotenv import load_dotenv
from garden_manager.database.plant_data import PlantDatabase
from garden_manager.database.garden_db import GardenDatabase
from garden_manager.services.weather_service import WeatherService
from garden_manager.services.location_service import LocationService
from garden_manager.services.scheduler import CareReminder
from garden_manager.services.auth_service import AuthService

# Import blueprints
from garden_manager.web.blueprints.auth import auth_bp, init_blueprint as init_auth_bp
from garden_manager.web.blueprints.plants import plants_bp, init_blueprint as init_plants_bp
from garden_manager.web.blueprints.garden import garden_bp, init_blueprint as init_garden_bp
from garden_manager.web.blueprints.care import care_bp, init_blueprint as init_care_bp
from garden_manager.web.blueprints.api import api_bp, init_blueprint as init_api_bp
from garden_manager.web.blueprints.main import main_bp, init_blueprint as init_main_bp

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

# Initialize CSRF protection
csrf = CSRFProtect(app)

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
        print(f"⚠️ Service initialization warning: {e}")
        # Continue with partially initialized services


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


@app.before_request
def check_auth():
    """Check authentication before each request."""
    # Public routes that don't require authentication
    public_routes = ['auth.login', 'auth.signup', 'auth.guest_mode', 'static']

    if request.endpoint in public_routes:
        return None

    # Check if user is authenticated or in guest mode
    if not session.get('user_id') and not session.get('is_guest'):
        return redirect(url_for('auth.login'))

    # Load user location once per session
    if not session.get('location_loaded'):
        load_user_location()
        session['location_loaded'] = True

    return None


@app.errorhandler(CSRFError)
def handle_csrf_error(e):  # pylint: disable=unused-argument
    """
    Handle CSRF validation errors.

    Args:
        e: CSRFError exception

    Returns:
        Rendered error page with appropriate status code
    """
    return render_template('error.html',
                          error_title='CSRF Validation Failed',
                          error_message='Your session may have expired. Please refresh the page and try again.',
                          error_code=400), 400


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


def register_blueprints():
    """Register all application blueprints."""
    # Check if blueprints are already registered
    if 'auth' in [bp.name for bp in app.blueprints.values()]:
        return  # Already registered
    
    # Create services dictionary for blueprint initialization
    services = {
        'plant_db': plant_db,
        'garden_db': garden_db,
        'location_service': location_service,
        'weather_service': weather_service,
        'care_reminder': care_reminder,
        'auth_service': auth_service
    }

    # Initialize and register blueprints
    init_auth_bp(services)
    app.register_blueprint(auth_bp)

    init_plants_bp(services)
    app.register_blueprint(plants_bp)

    init_garden_bp(services)
    app.register_blueprint(garden_bp)

    init_care_bp(services)
    app.register_blueprint(care_bp)

    init_api_bp(services, limiter)
    app.register_blueprint(api_bp)
    
    # Apply rate limiting to API endpoints
    limiter.limit("100 per hour")(api_bp)

    init_main_bp(services)
    app.register_blueprint(main_bp)
    
    # Apply rate limiting to auth routes after registration
    limiter.limit("5 per minute", methods=["POST"])(app.view_functions['auth.login'])
    limiter.limit("3 per minute", methods=["POST"])(app.view_functions['auth.signup'])


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

    # Register blueprints after services are initialized
    register_blueprints()
    print("   ✅ Blueprints registered successfully")

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
