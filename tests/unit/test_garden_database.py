"""
Unit tests for GardenDatabase class.

Tests cover garden plot management, plant planting, care task creation,
and watering schedule functionality.
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta

import pytest

from garden_manager.database.garden_db import GardenDatabase
from garden_manager.database.plant_data import PlantDatabase
from garden_manager.database.models import PlantingInfo


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    file_descriptor, path = tempfile.mkstemp(suffix=".db")
    os.close(file_descriptor)

    # Initialize with plant data
    _ = PlantDatabase(path)

    yield path

    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def garden_db(temp_db):
    """Create a GardenDatabase instance with test data."""
    return GardenDatabase(temp_db)


@pytest.fixture
def sample_plant_id(temp_db):
    """Get the ID of a sample plant from the database."""
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM plants LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None


class TestGardenPlotCreation:
    """Tests for creating garden plots."""

    def test_create_plot_success(self, garden_db):
        """Test successful creation of a garden plot."""
        plot_id = garden_db.create_garden_plot(
            name="Test Garden",
            width=10,
            height=8,
            location="Backyard"
        )

        assert plot_id is not None
        assert isinstance(plot_id, int)
        assert plot_id > 0

    def test_create_plot_with_minimum_dimensions(self, garden_db):
        """Test creating a plot with minimum valid dimensions."""
        plot_id = garden_db.create_garden_plot(
            name="Small Plot",
            width=1,
            height=1,
            location="Balcony"
        )

        assert plot_id is not None

        # Verify the plot was created correctly
        plot = garden_db.get_garden_plot(plot_id)
        assert plot.name == "Small Plot"
        assert plot.width == 1
        assert plot.height == 1
        assert plot.location == "Balcony"

    def test_create_plot_invalid_width(self, garden_db):
        """Test that creating a plot with invalid width raises ValueError."""
        with pytest.raises(ValueError, match="Width and height must be positive"):
            garden_db.create_garden_plot(
                name="Invalid Plot",
                width=0,
                height=5,
                location="Nowhere"
            )

    def test_create_plot_invalid_height(self, garden_db):
        """Test that creating a plot with invalid height raises ValueError."""
        with pytest.raises(ValueError, match="Width and height must be positive"):
            garden_db.create_garden_plot(
                name="Invalid Plot",
                width=5,
                height=-1,
                location="Nowhere"
            )

    def test_create_multiple_plots(self, garden_db):
        """Test creating multiple plots in sequence."""
        plot_id_1 = garden_db.create_garden_plot(
            name="Plot 1", width=5, height=5, location="Front"
        )
        plot_id_2 = garden_db.create_garden_plot(
            name="Plot 2", width=8, height=6, location="Back"
        )
        plot_id_3 = garden_db.create_garden_plot(
            name="Plot 3", width=4, height=4, location="Side"
        )

        assert plot_id_1 != plot_id_2
        assert plot_id_2 != plot_id_3
        assert plot_id_1 != plot_id_3


class TestGardenPlotRetrieval:
    """Tests for retrieving garden plots."""

    def test_get_plot_by_id(self, garden_db):
        """Test retrieving a plot by its ID."""
        plot_id = garden_db.create_garden_plot(
            name="Retrievable Plot",
            width=6,
            height=7,
            location="Garden"
        )

        plot = garden_db.get_garden_plot(plot_id)

        assert plot is not None
        assert plot.id == plot_id
        assert plot.name == "Retrievable Plot"
        assert plot.width == 6
        assert plot.height == 7
        assert plot.location == "Garden"
        assert isinstance(plot.created_date, datetime)

    def test_get_nonexistent_plot(self, garden_db):
        """Test retrieving a plot that doesn't exist returns None."""
        plot = garden_db.get_garden_plot(99999)
        assert plot is None

    def test_get_all_plots(self, garden_db):
        """Test retrieving all plots."""
        # Create several plots
        garden_db.create_garden_plot("Plot A", 5, 5, "Location A")
        garden_db.create_garden_plot("Plot B", 6, 6, "Location B")
        garden_db.create_garden_plot("Plot C", 7, 7, "Location C")

        plots = garden_db.get_garden_plots()

        assert len(plots) == 3
        # Verify all plots are present
        plot_names = {plot.name for plot in plots}
        assert plot_names == {"Plot A", "Plot B", "Plot C"}

    def test_get_plots_empty_database(self, garden_db):
        """Test getting plots from empty database returns empty list."""
        plots = garden_db.get_garden_plots()
        assert plots == []


class TestGardenPlotDeletion:
    """Tests for deleting garden plots."""

    def test_delete_plot_success(self, garden_db):
        """Test successful deletion of a garden plot."""
        plot_id = garden_db.create_garden_plot(
            name="Doomed Plot",
            width=5,
            height=5,
            location="Temporary"
        )

        # Verify plot exists
        assert garden_db.get_garden_plot(plot_id) is not None

        # Delete the plot
        result = garden_db.delete_garden_plot(plot_id)

        assert result is True
        # Verify plot no longer exists
        assert garden_db.get_garden_plot(plot_id) is None

    def test_delete_nonexistent_plot(self, garden_db):
        """Test deleting a plot that doesn't exist returns False."""
        result = garden_db.delete_garden_plot(99999)
        assert result is False

    def test_delete_plot_with_planted_items(self, garden_db, sample_plant_id):
        """Test deleting a plot cascades to planted items and care tasks."""
        # Create a plot
        plot_id = garden_db.create_garden_plot(
            name="Plot with Plants",
            width=10,
            height=10,
            location="Garden"
        )

        # Add planted items
        planting_info = PlantingInfo(
            plant_id=sample_plant_id,
            plot_id=plot_id,
            x_pos=1,
            y_pos=1,
            notes="Test plant",
            planted_date=datetime.now(),
            days_to_maturity=60
        )
        garden_db.add_planted_item(planting_info)

        # Verify planted item exists
        planted_items = garden_db.get_planted_items(plot_id)
        assert len(planted_items) > 0

        # Delete the plot
        result = garden_db.delete_garden_plot(plot_id)

        assert result is True
        # Verify planted items are also deleted
        planted_items = garden_db.get_planted_items(plot_id)
        assert len(planted_items) == 0


class TestPlantingInPlot:
    """Tests for adding plants to garden plots."""

    def test_add_planted_item(self, garden_db, sample_plant_id):
        """Test adding a planted item to a plot."""
        # Create a plot first
        plot_id = garden_db.create_garden_plot(
            name="Planting Plot",
            width=10,
            height=10,
            location="Garden"
        )

        planted_date = datetime.now()
        planting_info = PlantingInfo(
            plant_id=sample_plant_id,
            plot_id=plot_id,
            x_pos=2,
            y_pos=3,
            notes="Test tomato plant",
            planted_date=planted_date,
            days_to_maturity=65
        )

        planted_item_id = garden_db.add_planted_item(planting_info)

        assert planted_item_id is not None
        assert isinstance(planted_item_id, int)
        assert planted_item_id > 0

    def test_add_planted_item_validation(self, garden_db, sample_plant_id):
        """Test that planted item validation works correctly."""
        plot_id = garden_db.create_garden_plot(
            name="Validation Plot",
            width=5,
            height=5,
            location="Test"
        )

        # Test without days_to_maturity
        with pytest.raises(ValueError, match="days_to_maturity is required"):
            planting_info = PlantingInfo(
                plant_id=sample_plant_id,
                plot_id=plot_id,
                x_pos=1,
                y_pos=1,
                planted_date=datetime.now()
            )
            garden_db.add_planted_item(planting_info)

        # Test without planted_date
        with pytest.raises(ValueError, match="planted_date is required"):
            planting_info = PlantingInfo(
                plant_id=sample_plant_id,
                plot_id=plot_id,
                x_pos=1,
                y_pos=1,
                days_to_maturity=60
            )
            garden_db.add_planted_item(planting_info)

    def test_add_planted_item_invalid_maturity(self, garden_db, sample_plant_id):
        """Test that invalid days_to_maturity raises ValueError."""
        plot_id = garden_db.create_garden_plot(
            name="Invalid Maturity Plot",
            width=5,
            height=5,
            location="Test"
        )

        with pytest.raises(ValueError, match="days_to_maturity must be positive"):
            planting_info = PlantingInfo(
                plant_id=sample_plant_id,
                plot_id=plot_id,
                x_pos=1,
                y_pos=1,
                planted_date=datetime.now(),
                days_to_maturity=0
            )
            garden_db.add_planted_item(planting_info)

    def test_get_planted_items_in_plot(self, garden_db, sample_plant_id):
        """Test retrieving all planted items in a plot."""
        plot_id = garden_db.create_garden_plot(
            name="Multi Plant Plot",
            width=10,
            height=10,
            location="Garden"
        )

        # Add multiple plants
        for i in range(3):
            planting_info = PlantingInfo(
                plant_id=sample_plant_id,
                plot_id=plot_id,
                x_pos=i,
                y_pos=i,
                notes=f"Plant {i}",
                planted_date=datetime.now(),
                days_to_maturity=60
            )
            garden_db.add_planted_item(planting_info)

        planted_items = garden_db.get_planted_items(plot_id)

        assert len(planted_items) == 3
        for item in planted_items:
            assert item.plot_id == plot_id
            assert item.plant_id == sample_plant_id

    def test_get_planted_items_empty_plot(self, garden_db):
        """Test getting planted items from empty plot returns empty list."""
        plot_id = garden_db.create_garden_plot(
            name="Empty Plot",
            width=5,
            height=5,
            location="Empty"
        )

        planted_items = garden_db.get_planted_items(plot_id)
        assert planted_items == []


class TestWateringScheduleAndCareTasks:
    """Tests for watering schedule and care task creation."""

    def test_care_tasks_created_on_planting(self, garden_db, sample_plant_id):
        """Test that care tasks are automatically created when planting."""
        plot_id = garden_db.create_garden_plot(
            name="Care Task Plot",
            width=10,
            height=10,
            location="Garden"
        )

        planted_date = datetime.now()
        planting_info = PlantingInfo(
            plant_id=sample_plant_id,
            plot_id=plot_id,
            x_pos=1,
            y_pos=1,
            notes="Test plant for care tasks",
            planted_date=planted_date,
            days_to_maturity=60
        )

        planted_item_id = garden_db.add_planted_item(planting_info)

        # Get care tasks due within the next 60+ days
        care_tasks = garden_db.get_care_tasks(due_within_days=70)

        # Should have created watering, fertilizing, and harvesting tasks
        assert len(care_tasks) > 0

        # Check for different task types
        task_types = set(task.task_type for task in care_tasks)
        assert "watering" in task_types
        assert "harvesting" in task_types

        # Verify all tasks are for the planted item
        for task in care_tasks:
            assert task.planted_item_id == planted_item_id

    def test_watering_schedule_frequency(self, garden_db, temp_db):
        """Test that watering tasks are scheduled based on water needs."""
        # Create a plot
        plot_id = garden_db.create_garden_plot(
            name="Watering Test Plot",
            width=10,
            height=10,
            location="Garden"
        )

        # Get a plant with specific water needs
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            # Find a plant with high water needs or use the first plant
            cursor.execute("SELECT id FROM plants WHERE water_needs = 'high' LIMIT 1")
            result = cursor.fetchone()
            if result:
                high_water_plant_id = result[0]
            else:
                cursor.execute("SELECT id FROM plants LIMIT 1")
                high_water_plant_id = cursor.fetchone()[0]

        planted_date = datetime.now()
        planting_info = PlantingInfo(
            plant_id=high_water_plant_id,
            plot_id=plot_id,
            x_pos=1,
            y_pos=1,
            notes="High water plant",
            planted_date=planted_date,
            days_to_maturity=60
        )

        planted_item_id = garden_db.add_planted_item(planting_info)

        # Get watering tasks
        care_tasks = garden_db.get_care_tasks(due_within_days=70)
        watering_tasks = [
            task for task in care_tasks
            if task.task_type == "watering" and task.planted_item_id == planted_item_id
        ]

        # Should have multiple watering tasks scheduled
        assert len(watering_tasks) > 0

    def test_fertilizing_tasks_scheduled(self, garden_db, sample_plant_id):
        """Test that fertilizing tasks are scheduled at appropriate intervals."""
        plot_id = garden_db.create_garden_plot(
            name="Fertilizer Plot",
            width=10,
            height=10,
            location="Garden"
        )

        planted_date = datetime.now()
        planting_info = PlantingInfo(
            plant_id=sample_plant_id,
            plot_id=plot_id,
            x_pos=1,
            y_pos=1,
            notes="Fertilizer test plant",
            planted_date=planted_date,
            days_to_maturity=90  # Long enough for all fertilizing tasks
        )

        planted_item_id = garden_db.add_planted_item(planting_info)

        # Get all care tasks
        care_tasks = garden_db.get_care_tasks(due_within_days=100)
        fertilizing_tasks = [
            task for task in care_tasks
            if task.task_type == "fertilizing" and task.planted_item_id == planted_item_id
        ]

        # Should have fertilizing tasks scheduled at 2, 5, and 8 weeks
        # (if maturity date allows)
        assert len(fertilizing_tasks) > 0

    def test_harvest_task_scheduled(self, garden_db, sample_plant_id):
        """Test that a harvest task is scheduled at maturity date."""
        plot_id = garden_db.create_garden_plot(
            name="Harvest Plot",
            width=10,
            height=10,
            location="Garden"
        )

        planted_date = datetime.now()
        days_to_maturity = 60
        planting_info = PlantingInfo(
            plant_id=sample_plant_id,
            plot_id=plot_id,
            x_pos=1,
            y_pos=1,
            notes="Harvest test plant",
            planted_date=planted_date,
            days_to_maturity=days_to_maturity
        )

        planted_item_id = garden_db.add_planted_item(planting_info)

        # Get care tasks
        care_tasks = garden_db.get_care_tasks(due_within_days=70)
        harvest_tasks = [
            task for task in care_tasks
            if task.task_type == "harvesting" and task.planted_item_id == planted_item_id
        ]

        # Should have exactly one harvest task
        assert len(harvest_tasks) == 1

        # Verify harvest date is approximately days_to_maturity days from planting
        harvest_task = harvest_tasks[0]
        expected_harvest = planted_date + timedelta(days=days_to_maturity)
        time_diff = abs((harvest_task.due_date - expected_harvest).total_seconds())

        # Allow 1 second tolerance for timing differences
        assert time_diff < 1

    def test_get_care_tasks_within_timeframe(self, garden_db, sample_plant_id):
        """Test retrieving care tasks within a specific timeframe."""
        plot_id = garden_db.create_garden_plot(
            name="Timeframe Plot",
            width=10,
            height=10,
            location="Garden"
        )

        planted_date = datetime.now()
        planting_info = PlantingInfo(
            plant_id=sample_plant_id,
            plot_id=plot_id,
            x_pos=1,
            y_pos=1,
            notes="Timeframe test",
            planted_date=planted_date,
            days_to_maturity=60
        )

        garden_db.add_planted_item(planting_info)

        # Get tasks due in next 7 days
        tasks_7_days = garden_db.get_care_tasks(due_within_days=7)

        # Get tasks due in next 30 days
        tasks_30_days = garden_db.get_care_tasks(due_within_days=30)

        # Should have more tasks in 30 days than 7 days
        assert len(tasks_30_days) >= len(tasks_7_days)

    def test_complete_care_task(self, garden_db, sample_plant_id):
        """Test marking a care task as completed."""
        plot_id = garden_db.create_garden_plot(
            name="Complete Task Plot",
            width=10,
            height=10,
            location="Garden"
        )

        planted_date = datetime.now()
        planting_info = PlantingInfo(
            plant_id=sample_plant_id,
            plot_id=plot_id,
            x_pos=1,
            y_pos=1,
            notes="Task completion test",
            planted_date=planted_date,
            days_to_maturity=60
        )

        garden_db.add_planted_item(planting_info)

        # Get a care task
        care_tasks = garden_db.get_care_tasks(due_within_days=70)
        assert len(care_tasks) > 0

        task = care_tasks[0]
        assert task.completed is False

        # Complete the task
        completion_notes = "Task completed successfully"
        garden_db.complete_care_task(task.id, completion_notes)

        # Verify task is no longer returned (completed tasks are filtered out)
        remaining_tasks = garden_db.get_care_tasks(due_within_days=70)
        remaining_task_ids = [t.id for t in remaining_tasks]

        # The completed task should not be in the list
        assert task.id not in remaining_task_ids
