"""
Garden Manager Data Models

Defines dataclass models for all garden-related entities including plants,
garden plots, planted items, and care tasks. These models provide type safety
and structured data representation throughout the application.
"""

import sqlite3
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Plant:
    """
    Represents a plant species with growing information and care requirements.

    Attributes:
        id: Unique identifier for the plant
        name: Common name of the plant
        scientific_name: Scientific/botanical name
        plant_type: Category (vegetable, fruit, herb)
        season: Optimal planting season (spring, summer, fall, winter)
        planting_method: How to plant (seed, transplant)
        days_to_germination: Days from planting to germination
        days_to_maturity: Days from planting to harvest
        spacing_inches: Required spacing between plants in inches
        sun_requirements: Light needs (full_sun, partial_shade, shade)
        water_needs: Water requirements (low, medium, high)
        companion_plants: List of beneficial companion plants
        avoid_plants: List of plants to avoid growing nearby
        climate_zones: List of suitable USDA hardiness zones
        care_notes: Additional care instructions and tips
        is_custom: Whether this is a user-added custom plant
    """
    id: int
    name: str
    scientific_name: str
    plant_type: str
    season: str
    planting_method: str
    days_to_germination: int
    days_to_maturity: int
    spacing_inches: int
    sun_requirements: str
    water_needs: str
    companion_plants: List[str]
    avoid_plants: List[str]
    climate_zones: List[int]
    care_notes: str
    is_custom: bool = False

@dataclass
class GardenPlot:
    """
    Represents a garden plot where plants can be placed.

    Attributes:
        id: Unique identifier for the plot
        name: User-defined name for the plot
        width: Width of the plot in grid units
        height: Height of the plot in grid units
        location: Physical location description
        created_date: When the plot was created
    """
    id: int
    name: str
    width: int
    height: int
    location: str
    created_date: datetime

@dataclass
class PlantedItem:
    """
    Represents a specific plant instance placed in a garden plot.

    Attributes:
        id: Unique identifier for the planted item
        plant_id: Reference to the Plant species
        plot_id: Reference to the GardenPlot containing this item
        x_position: X coordinate within the plot grid
        y_position: Y coordinate within the plot grid
        planted_date: When the plant was planted
        expected_harvest: Calculated expected harvest date
        notes: User notes about this specific plant instance
    """
    id: int
    plant_id: int
    plot_id: int
    x_position: int
    y_position: int
    planted_date: datetime
    expected_harvest: datetime
    notes: str

@dataclass
class CareTask:
    """
    Represents a care task for a planted item.

    Attributes:
        id: Unique identifier for the task
        planted_item_id: Reference to the PlantedItem needing care
        task_type: Type of care needed (watering, fertilizing, pruning, harvesting)
        due_date: When the task should be completed
        completed: Whether the task has been completed
        notes: Additional notes about the task or completion
    """
    id: int
    planted_item_id: int
    task_type: str
    due_date: datetime
    completed: bool
    notes: str