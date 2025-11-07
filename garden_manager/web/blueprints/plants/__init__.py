"""
Plants blueprint for Planted application.

Handles plant catalog browsing, searching, adding custom plants, and managing plant details.
"""

import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for
import logging

logging.basicConfig(level=logging.INFO)
from garden_manager.database.models import PlantSpec, PlantGrowingInfo, PlantCareRequirements, PlantCompatibility
from garden_manager.utils.date_utils import SeasonCalculator
from garden_manager.web.blueprints.utils import get_current_user_id

plants_bp = Blueprint('plants', __name__, url_prefix='/plants')


def init_blueprint(services):
    """
    Initialize the blueprint with required services.
    
    Args:
        services: Dictionary containing service instances
    """
    global plant_db, location_service
    plant_db = services.get('plant_db')
    location_service = services.get('location_service')


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


@plants_bp.route("")
def index():
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
        logging.exception("Exception in plants index route")
        return "<h1>Plants Error</h1><p>An internal error occurred. Please try again later.</p>"


@plants_bp.route("/add", methods=["GET", "POST"])
def add():
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
            return redirect(url_for("plants.index"))

        return render_template("add_plant.html")
    except (sqlite3.Error, ValueError, KeyError) as e:
        print(f"Add plant error: {e}")
        return f"<h1>Add Plant Error</h1><p>{str(e)}</p>"


@plants_bp.route("/<int:plant_id>")
def detail(plant_id):
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


@plants_bp.route("/<int:plant_id>/edit", methods=["GET", "POST"])
def edit(plant_id):
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
            return redirect(url_for("plants.detail", plant_id=plant_id))

        return render_template("edit_plant.html", plant=plant)
    except (ValueError, sqlite3.Error, KeyError) as e:
        print(f"Edit plant error: {e}")
        error_msg = (
            "Invalid plant data. Please check your inputs and try again."
            if isinstance(e, ValueError)
            else "An error occurred while updating the plant. Please try again later."
        )
        return f"<h1>Edit Plant Error</h1><p>{error_msg}</p>"


@plants_bp.route("/<int:plant_id>/delete", methods=["POST"])
def delete(plant_id):
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
            return redirect(url_for("plants.index"))
        return "<h1>Error</h1><p>Failed to delete plant.</p>"
    except ValueError as e:
        print(f"Delete plant validation error: {e}")
        return "<h1>Delete Plant Error</h1><p>Cannot delete default plants. Only custom plants can be deleted.</p>"
    except sqlite3.Error as e:
        print(f"Delete plant database error: {e}")
        return "<h1>Delete Plant Error</h1><p>An error occurred while deleting the plant. Please try again later.</p>"
