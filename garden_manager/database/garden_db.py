"""
Garden Database Management

Handles all database operations for garden plots, planted items, and care tasks.
Provides CRUD operations with proper error handling and data validation.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from .models import GardenPlot, PlantedItem, CareTask, PlantingInfo, PlotPosition, PlantTimeline


class GardenDatabase:
    """
    Database interface for managing garden data.

    Handles garden plots, planted items, and automated care task scheduling.
    Uses SQLite for data persistence with proper transaction management.
    """

    def __init__(self, db_path: str = "garden.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    def create_garden_plot(
        self, name: str, width: int, height: int, location: str, user_id: Optional[int] = None
    ) -> int:
        """
        Create a new garden plot in the database.

        Args:
            name: User-defined name for the plot
            width: Width in grid units (must be positive)
            height: Height in grid units (must be positive)
            location: Physical location description
            user_id: Optional user ID to associate the plot with

        Returns:
            int: ID of the newly created plot

        Raises:
            ValueError: If width/height are not positive or database operation fails
        """
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive numbers")

        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO garden_plots (name, width, height, location, user_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (name, width, height, location, user_id),
                )

                plot_id = cursor.lastrowid
                if plot_id is None:
                    raise ValueError("Failed to create garden plot: no ID returned")

                conn.commit()
                return plot_id
            except sqlite3.Error as e:
                conn.rollback()
                raise ValueError(
                    f"Database error while creating garden plot: {e}"
                ) from e

    def get_garden_plots(self, user_id: Optional[int] = None) -> List[GardenPlot]:
        """
        Retrieve all garden plots ordered by creation date.

        Args:
            user_id: Optional user ID to filter plots by

        Returns:
            List[GardenPlot]: All garden plots, newest first
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if user_id is not None:
                cursor.execute(
                    "SELECT * FROM garden_plots WHERE user_id = ? OR user_id IS NULL ORDER BY created_date DESC",
                    (user_id,)
                )
            else:
                cursor.execute("SELECT * FROM garden_plots WHERE user_id IS NULL ORDER BY created_date DESC")
            rows = cursor.fetchall()
            return [self._row_to_plot(row) for row in rows]

    def get_garden_plot(self, plot_id: int) -> Optional[GardenPlot]:
        """
        Retrieve a specific garden plot by ID.

        Args:
            plot_id: Unique identifier of the plot

        Returns:
            Optional[GardenPlot]: The plot if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM garden_plots WHERE id = ?", (plot_id,))
            row = cursor.fetchone()
            return self._row_to_plot(row) if row else None

    def delete_garden_plot(self, plot_id: int) -> bool:
        """
        Delete a garden plot and all associated data.

        Deletes the plot along with all planted items and their care tasks
        in a cascading manner to maintain database integrity.

        Args:
            plot_id: Unique identifier of the plot to delete

        Returns:
            bool: True if plot was deleted, False if plot was not found

        Raises:
            ValueError: If database operation fails
        """
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.cursor()

                # Check if plot exists
                cursor.execute("SELECT id FROM garden_plots WHERE id = ?", (plot_id,))
                if cursor.fetchone() is None:
                    return False

                # Get all planted items in this plot
                cursor.execute("SELECT id FROM planted_items WHERE plot_id = ?", (plot_id,))
                planted_items = cursor.fetchall()

                # Delete care tasks for each planted item
                for (planted_item_id,) in planted_items:
                    cursor.execute(
                        "DELETE FROM care_tasks WHERE planted_item_id = ?",
                        (planted_item_id,),
                    )

                # Delete all planted items in this plot
                cursor.execute("DELETE FROM planted_items WHERE plot_id = ?", (plot_id,))

                # Delete the plot itself
                cursor.execute("DELETE FROM garden_plots WHERE id = ?", (plot_id,))

                conn.commit()
                return True
            except sqlite3.Error as e:
                conn.rollback()
                raise ValueError(
                    f"Failed to delete garden plot {plot_id}: {e}"
                ) from e

    def plant_item(self, planting_info: PlantingInfo) -> int:
        """
        Plant a new item in a garden plot and create care tasks.

        Automatically calculates harvest date and creates watering, fertilizing,
        and harvesting tasks based on plant requirements.

        Args:
            planting_info: PlantingInfo containing all planting parameters

        Returns:
            int: ID of the newly planted item

        Raises:
            ValueError: If database operation fails
        """
        planted_date = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT days_to_maturity FROM plants WHERE id = ?",
                (planting_info.plant_id,),
            )
            days_to_maturity = cursor.fetchone()[0]
            expected_harvest = planted_date + timedelta(days=days_to_maturity)

            cursor.execute(
                """
                INSERT INTO planted_items (plant_id, plot_id, x_position, y_position,
                                         planted_date, expected_harvest, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    planting_info.plant_id,
                    planting_info.plot_id,
                    planting_info.x_pos,
                    planting_info.y_pos,
                    planted_date,
                    expected_harvest,
                    planting_info.notes,
                ),
            )

            planted_item_id = cursor.lastrowid
            if planted_item_id is None:
                raise ValueError("Failed to create planted item: no ID returned")

            self._create_care_tasks(
                cursor, planted_item_id, planting_info.plant_id, planted_date
            )

            return planted_item_id

    def add_planted_item(self, planting_info: PlantingInfo) -> int:
        """
        Adds a planted item to the database with specified parameters.

        Args:
            planting_info: PlantingInfo containing all planting parameters including
                          planted_date and days_to_maturity

        Returns:
            int: The ID of the newly created planted item.

        Raises:
            ValueError: If days_to_maturity is not positive.
            ValueError: If planted_date is not a datetime object.
            ValueError: If the planted item could not be created in the database.
        """
        if planting_info.days_to_maturity is None:
            raise ValueError("days_to_maturity is required")
        if planting_info.planted_date is None:
            raise ValueError("planted_date is required")

        if planting_info.days_to_maturity <= 0:
            raise ValueError("days_to_maturity must be positive")
        if not isinstance(planting_info.planted_date, datetime):
            raise ValueError("planted_date must be a datetime object")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            expected_harvest = planting_info.planted_date + timedelta(
                days=planting_info.days_to_maturity
            )

            cursor.execute(
                """
                INSERT INTO planted_items (plant_id, plot_id, x_position, y_position,
                                         planted_date, expected_harvest, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    planting_info.plant_id,
                    planting_info.plot_id,
                    planting_info.x_pos,
                    planting_info.y_pos,
                    planting_info.planted_date,
                    expected_harvest,
                    planting_info.notes,
                ),
            )

            planted_item_id = cursor.lastrowid
            if planted_item_id is None:
                raise ValueError("Failed to create planted item: no ID returned")

            self._create_care_tasks(
                cursor,
                planted_item_id,
                planting_info.plant_id,
                planting_info.planted_date,
            )

            return planted_item_id

    def get_planted_items(self, plot_id: int) -> List[PlantedItem]:
        """
        Retrieves all planted items associated with a specific plot from the database.

        Args:
            plot_id (int): The unique identifier of the plot to query planted items for.

        Returns:
            List[PlantedItem]: A list of PlantedItem objects representing all plants in the 
            specified plot.
            Returns an empty list if no planted items are found.

        Example:
            >>> db = GardenDatabase('garden.db')
            >>> planted_items = db.get_planted_items(1)
            >>> print(planted_items)
            [PlantedItem(id=1, plot_id=1, plant_id=2, ...), 
             PlantedItem(id=2, plot_id=1, plant_id=3, ...)]
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM planted_items WHERE plot_id = ?", (plot_id,))
            rows = cursor.fetchall()
            return [self._row_to_planted_item(row) for row in rows]

    def get_planted_items_with_plant_ids(self, plot_id: int) -> List[Tuple[PlantedItem, int]]:
        """
        Retrieve planted items with their plant IDs for efficient batch loading.

        This method returns minimal data to enable batch fetching of plant details,
        avoiding N+1 query problems.

        Args:
            plot_id: ID of the plot to query

        Returns:
            List[Tuple[PlantedItem, int]]: List of (PlantedItem, plant_id) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM planted_items WHERE plot_id = ?", (plot_id,))
            rows = cursor.fetchall()
            return [(self._row_to_planted_item(row), row[1]) for row in rows]

    def get_planted_items_count(self, user_id: Optional[int] = None) -> int:
        """
        Count the total number of planted items across all garden plots for a user.

        Args:
            user_id: Optional user ID to filter by. If provided, counts planted items 
                    in plots belonging to that user (including plots with NULL user_id 
                    for backward compatibility). If None, counts only planted items in 
                    plots with NULL user_id.

        Returns:
            int: Total count of planted items for the specified user
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if user_id is not None:
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM planted_items pi
                    JOIN garden_plots gp ON pi.plot_id = gp.id
                    WHERE gp.user_id = ? OR gp.user_id IS NULL
                    """,
                    (user_id,)
                )
            else:
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM planted_items pi
                    JOIN garden_plots gp ON pi.plot_id = gp.id
                    WHERE gp.user_id IS NULL
                    """
                )
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_care_tasks(self, due_within_days: int = 7) -> List[CareTask]:
        """
        Retrieve care tasks due within a specified timeframe.

        Args:
            due_within_days: Number of days to look ahead (negative for past tasks)

        Returns:
            List[CareTask]: Tasks due within the timeframe, ordered by due date
        """
        cutoff_date = datetime.now() + timedelta(days=due_within_days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM care_tasks 
                WHERE due_date <= ? AND completed = FALSE
                ORDER BY due_date
            """,
                (cutoff_date,),
            )
            rows = cursor.fetchall()
            return [self._row_to_care_task(row) for row in rows]

    def complete_care_task(self, task_id: int, notes: str = ""):
        """
        Mark a care task as completed.

        Args:
            task_id: ID of the task to complete
            notes: Optional completion notes
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE care_tasks 
                SET completed = TRUE, notes = ?
                WHERE id = ?
            """,
                (notes, task_id),
            )

    def _create_care_tasks(
        self, cursor, planted_item_id: int, plant_id: int, planted_date: datetime
    ):
        """
        Create automated care tasks for a newly planted item.

        Generates watering tasks based on plant water needs, fertilizing tasks
        at 2, 5, and 8 week intervals, and a harvest task at maturity.

        Args:
            cursor: Database cursor for transaction
            planted_item_id: ID of the planted item
            plant_id: ID of the plant species
            planted_date: When the plant was planted
        """
        cursor.execute(
            "SELECT water_needs, days_to_maturity FROM plants WHERE id = ?", (plant_id,)
        )
        water_needs, days_to_maturity = cursor.fetchone()

        # Map water needs to watering frequency in days
        water_frequency = {"low": 7, "medium": 3, "high": 2}[water_needs]

        current_date = planted_date
        harvest_date = planted_date + timedelta(days=days_to_maturity)

        # Create watering tasks from planting until harvest
        while current_date < harvest_date:
            current_date += timedelta(days=water_frequency)
            cursor.execute(
                """
                INSERT INTO care_tasks (planted_item_id, task_type, due_date)
                VALUES (?, ?, ?)
            """,
                (planted_item_id, "watering", current_date),
            )

        # Schedule fertilizing at 2, 5, and 8 weeks after planting
        fertilize_dates = [
            planted_date + timedelta(days=14),  # 2 weeks
            planted_date + timedelta(days=35),  # 5 weeks
            planted_date + timedelta(days=56),  # 8 weeks
        ]

        # Only create fertilizing tasks that occur before harvest
        for fert_date in fertilize_dates:
            if fert_date < harvest_date:
                cursor.execute(
                    """
                    INSERT INTO care_tasks (planted_item_id, task_type, due_date)
                    VALUES (?, ?, ?)
                """,
                    (planted_item_id, "fertilizing", fert_date),
                )

        cursor.execute(
            """
            INSERT INTO care_tasks (planted_item_id, task_type, due_date)
            VALUES (?, ?, ?)
        """,
            (planted_item_id, "harvesting", harvest_date),
        )

    def _row_to_plot(self, row) -> GardenPlot:
        return GardenPlot(
            id=row[0],
            name=row[1],
            width=row[2],
            height=row[3],
            location=row[4],
            created_date=datetime.fromisoformat(row[5]),
        )

    def _row_to_planted_item(self, row) -> PlantedItem:
        position = PlotPosition(x=row[3], y=row[4])
        timeline = PlantTimeline(
            planted_date=datetime.fromisoformat(row[5]),
            expected_harvest=datetime.fromisoformat(row[6]),
        )
        return PlantedItem(
            id=row[0],
            plant_id=row[1],
            plot_id=row[2],
            position=position,
            timeline=timeline,
            notes=row[7],
        )

    def _row_to_care_task(self, row) -> CareTask:
        return CareTask(
            id=row[0],
            planted_item_id=row[1],
            task_type=row[2],
            due_date=datetime.fromisoformat(row[3]),
            completed=bool(row[4]),
            notes=row[5] or "",
        )
