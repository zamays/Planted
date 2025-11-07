"""
Integration test for plot viewing with N+1 optimization.

Tests the full web route to ensure the optimized batch loading works correctly.
"""

import os
import tempfile
import unittest
from datetime import datetime

from garden_manager.database.plant_data import PlantDatabase
from garden_manager.database.garden_db import GardenDatabase
from garden_manager.database.models import PlantingInfo


class TestPlotViewingIntegration(unittest.TestCase):
    """Integration test for plot viewing optimization."""

    def setUp(self):
        """Set up test database with sample data."""
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.plant_db = PlantDatabase(self.db_path)
        self.garden_db = GardenDatabase(self.db_path)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_view_plot_data_integrity_with_optimization(self):
        """Test that optimized plot viewing returns identical data."""
        # Create a test plot
        plot_id = self.garden_db.create_garden_plot(
            "Test Plot", 10, 10, "Test Location"
        )

        # Get some plants
        spring_plants = self.plant_db.get_plants_by_season("spring")
        plants_to_add = spring_plants[:20]  # Add 20 plants

        # Add planted items
        for i, plant in enumerate(plants_to_add):
            planting_info = PlantingInfo(
                plant_id=plant.id,
                plot_id=plot_id,
                x_pos=i % 10,
                y_pos=i // 10,
                notes=f"Test plant {i}",
                planted_date=datetime.now(),
                days_to_maturity=plant.growing.days_to_maturity,
            )
            self.garden_db.add_planted_item(planting_info)

        # Test old method (N+1 queries)
        planted_items_old = self.garden_db.get_planted_items(plot_id)
        old_results = []
        for item in planted_items_old:
            plant = self.plant_db.get_plant_by_id(item.plant_id)
            if plant:
                old_results.append({"item": item, "plant": plant})

        # Test new method (batch loading)
        planted_items_data = self.garden_db.get_planted_items_with_plant_ids(plot_id)
        plant_ids = [plant_id for _, plant_id in planted_items_data]
        plants_dict = self.plant_db.get_plants_by_ids(plant_ids)
        new_results = []
        for item, plant_id in planted_items_data:
            plant = plants_dict.get(plant_id)
            if plant:
                new_results.append({"item": item, "plant": plant})

        # Verify data integrity
        self.assertEqual(len(old_results), len(new_results))
        self.assertEqual(len(new_results), 20)

        # Verify each item matches
        for old, new in zip(old_results, new_results):
            # Verify item properties
            self.assertEqual(old["item"].id, new["item"].id)
            self.assertEqual(old["item"].plant_id, new["item"].plant_id)
            self.assertEqual(old["item"].plot_id, new["item"].plot_id)
            self.assertEqual(old["item"].position.x, new["item"].position.x)
            self.assertEqual(old["item"].position.y, new["item"].position.y)

            # Verify plant properties
            self.assertEqual(old["plant"].id, new["plant"].id)
            self.assertEqual(old["plant"].name, new["plant"].name)
            self.assertEqual(old["plant"].scientific_name, new["plant"].scientific_name)
            self.assertEqual(old["plant"].plant_type, new["plant"].plant_type)

    def test_view_plot_empty_plot(self):
        """Test that optimized method handles empty plots correctly."""
        # Create an empty plot
        plot_id = self.garden_db.create_garden_plot(
            "Empty Plot", 5, 5, "Test Location"
        )

        # Test new method with empty plot
        planted_items_data = self.garden_db.get_planted_items_with_plant_ids(plot_id)
        self.assertEqual(len(planted_items_data), 0)

        plant_ids = [plant_id for _, plant_id in planted_items_data]
        plants_dict = self.plant_db.get_plants_by_ids(plant_ids)
        self.assertEqual(len(plants_dict), 0)

    def test_view_plot_single_plant(self):
        """Test that optimized method works with a single plant."""
        # Create a plot
        plot_id = self.garden_db.create_garden_plot(
            "Single Plant Plot", 3, 3, "Test Location"
        )

        # Add one plant
        plants = self.plant_db.get_plants_by_season("spring")
        plant = plants[0]

        planting_info = PlantingInfo(
            plant_id=plant.id,
            plot_id=plot_id,
            x_pos=1,
            y_pos=1,
            notes="Single test plant",
            planted_date=datetime.now(),
            days_to_maturity=plant.growing.days_to_maturity,
        )
        self.garden_db.add_planted_item(planting_info)

        # Test new method
        planted_items_data = self.garden_db.get_planted_items_with_plant_ids(plot_id)
        self.assertEqual(len(planted_items_data), 1)

        plant_ids = [plant_id for _, plant_id in planted_items_data]
        plants_dict = self.plant_db.get_plants_by_ids(plant_ids)
        self.assertEqual(len(plants_dict), 1)
        self.assertIn(plant.id, plants_dict)
        self.assertEqual(plants_dict[plant.id].name, plant.name)


if __name__ == "__main__":
    unittest.main()
