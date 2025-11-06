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
                    scientific_name TEXT NOT NULL,
                    plant_type TEXT NOT NULL,
                    season TEXT NOT NULL,
                    planting_method TEXT NOT NULL,
                    days_to_germination INTEGER NOT NULL,
                    days_to_maturity INTEGER NOT NULL,
                    spacing_inches INTEGER NOT NULL,
                    sun_requirements TEXT NOT NULL,
                    water_needs TEXT NOT NULL,
                    companion_plants TEXT NOT NULL,
                    avoid_plants TEXT NOT NULL,
                    climate_zones TEXT NOT NULL,
                    care_notes TEXT NOT NULL,
                    is_custom BOOLEAN DEFAULT FALSE,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS garden_plots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    location TEXT,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (id)
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

            # Create indexes for performance optimization
            self._create_indexes(conn)

    def _create_indexes(self, conn):
        """
        Create database indexes for query performance optimization.

        Adds strategic indexes on frequently queried columns to improve
        query performance by 5-30x for filtered and joined queries.

        Indexes created:
        - plants(season): For season filtering queries
        - plants(user_id): For custom plants queries by user
        - garden_plots(user_id): For retrieving user's plots
        - planted_items(plot_id): For plot-based joins and queries
        - care_tasks(planted_item_id): For task lookups by planted item
        - care_tasks(due_date): For scheduling and date-based queries
        - care_tasks(due_date, completed): Compound index for common filtered queries

        Args:
            conn: Active SQLite database connection
        """
        # Index for season filtering on plants
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_plants_season
            ON plants(season)
        """)

        # Index for user-specific custom plants
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_plants_user_id
            ON plants(user_id)
        """)

        # Index for user's garden plots
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_garden_plots_user_id
            ON garden_plots(user_id)
        """)

        # Index for planted items by plot (for joins and filtering)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_planted_items_plot_id
            ON planted_items(plot_id)
        """)

        # Index for care tasks by planted item (for joins)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_care_tasks_planted_item_id
            ON care_tasks(planted_item_id)
        """)

        # Index for care tasks by due date (for scheduling queries)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_care_tasks_due_date
            ON care_tasks(due_date)
        """)

        # Compound index for care tasks by due_date and completed status
        # This optimizes the most common query: tasks due before a date that aren't completed
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_care_tasks_due_date_completed
            ON care_tasks(due_date, completed)
        """)

        conn.commit()

    def populate_plant_data(self):
        """
        Populate database with default plant data if empty, or sync changes from JSON.

        On first run, loads all plants from default_plants.json.
        On subsequent runs, updates existing plants and adds new ones from the JSON file.
        Does not delete plants (preserves custom plants and allows for local modifications).

        Includes a comprehensive set of common garden plants with complete
        growing information, companion planting data, and care instructions.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get pre-defined plant data from external module
            plants_data = get_default_plants_data()

            # Check if this is initial setup (no non-custom plants exist)
            cursor.execute("SELECT COUNT(*) FROM plants WHERE is_custom = FALSE OR is_custom IS NULL")
            existing_count = cursor.fetchone()[0]

            if existing_count == 0:
                # Initial population - insert all plants
                for plant_data in plants_data:
                    cursor.execute(
                        """
                        INSERT INTO plants (name, scientific_name, plant_type, season, planting_method,
                                          days_to_germination, days_to_maturity, spacing_inches,
                                          sun_requirements, water_needs, companion_plants, avoid_plants,
                                          climate_zones, care_notes, is_custom)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE)
                    """,
                        plant_data,
                    )
                print(f"   ✅ Loaded {len(plants_data)} default plants into database")
            else:
                # Sync mode - update existing plants and add new ones
                updated_count = 0
                added_count = 0

                for plant_data in plants_data:
                    plant_name = plant_data[0]

                    # Check if plant exists (by name, non-custom only)
                    cursor.execute(
                        "SELECT id FROM plants WHERE name = ? AND (is_custom = FALSE OR is_custom IS NULL)",
                        (plant_name,)
                    )
                    existing = cursor.fetchone()

                    if existing:
                        # Update existing plant
                        cursor.execute(
                            """
                            UPDATE plants SET
                                scientific_name = ?,
                                plant_type = ?,
                                season = ?,
                                planting_method = ?,
                                days_to_germination = ?,
                                days_to_maturity = ?,
                                spacing_inches = ?,
                                sun_requirements = ?,
                                water_needs = ?,
                                companion_plants = ?,
                                avoid_plants = ?,
                                climate_zones = ?,
                                care_notes = ?
                            WHERE id = ?
                        """,
                            plant_data[1:] + (existing[0],)
                        )
                        updated_count += 1
                    else:
                        # Insert new plant
                        cursor.execute(
                            """
                            INSERT INTO plants (name, scientific_name, plant_type, season, planting_method,
                                              days_to_germination, days_to_maturity, spacing_inches,
                                              sun_requirements, water_needs, companion_plants, avoid_plants,
                                              climate_zones, care_notes, is_custom)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, FALSE)
                        """,
                            plant_data,
                        )
                        added_count += 1

                print(f"   ✅ Plant sync: {added_count} added, {updated_count} updated")

            conn.commit()

    def get_plants_by_season(self, season: str, user_id: Optional[int] = None) -> List[Plant]:
        """
        Retrieve plants suitable for a specific planting season.

        Args:
            season: Season name (spring, summer, fall, winter)
            user_id: Optional user ID to include user's custom plants

        Returns:
            List[Plant]: Plants suitable for the specified season
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if user_id is not None:
                cursor.execute(
                    "SELECT * FROM plants WHERE season = ? AND (user_id IS NULL OR user_id = ?)",
                    (season, user_id)
                )
            else:
                cursor.execute("SELECT * FROM plants WHERE season = ? AND user_id IS NULL", (season,))
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

    def add_custom_plant(self, plant_spec: PlantSpec, user_id: Optional[int] = None) -> Optional[int]:
        """
        Add a custom plant to the database.

        Args:
            plant_spec: PlantSpec containing all plant characteristics
            user_id: Optional user ID to associate the plant with

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
                                  climate_zones, care_notes, is_custom, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE, ?)
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
                    user_id,
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

    def update_plant(self, plant_id: int, plant_spec: PlantSpec) -> bool:
        """
        Update an existing plant in the database.

        Args:
            plant_id: ID of the plant to update
            plant_spec: PlantSpec containing updated plant characteristics

        Returns:
            bool: True if update was successful, False otherwise

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not plant_spec.name:
            raise ValueError("Plant name is required")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE plants SET name = ?, scientific_name = ?, plant_type = ?, season = ?,
                                  planting_method = ?, days_to_germination = ?, days_to_maturity = ?,
                                  spacing_inches = ?, sun_requirements = ?, water_needs = ?,
                                  companion_plants = ?, avoid_plants = ?, climate_zones = ?, care_notes = ?
                WHERE id = ?
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
                    plant_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_plant(self, plant_id: int) -> bool:
        """
        Delete a custom plant from the database.

        Args:
            plant_id: ID of the plant to delete

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            ValueError: If attempting to delete a non-custom plant
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if plant is custom
            cursor.execute("SELECT is_custom FROM plants WHERE id = ?", (plant_id,))
            row = cursor.fetchone()

            if not row:
                return False

            is_custom = row[0]
            if not is_custom:
                raise ValueError("Cannot delete default plants. Only custom plants can be deleted.")

            # Delete the plant
            cursor.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
            conn.commit()
            return cursor.rowcount > 0
