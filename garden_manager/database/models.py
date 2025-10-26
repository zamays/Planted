"""
Garden Manager Data Models

Defines dataclass models for all garden-related entities including plants,
garden plots, planted items, and care tasks. These models provide type safety
and structured data representation throughout the application.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class PlantGrowingInfo:
    """Growing parameters for a plant species."""
    season: str
    planting_method: str
    days_to_germination: int
    days_to_maturity: int
    spacing_inches: int


@dataclass
class PlantCareRequirements:
    """Care requirements for a plant species."""
    sun_requirements: str
    water_needs: str
    care_notes: str


@dataclass
class PlantCompatibility:
    """Companion planting and climate compatibility information."""
    companion_plants: List[str]
    avoid_plants: List[str]
    climate_zones: List[int]


@dataclass
class Plant:
    """
    Represents a plant species with growing information and care requirements.

    Attributes:
        id: Unique identifier for the plant
        name: Common name of the plant
        scientific_name: Scientific/botanical name
        plant_type: Category (vegetable, fruit, herb)
        growing: Growing parameters
        care: Care requirements
        compatibility: Companion planting info
        is_custom: Whether this is a user-added custom plant
    """

    id: int
    name: str
    scientific_name: str
    plant_type: str
    growing: PlantGrowingInfo
    care: PlantCareRequirements
    compatibility: PlantCompatibility
    is_custom: bool = False

    # Helper properties for template access
    @property
    def season(self) -> str:
        """Get the planting season."""
        return self.growing.season

    @property
    def days_to_germination(self) -> int:
        """Get days to germination."""
        return self.growing.days_to_germination

    @property
    def days_to_maturity(self) -> int:
        """Get days to maturity."""
        return self.growing.days_to_maturity

    @property
    def spacing_inches(self) -> int:
        """Get required spacing."""
        return self.growing.spacing_inches

    @property
    def planting_method(self) -> str:
        """Get planting method."""
        return self.growing.planting_method

    @property
    def sun_requirements(self) -> str:
        """Get sun requirements."""
        return self.care.sun_requirements

    @property
    def water_needs(self) -> str:
        """Get water needs."""
        return self.care.water_needs

    @property
    def care_notes(self) -> str:
        """Get care notes."""
        return self.care.care_notes

    @property
    def companion_plants(self) -> List[str]:
        """Get companion plants list."""
        return self.compatibility.companion_plants

    @property
    def avoid_plants(self) -> List[str]:
        """Get plants to avoid."""
        return self.compatibility.avoid_plants

    @property
    def climate_zones(self) -> List[int]:
        """Get compatible climate zones."""
        return self.compatibility.climate_zones


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
class PlotPosition:
    """Position coordinates within a garden plot grid."""
    x: int
    y: int


@dataclass
class PlantTimeline:
    """Timeline information for a planted item."""
    planted_date: datetime
    expected_harvest: datetime


@dataclass
class PlantedItem:
    """
    Represents a specific plant instance placed in a garden plot.

    Attributes:
        id: Unique identifier for the planted item
        plant_id: Reference to the Plant species
        plot_id: Reference to the GardenPlot containing this item
        position: Position coordinates within the plot
        timeline: Planting and harvest timeline
        notes: User notes about this specific plant instance
    """

    id: int
    plant_id: int
    plot_id: int
    position: PlotPosition
    timeline: PlantTimeline
    notes: str

    # Helper properties for template access
    @property
    def planted_date(self) -> datetime:
        """Get the planted date from timeline."""
        return self.timeline.planted_date

    @property
    def expected_harvest(self) -> datetime:
        """Get the expected harvest date from timeline."""
        return self.timeline.expected_harvest

    @property
    def x_position(self) -> int:
        """Get the x coordinate from position."""
        return self.position.x

    @property
    def y_position(self) -> int:
        """Get the y coordinate from position."""
        return self.position.y


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


@dataclass
class PlantingInfo:
    """
    Container for planting operation parameters.

    Groups related parameters for planting operations to reduce
    method argument counts.

    Attributes:
        plant_id: ID of the plant species to plant
        plot_id: ID of the garden plot
        x_pos: X coordinate in the plot grid
        y_pos: Y coordinate in the plot grid
        notes: Optional planting notes
        planted_date: Date the plant was planted (optional)
        days_to_maturity: Days until maturity (optional)
    """

    plant_id: int
    plot_id: int
    x_pos: int
    y_pos: int
    notes: str = ""
    planted_date: Optional[datetime] = None
    days_to_maturity: Optional[int] = None


@dataclass
class PlantSpec:
    """
    Specification for creating a new plant species.

    Groups all plant characteristics for custom plant creation
    to reduce method argument counts.

    Attributes:
        name: Common name of the plant
        scientific_name: Scientific/botanical name
        plant_type: Category (vegetable, fruit, herb)
        growing: Growing parameters
        care: Care requirements
        compatibility: Companion planting info
    """

    name: str
    scientific_name: str
    plant_type: str
    growing: PlantGrowingInfo
    care: PlantCareRequirements
    compatibility: PlantCompatibility
