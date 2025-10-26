"""
Sample unit tests for Planted application.

This is a placeholder to establish the testing structure.
Contributors should add comprehensive tests for all modules.
"""

from garden_manager.utils.date_utils import SeasonCalculator


def test_season_calc_init():
    """Test that SeasonCalculator can be initialized."""
    calculator = SeasonCalculator()
    assert calculator is not None


def test_sample_plant_data_fixture(sample_plant_data):
    """Test that the sample_plant_data fixture works."""
    assert sample_plant_data["name"] == "Test Tomato"
    assert sample_plant_data["plant_type"] == "Vegetable"
    assert "Spring" in sample_plant_data["planting_seasons"]


def test_sample_plot_data_fixture(sample_plot_data):
    """Test that the sample_plot_data fixture works."""
    assert sample_plot_data["name"] == "Test Garden Plot"
    assert sample_plot_data["width"] == 4
    assert sample_plot_data["height"] == 4
