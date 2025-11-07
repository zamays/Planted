"""
Tests for N+1 query optimization in plot viewing.

Validates that the batch loading methods work correctly and improve performance.
"""

import os
import tempfile
import time
import unittest
from datetime import datetime

from garden_manager.database.plant_data import PlantDatabase
from garden_manager.database.garden_db import GardenDatabase
from garden_manager.database.models import (
    PlantSpec,
    PlantingInfo,
    PlantGrowingInfo,
    PlantCareRequirements,
    PlantCompatibility,
)


class TestNPlus1Optimization(unittest.TestCase):
    """Test cases for N+1 query optimization."""

    def setUp(self):
        """Set up test database with sample data."""
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.plant_db = PlantDatabase(self.db_path)
        self.garden_db = GardenDatabase(self.db_path)

        # Create a test plot
        self.plot_id = self.garden_db.create_garden_plot(
            "Test Plot", 10, 10, "Test Location"
        )

        # Add some test plants
        self.plant_ids = []
        for i in range(5):
            growing = PlantGrowingInfo(
                season="spring",
                planting_method="seed",
                days_to_germination=7,
                days_to_maturity=60,
                spacing_inches=12,
            )
            care = PlantCareRequirements(
                sun_requirements="Full sun",
                water_needs="medium",
                care_notes="Test notes",
            )
            compatibility = PlantCompatibility(
                companion_plants=[],
                avoid_plants=[],
                climate_zones=[4, 5, 6, 7, 8, 9],
            )
            plant_spec = PlantSpec(
                name=f"Test Plant {i}",
                scientific_name=f"Plantus testus {i}",
                plant_type="vegetable",
                growing=growing,
                care=care,
                compatibility=compatibility,
            )
            plant_id = self.plant_db.add_custom_plant(plant_spec)
            self.plant_ids.append(plant_id)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_get_plants_by_ids_empty_list(self):
        """Test that empty list returns empty dict."""
        result = self.plant_db.get_plants_by_ids([])
        self.assertEqual(result, {})

    def test_get_plants_by_ids_single_plant(self):
        """Test batch loading with a single plant."""
        result = self.plant_db.get_plants_by_ids([self.plant_ids[0]])
        self.assertEqual(len(result), 1)
        self.assertIn(self.plant_ids[0], result)
        self.assertEqual(result[self.plant_ids[0]].name, "Test Plant 0")

    def test_get_plants_by_ids_multiple_plants(self):
        """Test batch loading with multiple plants."""
        result = self.plant_db.get_plants_by_ids(self.plant_ids)
        self.assertEqual(len(result), len(self.plant_ids))
        for plant_id in self.plant_ids:
            self.assertIn(plant_id, result)

    def test_get_plants_by_ids_nonexistent_ids(self):
        """Test batch loading with nonexistent IDs."""
        result = self.plant_db.get_plants_by_ids([9999, 10000])
        self.assertEqual(len(result), 0)

    def test_get_plants_by_ids_mixed_valid_invalid(self):
        """Test batch loading with mix of valid and invalid IDs."""
        mixed_ids = [self.plant_ids[0], 9999, self.plant_ids[1]]
        result = self.plant_db.get_plants_by_ids(mixed_ids)
        self.assertEqual(len(result), 2)
        self.assertIn(self.plant_ids[0], result)
        self.assertIn(self.plant_ids[1], result)
        self.assertNotIn(9999, result)

    def test_get_planted_items_with_plant_ids_empty_plot(self):
        """Test getting planted items from empty plot."""
        result = self.garden_db.get_planted_items_with_plant_ids(self.plot_id)
        self.assertEqual(len(result), 0)

    def test_get_planted_items_with_plant_ids_single_item(self):
        """Test getting planted items with one plant."""
        # Plant one item
        planting_info = PlantingInfo(
            plant_id=self.plant_ids[0],
            plot_id=self.plot_id,
            x_pos=0,
            y_pos=0,
            notes="Test",
            planted_date=datetime.now(),
            days_to_maturity=60,
        )
        self.garden_db.add_planted_item(planting_info)

        result = self.garden_db.get_planted_items_with_plant_ids(self.plot_id)
        self.assertEqual(len(result), 1)
        item, plant_id = result[0]
        self.assertEqual(plant_id, self.plant_ids[0])
        self.assertEqual(item.plant_id, self.plant_ids[0])

    def test_get_planted_items_with_plant_ids_multiple_items(self):
        """Test getting planted items with multiple plants."""
        # Plant multiple items
        for i, plant_id in enumerate(self.plant_ids[:3]):
            planting_info = PlantingInfo(
                plant_id=plant_id,
                plot_id=self.plot_id,
                x_pos=i,
                y_pos=0,
                notes=f"Test {i}",
                planted_date=datetime.now(),
                days_to_maturity=60,
            )
            self.garden_db.add_planted_item(planting_info)

        result = self.garden_db.get_planted_items_with_plant_ids(self.plot_id)
        self.assertEqual(len(result), 3)

        # Verify all plant IDs are correct
        returned_plant_ids = [plant_id for _, plant_id in result]
        for plant_id in self.plant_ids[:3]:
            self.assertIn(plant_id, returned_plant_ids)

    def test_batch_loading_data_integrity(self):
        """Test that batch loading returns correct data."""
        # Plant items
        for i, plant_id in enumerate(self.plant_ids):
            planting_info = PlantingInfo(
                plant_id=plant_id,
                plot_id=self.plot_id,
                x_pos=i % 10,
                y_pos=i // 10,
                notes=f"Test {i}",
                planted_date=datetime.now(),
                days_to_maturity=60,
            )
            self.garden_db.add_planted_item(planting_info)

        # Use batch loading
        planted_items_data = self.garden_db.get_planted_items_with_plant_ids(self.plot_id)
        plant_ids = [plant_id for _, plant_id in planted_items_data]
        plants_dict = self.plant_db.get_plants_by_ids(plant_ids)

        # Verify data integrity
        for item, plant_id in planted_items_data:
            plant = plants_dict.get(plant_id)
            self.assertIsNotNone(plant)
            self.assertEqual(plant.id, plant_id)
            self.assertEqual(item.plant_id, plant_id)

    def test_performance_batch_vs_individual(self):
        """Test that batch loading is faster than individual queries."""
        # Create more plants for meaningful performance test
        num_plants = 50
        plant_ids = []
        for i in range(num_plants):
            growing = PlantGrowingInfo(
                season="spring",
                planting_method="seed",
                days_to_germination=7,
                days_to_maturity=60,
                spacing_inches=12,
            )
            care = PlantCareRequirements(
                sun_requirements="Full sun",
                water_needs="medium",
                care_notes="Test notes",
            )
            compatibility = PlantCompatibility(
                companion_plants=[],
                avoid_plants=[],
                climate_zones=[4, 5, 6, 7, 8, 9],
            )
            plant_spec = PlantSpec(
                name=f"Perf Test Plant {i}",
                scientific_name=f"Plantus perfus {i}",
                plant_type="vegetable",
                growing=growing,
                care=care,
                compatibility=compatibility,
            )
            plant_id = self.plant_db.add_custom_plant(plant_spec)
            plant_ids.append(plant_id)

            # Plant the item
            planting_info = PlantingInfo(
                plant_id=plant_id,
                plot_id=self.plot_id,
                x_pos=i % 10,
                y_pos=i // 10,
                notes=f"Test {i}",
                planted_date=datetime.now(),
                days_to_maturity=60,
            )
            self.garden_db.add_planted_item(planting_info)

        # Time individual queries (old method)
        start_time = time.time()
        planted_items = self.garden_db.get_planted_items(self.plot_id)
        for item in planted_items:
            _ = self.plant_db.get_plant_by_id(item.plant_id)
        individual_time = time.time() - start_time

        # Time batch query (new method)
        start_time = time.time()
        planted_items_data = self.garden_db.get_planted_items_with_plant_ids(self.plot_id)
        plant_ids_to_fetch = [plant_id for _, plant_id in planted_items_data]
        _ = self.plant_db.get_plants_by_ids(plant_ids_to_fetch)
        batch_time = time.time() - start_time

        # Batch loading should be significantly faster
        # Allow for some variance, but should be at least 2x faster
        print(f"\nPerformance comparison ({num_plants} plants):")
        print(f"  Individual queries: {individual_time:.4f}s")
        print(f"  Batch query: {batch_time:.4f}s")
        print(f"  Speedup: {individual_time / batch_time:.2f}x")

        # Batch should be faster (but we don't enforce strict ratio due to test variability)
        self.assertLess(batch_time, individual_time * 0.9)  # At least 10% improvement


if __name__ == "__main__":
    unittest.main()
