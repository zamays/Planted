"""
Plant Database Management

Handles plant species data including characteristics, growing requirements,
companion planting information, and care instructions. Provides search
and filtering capabilities for plant selection.
"""

import sqlite3
import json
from typing import List, Optional
from .default_plants_data import get_default_plants_data
from .models import (
    Plant,
    PlantSpec,
    PlantGrowingInfo,
    PlantCareRequirements,
    PlantCompatibility,
)


class PlantDatabase:
    """
    Database interface for plant species information.

    Manages a comprehensive database of plant varieties with growing
    characteristics, companion planting data, and care requirements.
    Includes pre-populated data for common garden plants.
    """

    def __init__(self, db_path: str = "garden.db"):
        """
        Initialize plant database with schema and default data.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
        self.populate_plant_data()

    def init_database(self):
        """
        Create database tables if they don't exist.

        Sets up the complete schema for plants, garden plots, planted items,
        and care tasks with proper foreign key relationships.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    scientific_name TEXT,
                    plant_type TEXT,
                    season TEXT,
                    planting_method TEXT,
                    days_to_germination INTEGER,
                    days_to_maturity INTEGER,
                    spacing_inches INTEGER,
                    sun_requirements TEXT,
                    water_needs TEXT,
                    companion_plants TEXT,
                    avoid_plants TEXT,
                    climate_zones TEXT,
                    care_notes TEXT,
                    is_custom BOOLEAN DEFAULT FALSE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS garden_plots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    location TEXT,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS planted_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plant_id INTEGER,
                    plot_id INTEGER,
                    x_position INTEGER,
                    y_position INTEGER,
                    planted_date DATETIME,
                    expected_harvest DATETIME,
                    notes TEXT,
                    FOREIGN KEY (plant_id) REFERENCES plants (id),
                    FOREIGN KEY (plot_id) REFERENCES garden_plots (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS care_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    planted_item_id INTEGER,
                    task_type TEXT,
                    due_date DATETIME,
                    completed BOOLEAN DEFAULT FALSE,
                    notes TEXT,
                    FOREIGN KEY (planted_item_id) REFERENCES planted_items (id)
                )
            """)

    def populate_plant_data(self):
        """
        Populate database with default plant data if empty.

        Includes a comprehensive set of common garden plants with complete
        growing information, companion planting data, and care instructions.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM plants")
            if cursor.fetchone()[0] > 0:
                return  # Skip if plants already exist

            # Get pre-defined plant data from external module
            plants_data = get_default_plants_data()

            for plant_data in plants_data:
                cursor.execute(
                    """
                    INSERT INTO plants (name, scientific_name, plant_type, season, planting_method,
                                      days_to_germination, days_to_maturity, spacing_inches,
                                      sun_requirements, water_needs, companion_plants, avoid_plants,
                                      climate_zones, care_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    plant_data,
                )

    def get_plants_by_season(self, season: str) -> List[Plant]:
        """
        Retrieve plants suitable for a specific planting season.

        Args:
            season: Season name (spring, summer, fall, winter)

        Returns:
            List[Plant]: Plants suitable for the specified season
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plants WHERE season = ?", (season,))
            return [self._row_to_plant(row) for row in cursor.fetchall()]

    def get_plants_by_type(self, plant_type: str) -> List[Plant]:
        """
        Retrieve plants of a specific type.

        Args:
            plant_type: Type of plant (vegetable, fruit, herb)

        Returns:
            List[Plant]: Plants of the specified type
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plants WHERE plant_type = ?", (plant_type,))
            return [self._row_to_plant(row) for row in cursor.fetchall()]

    def search_plants(self, query: str) -> List[Plant]:
        """
        Search plants by name or scientific name.

        Args:
            query: Search term to match against plant names

        Returns:
            List[Plant]: Plants matching the search query
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM plants WHERE name LIKE ? OR scientific_name LIKE ?",
                (f"%{query}%", f"%{query}%"),
            )
            return [self._row_to_plant(row) for row in cursor.fetchall()]

    def add_custom_plant(self, plant_spec: PlantSpec) -> Optional[int]:
        """
        Add a custom plant to the database.

        Args:
            plant_spec: PlantSpec containing all plant characteristics

        Returns:
            int: ID of the newly created plant

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not plant_spec.name:
            raise ValueError("Plant name is required")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO plants (name, scientific_name, plant_type, season, planting_method,
                                  days_to_germination, days_to_maturity, spacing_inches,
                                  sun_requirements, water_needs, companion_plants, avoid_plants,
                                  climate_zones, care_notes, is_custom)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            """,
                (
                    plant_spec.name,
                    plant_spec.scientific_name,
                    plant_spec.plant_type,
                    plant_spec.growing.season,
                    plant_spec.growing.planting_method,
                    plant_spec.growing.days_to_germination,
                    plant_spec.growing.days_to_maturity,
                    plant_spec.growing.spacing_inches,
                    plant_spec.care.sun_requirements,
                    plant_spec.care.water_needs,
                    json.dumps(plant_spec.compatibility.companion_plants),
                    json.dumps(plant_spec.compatibility.avoid_plants),
                    json.dumps(plant_spec.compatibility.climate_zones),
                    plant_spec.care.care_notes,
                ),
            )

            plant_id = cursor.lastrowid
            conn.commit()
            return plant_id

    def _row_to_plant(self, row) -> Plant:
        """Convert a database row to a Plant object.

        Args:
            row: Database row containing plant data

        Returns:
            Plant: Constructed Plant object

        Raises:
            ValueError: If row data is invalid or missing required fields
        """
        if not row or len(row) < 15:  # Check minimum required fields
            raise ValueError("Invalid row data for plant conversion")

        try:
            growing = PlantGrowingInfo(
                season=row[4],
                planting_method=row[5],
                days_to_germination=row[6],
                days_to_maturity=row[7],
                spacing_inches=row[8],
            )

            care = PlantCareRequirements(
                sun_requirements=row[9],
                water_needs=row[10],
                care_notes=row[14],
            )

            compatibility = PlantCompatibility(
                companion_plants=json.loads(row[11]) if row[11] else [],
                avoid_plants=json.loads(row[12]) if row[12] else [],
                climate_zones=json.loads(row[13]) if row[13] else [],
            )

            return Plant(
                id=row[0],
                name=row[1],
                scientific_name=row[2],
                plant_type=row[3],
                growing=growing,
                care=care,
                compatibility=compatibility,
                is_custom=bool(row[15]) if len(row) > 15 else False,
            )
        except (IndexError, json.JSONDecodeError) as e:
            raise ValueError(f"Error converting row to plant: {str(e)}") from e

    def get_plant_by_id(self, plant_id: int) -> Optional[Plant]:
        """
        Retrieve a specific plant by its ID.

        Args:
            plant_id: Unique identifier of the plant

        Returns:
            Optional[Plant]: The plant if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plants WHERE id = ?", (plant_id,))
            row = cursor.fetchone()
            return self._row_to_plant(row) if row else None
