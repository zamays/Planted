"""
Unit tests for database index creation and performance verification.

Tests verify that all strategic indexes are created properly during
database initialization and that they improve query performance.
"""

import os
import sqlite3
import tempfile
from datetime import datetime

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


class TestDatabaseIndexes:
    """Tests for database index creation."""

    def test_all_indexes_created(self, temp_db):
        """Test that all required indexes are created during database initialization."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()

            # Get all indexes
            cursor.execute("""
                SELECT name, tbl_name
                FROM sqlite_master
                WHERE type='index' AND sql IS NOT NULL
                ORDER BY name
            """)

            indexes = cursor.fetchall()
            index_dict = dict(indexes)

            # Verify all required indexes exist
            expected_indexes = {
                'idx_plants_season': 'plants',
                'idx_plants_user_id': 'plants',
                'idx_garden_plots_user_id': 'garden_plots',
                'idx_planted_items_plot_id': 'planted_items',
                'idx_care_tasks_planted_item_id': 'care_tasks',
                'idx_care_tasks_due_date': 'care_tasks',
                'idx_care_tasks_due_date_completed': 'care_tasks',
            }

            for index_name, expected_table in expected_indexes.items():
                assert index_name in index_dict, f"Index {index_name} not found"
                assert index_dict[index_name] == expected_table, \
                    f"Index {index_name} on wrong table: {index_dict[index_name]} != {expected_table}"

    def test_plants_season_index(self, temp_db):
        """Test that plants.season index exists."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND name='idx_plants_season'
            """)
            result = cursor.fetchone()
            assert result is not None, "idx_plants_season not found"
            assert 'season' in result[0].lower()

    def test_plants_user_id_index(self, temp_db):
        """Test that plants.user_id index exists."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND name='idx_plants_user_id'
            """)
            result = cursor.fetchone()
            assert result is not None, "idx_plants_user_id not found"
            assert 'user_id' in result[0].lower()

    def test_garden_plots_user_id_index(self, temp_db):
        """Test that garden_plots.user_id index exists."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND name='idx_garden_plots_user_id'
            """)
            result = cursor.fetchone()
            assert result is not None, "idx_garden_plots_user_id not found"
            assert 'user_id' in result[0].lower()

    def test_planted_items_plot_id_index(self, temp_db):
        """Test that planted_items.plot_id index exists."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND name='idx_planted_items_plot_id'
            """)
            result = cursor.fetchone()
            assert result is not None, "idx_planted_items_plot_id not found"
            assert 'plot_id' in result[0].lower()

    def test_care_tasks_planted_item_id_index(self, temp_db):
        """Test that care_tasks.planted_item_id index exists."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND name='idx_care_tasks_planted_item_id'
            """)
            result = cursor.fetchone()
            assert result is not None, "idx_care_tasks_planted_item_id not found"
            assert 'planted_item_id' in result[0].lower()

    def test_care_tasks_due_date_index(self, temp_db):
        """Test that care_tasks.due_date index exists."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND name='idx_care_tasks_due_date'
            """)
            result = cursor.fetchone()
            assert result is not None, "idx_care_tasks_due_date not found"
            assert 'due_date' in result[0].lower()

    def test_care_tasks_compound_index(self, temp_db):
        """Test that care_tasks compound index (due_date, completed) exists."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND name='idx_care_tasks_due_date_completed'
            """)
            result = cursor.fetchone()
            assert result is not None, "idx_care_tasks_due_date_completed not found"
            sql = result[0].lower()
            assert 'due_date' in sql
            assert 'completed' in sql


class TestIndexedQueryPerformance:
    """Tests to verify that indexes improve query performance."""

    def test_season_filtering_uses_index(self, temp_db):
        """Test that season filtering queries can use the index."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()

            # Check query plan
            cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM plants WHERE season = 'spring'")
            plan = cursor.fetchall()
            plan_str = str(plan).lower()

            # Should use index scan, not table scan
            # SQLite EXPLAIN QUERY PLAN shows 'using index' or 'search using index' for indexed queries
            # Note: This is a basic check - the exact output format varies by SQLite version
            assert 'idx_plants_season' in plan_str or 'index' in plan_str

    def test_plot_lookup_uses_index(self, temp_db):
        """Test that planted_items lookup by plot_id uses the index."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()

            # Check query plan
            cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM planted_items WHERE plot_id = 1")
            plan = cursor.fetchall()
            plan_str = str(plan).lower()

            # Should mention the index
            assert 'idx_planted_items_plot_id' in plan_str or 'index' in plan_str

    def test_care_tasks_date_query_uses_index(self, temp_db):
        """Test that care tasks due date queries use the compound index."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()

            # Check query plan for the common query pattern
            cursor.execute("""
                EXPLAIN QUERY PLAN
                SELECT * FROM care_tasks
                WHERE due_date <= datetime('now', '+7 days') AND completed = 0
            """)
            plan = cursor.fetchall()
            plan_str = str(plan).lower()

            # Should use one of the care_tasks indexes
            assert 'idx_care_tasks' in plan_str or 'index' in plan_str

    def test_query_executes_successfully_with_indexes(self, garden_db, temp_db):
        """Test that indexed queries execute correctly with real data."""
        # Create some test data
        plot_id = garden_db.create_garden_plot(
            name="Test Plot",
            width=10,
            height=10,
            location="Test",
            user_id=1
        )

        # Get a plant ID
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM plants LIMIT 1")
            plant_id = cursor.fetchone()[0]

        # Add planted item
        planting_info = PlantingInfo(
            plant_id=plant_id,
            plot_id=plot_id,
            x_pos=1,
            y_pos=1,
            notes="Test",
            planted_date=datetime.now(),
            days_to_maturity=60
        )
        garden_db.add_planted_item(planting_info)

        # These queries should all use indexes and execute successfully
        plots = garden_db.get_garden_plots(user_id=1)
        assert len(plots) > 0

        planted_items = garden_db.get_planted_items(plot_id)
        assert len(planted_items) > 0

        care_tasks = garden_db.get_care_tasks(due_within_days=70)
        assert len(care_tasks) > 0


class TestIndexIdempotency:
    """Test that index creation is idempotent and safe."""

    def test_reinitialize_database_safe(self, temp_db):
        """Test that reinitializing the database doesn't cause errors."""
        # Database is already initialized by the fixture
        # Try to initialize again
        _ = PlantDatabase(temp_db)

        # Should still have all indexes
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='index' AND sql IS NOT NULL
            """)
            count = cursor.fetchone()[0]

            # Should have exactly 7 indexes (no duplicates)
            assert count == 7

    def test_create_if_not_exists_behavior(self, temp_db):
        """Test that CREATE INDEX IF NOT EXISTS works correctly."""
        with sqlite3.connect(temp_db) as conn:
            # Try to create an index that already exists
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_plants_season
                ON plants(season)
            """)

            # Should not raise an error and should still have one index
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='index' AND name='idx_plants_season'
            """)
            count = cursor.fetchone()[0]

            assert count == 1, "Duplicate index created"
