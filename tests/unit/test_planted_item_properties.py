"""
Unit tests for PlantedItem property accessors.

Tests that the PlantedItem model provides convenient property access
to nested attributes for template compatibility.
"""

from datetime import datetime
from garden_manager.database.models import PlantedItem, PlotPosition, PlantTimeline


def test_planted_item_planted_date_property():
    """Test that planted_date property returns timeline.planted_date."""
    planted_date = datetime(2024, 3, 15, 10, 30, 0)
    expected_harvest = datetime(2024, 6, 15, 10, 30, 0)
    
    timeline = PlantTimeline(planted_date=planted_date, expected_harvest=expected_harvest)
    position = PlotPosition(x=2, y=3)
    
    item = PlantedItem(
        id=1,
        plant_id=10,
        plot_id=5,
        position=position,
        timeline=timeline,
        notes="Test plant"
    )
    
    assert item.planted_date == planted_date
    assert item.planted_date == item.timeline.planted_date


def test_planted_item_expected_harvest_property():
    """Test that expected_harvest property returns timeline.expected_harvest."""
    planted_date = datetime(2024, 3, 15, 10, 30, 0)
    expected_harvest = datetime(2024, 6, 15, 10, 30, 0)
    
    timeline = PlantTimeline(planted_date=planted_date, expected_harvest=expected_harvest)
    position = PlotPosition(x=2, y=3)
    
    item = PlantedItem(
        id=1,
        plant_id=10,
        plot_id=5,
        position=position,
        timeline=timeline,
        notes="Test plant"
    )
    
    assert item.expected_harvest == expected_harvest
    assert item.expected_harvest == item.timeline.expected_harvest


def test_planted_item_x_position_property():
    """Test that x_position property returns position.x."""
    planted_date = datetime(2024, 3, 15, 10, 30, 0)
    expected_harvest = datetime(2024, 6, 15, 10, 30, 0)
    
    timeline = PlantTimeline(planted_date=planted_date, expected_harvest=expected_harvest)
    position = PlotPosition(x=2, y=3)
    
    item = PlantedItem(
        id=1,
        plant_id=10,
        plot_id=5,
        position=position,
        timeline=timeline,
        notes="Test plant"
    )
    
    assert item.x_position == 2
    assert item.x_position == item.position.x


def test_planted_item_y_position_property():
    """Test that y_position property returns position.y."""
    planted_date = datetime(2024, 3, 15, 10, 30, 0)
    expected_harvest = datetime(2024, 6, 15, 10, 30, 0)
    
    timeline = PlantTimeline(planted_date=planted_date, expected_harvest=expected_harvest)
    position = PlotPosition(x=2, y=3)
    
    item = PlantedItem(
        id=1,
        plant_id=10,
        plot_id=5,
        position=position,
        timeline=timeline,
        notes="Test plant"
    )
    
    assert item.y_position == 3
    assert item.y_position == item.position.y


def test_planted_item_all_properties():
    """Test that all PlantedItem properties work together."""
    planted_date = datetime(2024, 3, 15, 10, 30, 0)
    expected_harvest = datetime(2024, 6, 15, 10, 30, 0)
    
    timeline = PlantTimeline(planted_date=planted_date, expected_harvest=expected_harvest)
    position = PlotPosition(x=5, y=7)
    
    item = PlantedItem(
        id=1,
        plant_id=10,
        plot_id=5,
        position=position,
        timeline=timeline,
        notes="Multi-property test"
    )
    
    # Verify all properties return correct values
    assert item.planted_date == planted_date
    assert item.expected_harvest == expected_harvest
    assert item.x_position == 5
    assert item.y_position == 7
    
    # Verify they match the nested attributes
    assert item.planted_date == item.timeline.planted_date
    assert item.expected_harvest == item.timeline.expected_harvest
    assert item.x_position == item.position.x
    assert item.y_position == item.position.y
