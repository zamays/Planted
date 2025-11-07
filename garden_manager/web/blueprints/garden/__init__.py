"""
Garden blueprint for Planted application.

Handles garden plot management, viewing, creation, deletion, and planting operations.
"""

import sqlite3
import traceback
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from garden_manager.database.models import PlantingInfo
from garden_manager.web.blueprints.utils import get_current_user_id

garden_bp = Blueprint('garden', __name__, url_prefix='/garden')


def init_blueprint(services):
    """
    Initialize the blueprint with required services.
    
    Args:
        services: Dictionary containing service instances
    """
    global garden_db, plant_db
    garden_db = services.get('garden_db')
    plant_db = services.get('plant_db')


@garden_bp.route("")
def index():
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


@garden_bp.route("/<int:plot_id>")
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
        return "<h1>View Plot Error</h1><p>An internal error occurred while loading the plot.</p>"


@garden_bp.route("/<int:plot_id>/delete", methods=["POST"])
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

        return redirect(url_for("garden.index"))
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

    return redirect(url_for("garden.view_plot", plot_id=plot_id))


def _handle_plant_to_plot_get(plot_id, plot, user_id=None):
    """Handle GET request for plant selection form."""
    x = int(request.args.get("x", 0))
    y = int(request.args.get("y", 0))

    # Validate position
    if not _validate_position_in_bounds(x, y, plot):
        return "<h1>Error</h1><p>Invalid position.</p>"

    # Check if position is already occupied
    if _is_position_occupied(x, y, plot_id):
        return redirect(url_for("garden.view_plot", plot_id=plot_id))

    # Get all available plants
    unique_plants = _get_all_unique_plants(user_id)

    return render_template(
        "plant_to_plot.html", plot=plot, plants=unique_plants, x=x, y=y
    )


@garden_bp.route("/<int:plot_id>/plant", methods=["GET", "POST"])
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
        return "<h1>Plant to Plot Error</h1><p>An internal error occurred while planting to plot. Please try again later.</p>"


@garden_bp.route("/create", methods=["GET", "POST"])
def create():
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
                    return redirect(url_for("garden.view_plot", plot_id=plot_id))
                return redirect(url_for("garden.index"))

            return "<h1>Error</h1><p>Garden database is not initialized.</p>"

        return render_template("create_plot.html")
    except (sqlite3.Error, ValueError, KeyError) as e:
        print(f"Create plot error: {e}")
        return "<h1>Create Plot Error</h1><p>An error occurred while creating the plot. Please try again later.</p>"
