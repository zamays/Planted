"""
Test configuration and fixtures for Planted tests.

This file provides common fixtures and configuration for pytest.
"""

import sys
import os

import pytest

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture
def sample_plant_data():
    """Provide sample plant data for testing."""
    return {
        "name": "Test Tomato",
        "plant_type": "Vegetable",
        "scientific_name": "Solanum lycopersicum",
        "planting_seasons": ["Spring", "Summer"],
        "hardiness_zones": [5, 6, 7, 8, 9],
        "days_to_germination": 7,
        "days_to_maturity": 65,
        "spacing_inches": 24,
        "soil_requirements": "Well-drained, rich soil",
        "light_requirements": "Full sun",
        "water_requirements": "Moderate to high",
    }


@pytest.fixture
def sample_plot_data():
    """Provide sample garden plot data for testing."""
    return {
        "name": "Test Garden Plot",
        "width": 4,
        "height": 4,
        "location": "Backyard",
    }
