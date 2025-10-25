"""
Garden Database Management

Handles all database operations for garden plots, planted items, and care tasks.
Provides CRUD operations with proper error handling and data validation.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from .models import GardenPlot, PlantedItem, CareTask

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
    
    def create_garden_plot(self, name: str, width: int, height: int, location: str) -> int:
        """
        Create a new garden plot in the database.

        Args:
            name: User-defined name for the plot
            width: Width in grid units (must be positive)
            height: Height in grid units (must be positive)
            location: Physical location description

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
                cursor.execute('''
                    INSERT INTO garden_plots (name, width, height, location)
                    VALUES (?, ?, ?, ?)
                ''', (name, width, height, location))
                
                plot_id = cursor.lastrowid
                if plot_id is None:
                    raise ValueError("Failed to create garden plot: no ID returned")
                
                conn.commit()
                return plot_id
            except sqlite3.Error as e:
                conn.rollback()
                raise ValueError(f"Database error while creating garden plot: {e}")
    
    def get_garden_plots(self) -> List[GardenPlot]:
        """
        Retrieve all garden plots ordered by creation date.

        Returns:
            List[GardenPlot]: All garden plots, newest first
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM garden_plots ORDER BY created_date DESC")
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
    
    def plant_item(self, plant_id: int, plot_id: int, x_pos: int, y_pos: int, notes: str = "") -> int:
        """
        Plant a new item in a garden plot and create care tasks.

        Automatically calculates harvest date and creates watering, fertilizing,
        and harvesting tasks based on plant requirements.

        Args:
            plant_id: ID of the plant species to plant
            plot_id: ID of the garden plot
            x_pos: X coordinate in the plot grid
            y_pos: Y coordinate in the plot grid
            notes: Optional planting notes

        Returns:
            int: ID of the newly planted item

        Raises:
            ValueError: If database operation fails
        """
        planted_date = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT days_to_maturity FROM plants WHERE id = ?", (plant_id,))
            days_to_maturity = cursor.fetchone()[0]
            expected_harvest = planted_date + timedelta(days=days_to_maturity)
            
            cursor.execute('''
                INSERT INTO planted_items (plant_id, plot_id, x_position, y_position, 
                                         planted_date, expected_harvest, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (plant_id, plot_id, x_pos, y_pos, planted_date, expected_harvest, notes))
            
            planted_item_id = cursor.lastrowid
            if planted_item_id is None:
                raise ValueError("Failed to create planted item: no ID returned")
            
            self._create_care_tasks(cursor, planted_item_id, plant_id, planted_date)
            
            return planted_item_id
    
    def add_planted_item(self, plant_id: int, plot_id: int, x_pos: int, y_pos: int, 
                    planted_date: datetime, days_to_maturity: int, notes: str = "") -> int:
        if not all(isinstance(x, int) for x in (plant_id, plot_id, x_pos, y_pos, days_to_maturity)):
            raise ValueError("Invalid input: plant_id, plot_id, x_pos, y_pos, and days_to_maturity must be integers")
        if days_to_maturity <= 0:
            raise ValueError("days_to_maturity must be positive")
        if not isinstance(planted_date, datetime):
            raise ValueError("planted_date must be a datetime object")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            expected_harvest = planted_date + timedelta(days=days_to_maturity)
            
            cursor.execute('''
                INSERT INTO planted_items (plant_id, plot_id, x_position, y_position, 
                                         planted_date, expected_harvest, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (plant_id, plot_id, x_pos, y_pos, planted_date, expected_harvest, notes))
            
            planted_item_id = cursor.lastrowid
            if planted_item_id is None:
                raise ValueError("Failed to create planted item: no ID returned")
            
            self._create_care_tasks(cursor, planted_item_id, plant_id, planted_date)
            
            return planted_item_id
    
    def get_planted_items(self, plot_id: int) -> List[PlantedItem]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM planted_items WHERE plot_id = ?", (plot_id,))
            rows = cursor.fetchall()
            return [self._row_to_planted_item(row) for row in rows]
    
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
            cursor.execute('''
                SELECT * FROM care_tasks 
                WHERE due_date <= ? AND completed = FALSE
                ORDER BY due_date
            ''', (cutoff_date,))
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
            cursor.execute('''
                UPDATE care_tasks 
                SET completed = TRUE, notes = ?
                WHERE id = ?
            ''', (notes, task_id))
    
    def _create_care_tasks(self, cursor, planted_item_id: int, plant_id: int, planted_date: datetime):
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
        cursor.execute("SELECT water_needs, days_to_maturity FROM plants WHERE id = ?", (plant_id,))
        water_needs, days_to_maturity = cursor.fetchone()
        
        # Map water needs to watering frequency in days
        water_frequency = {"low": 7, "medium": 3, "high": 2}[water_needs]

        current_date = planted_date
        harvest_date = planted_date + timedelta(days=days_to_maturity)

        # Create watering tasks from planting until harvest
        while current_date < harvest_date:
            current_date += timedelta(days=water_frequency)
            cursor.execute('''
                INSERT INTO care_tasks (planted_item_id, task_type, due_date)
                VALUES (?, ?, ?)
            ''', (planted_item_id, "watering", current_date))

        # Schedule fertilizing at 2, 5, and 8 weeks after planting
        fertilize_dates = [
            planted_date + timedelta(days=14),   # 2 weeks
            planted_date + timedelta(days=35),   # 5 weeks
            planted_date + timedelta(days=56)    # 8 weeks
        ]

        # Only create fertilizing tasks that occur before harvest
        for fert_date in fertilize_dates:
            if fert_date < harvest_date:
                cursor.execute('''
                    INSERT INTO care_tasks (planted_item_id, task_type, due_date)
                    VALUES (?, ?, ?)
                ''', (planted_item_id, "fertilizing", fert_date))
        
        cursor.execute('''
            INSERT INTO care_tasks (planted_item_id, task_type, due_date)
            VALUES (?, ?, ?)
        ''', (planted_item_id, "harvesting", harvest_date))
    
    def _row_to_plot(self, row) -> GardenPlot:
        return GardenPlot(
            id=row[0],
            name=row[1],
            width=row[2],
            height=row[3],
            location=row[4],
            created_date=datetime.fromisoformat(row[5])
        )
    
    def _row_to_planted_item(self, row) -> PlantedItem:
        return PlantedItem(
            id=row[0],
            plant_id=row[1],
            plot_id=row[2],
            x_position=row[3],
            y_position=row[4],
            planted_date=datetime.fromisoformat(row[5]),
            expected_harvest=datetime.fromisoformat(row[6]),
            notes=row[7]
        )
    
    def _row_to_care_task(self, row) -> CareTask:
        return CareTask(
            id=row[0],
            planted_item_id=row[1],
            task_type=row[2],
            due_date=datetime.fromisoformat(row[3]),
            completed=bool(row[4]),
            notes=row[5] or ""
        )