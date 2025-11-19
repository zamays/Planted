"""
API blueprint for Planted application.

Handles AJAX API endpoints for task completion, location updates, and cache management.
"""

import sqlite3
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)
from garden_manager.web.blueprints.utils import get_current_user_id

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global limiter instance set during initialization
limiter = None


def init_blueprint(services, limiter_instance):
    """
    Initialize the blueprint with required services.
    
    Args:
        services: Dictionary containing service instances
        limiter_instance: Flask-Limiter instance for rate limiting
    """
    global garden_db, auth_service, location_service, weather_service, limiter
    garden_db = services.get('garden_db')
    auth_service = services.get('auth_service')
    location_service = services.get('location_service')
    weather_service = services.get('weather_service')
    limiter = limiter_instance


@api_bp.route("/complete_task", methods=["POST"])
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
        logger.error("Exception in complete_task: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Failed to complete task."})


@api_bp.route("/update_location", methods=["POST"])
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

        # Update location service for this session (with reverse geocoding if needed)
        location_result = None
        if location_service is not None:
            location_result = location_service.set_manual_location(
                latitude, longitude,
                {"city": city, "region": region, "country": country},
                is_default=False  # User updated location via API
            )

            # Use the geocoded location data (may have been enriched with city info)
            if location_result:
                city = location_result.get("city", city)
                region = location_result.get("region", region)
                country = location_result.get("country", country)

            # Clear weather cache and fetch fresh data for new location
            if weather_service is not None:
                if hasattr(weather_service, 'clear_cache'):
                    weather_service.clear_cache()
                weather_service.get_current_weather(latitude, longitude)
                weather_service.get_forecast(latitude, longitude)

        # Update in database with potentially geocoded city information
        if auth_service is None:
            return jsonify({
                "status": "error",
                "message": "Authentication service unavailable"
            })

        auth_service.update_user_location(
            user_id, latitude, longitude, city, region, country
        )

        # Build location display string for confirmation
        location_display = ""
        geocoding_warning = ""
        if city and region:
            location_display = f"{city}, {region}"
        elif city and country:
            location_display = f"{city}, {country}"
        elif city:
            location_display = city
        elif region and country:
            location_display = f"{region}, {country}"
        elif country:
            location_display = country
        else:
            # Geocoding failed to find a location name
            geocoding_warning = "We saved your coordinates but couldn't determine your city name. You can add it manually in Settings."

        response = {
            "status": "success",
            "message": "Location updated successfully",
            "location": location_display
        }
        if geocoding_warning:
            response["warning"] = geocoding_warning

        return jsonify(response)

    except (sqlite3.Error, ValueError, KeyError, AttributeError) as e:
        logger.error("Error updating location: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Failed to update location"})


@api_bp.route("/cache_stats", methods=["GET"])
def get_cache_stats():
    """
    Get weather cache statistics via AJAX API.

    Returns cache performance metrics including hit rate, API calls saved, etc.

    Returns:
        JSON: Cache statistics including hits, misses, hit rate, and cache sizes
    """
    try:
        if weather_service is None:
            return jsonify({
                "status": "error",
                "message": "Weather service is not initialized."
            })

        stats = weather_service.get_cache_stats()
        return jsonify({
            "status": "success",
            "stats": stats
        })
    except (AttributeError, KeyError):
        return jsonify({"status": "error", "message": "Failed to retrieve cache statistics"})


@api_bp.route("/clear_cache", methods=["POST"])
def clear_weather_cache():
    """
    Clear weather cache via AJAX API.

    Forces fresh API calls on next weather data request.
    Useful after location changes or for manual refresh.

    Returns:
        JSON: Success/error status with message
    """
    try:
        if weather_service is None:
            return jsonify({
                "status": "error",
                "message": "Weather service is not initialized."
            })

        weather_service.clear_cache()
        return jsonify({
            "status": "success",
            "message": "Weather cache cleared successfully"
        })
    except (AttributeError, KeyError):
        return jsonify({"status": "error", "message": "Failed to clear cache"})


# API-specific error handlers that return JSON responses
@api_bp.errorhandler(404)
def api_not_found(e):  # pylint: disable=unused-argument
    """
    Handle 404 errors for API endpoints with JSON response.

    Args:
        e: NotFound exception

    Returns:
        JSON error response with 404 status
    """
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status': 404
    }), 404


@api_bp.errorhandler(403)
def api_forbidden(e):  # pylint: disable=unused-argument
    """
    Handle 403 errors for API endpoints with JSON response.

    Args:
        e: Forbidden exception

    Returns:
        JSON error response with 403 status
    """
    return jsonify({
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource',
        'status': 403
    }), 403


@api_bp.errorhandler(500)
def api_internal_error(e):
    """
    Handle 500 errors for API endpoints with JSON response.

    Args:
        e: Internal server error exception

    Returns:
        JSON error response with 500 status
    """
    logger.error("API internal server error: %s", e, exc_info=True)
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An internal error occurred while processing your request',
        'status': 500
    }), 500


@api_bp.errorhandler(400)
def api_bad_request(e):  # pylint: disable=unused-argument
    """
    Handle 400 Bad Request errors for API endpoints with JSON response.

    Args:
        e: Bad request exception

    Returns:
        JSON error response with 400 status
    """
    return jsonify({
        'error': 'Bad Request',
        'message': 'The request could not be understood or was missing required parameters',
        'status': 400
    }), 400
