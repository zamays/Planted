"""
Test plant editing and deletion functionality
"""

import pytest
import json
from garden_manager.database.plant_data import PlantDatabase
from garden_manager.database.models import (
    PlantSpec,
    PlantGrowingInfo,
    PlantCareRequirements,
    PlantCompatibility,
)


@pytest.fixture
def plant_db(tmp_path):
    """Create a temporary plant database for testing."""
    db_file = tmp_path / "test_plants.db"
    return PlantDatabase(str(db_file))


@pytest.fixture
def custom_plant_id(plant_db):
    """Create a custom plant for testing."""
    plant_spec = PlantSpec(
        name="Test Tomato",
        scientific_name="Solanum lycopersicum test",
        plant_type="vegetable",
        growing=PlantGrowingInfo(
            season="summer",
            planting_method="transplant",
            days_to_germination=7,
            days_to_maturity=80,
            spacing_inches=24,
        ),
        care=PlantCareRequirements(
            sun_requirements="full_sun",
            water_needs="high",
            care_notes="Test care notes",
        ),
        compatibility=PlantCompatibility(
            companion_plants=["basil", "carrots"],
            avoid_plants=["fennel"],
            climate_zones=[5, 6, 7, 8, 9],
        ),
    )
    return plant_db.add_custom_plant(plant_spec)


class TestPlantUpdate:
    """Tests for updating plant information."""

    def test_update_plant_basic_info(self, plant_db, custom_plant_id):
        """Test updating basic plant information."""
        updated_spec = PlantSpec(
            name="Updated Tomato",
            scientific_name="Solanum lycopersicum updated",
            plant_type="vegetable",
            growing=PlantGrowingInfo(
                season="spring",
                planting_method="seed",
                days_to_germination=10,
                days_to_maturity=90,
                spacing_inches=30,
            ),
            care=PlantCareRequirements(
                sun_requirements="partial_shade",
                water_needs="medium",
                care_notes="Updated care notes",
            ),
            compatibility=PlantCompatibility(
                companion_plants=["peppers"],
                avoid_plants=["brassicas"],
                climate_zones=[4, 5, 6],
            ),
        )

        success = plant_db.update_plant(custom_plant_id, updated_spec)
        assert success is True

        # Verify the update
        plant = plant_db.get_plant_by_id(custom_plant_id)
        assert plant.name == "Updated Tomato"
        assert plant.scientific_name == "Solanum lycopersicum updated"
        assert plant.season == "spring"
        assert plant.planting_method == "seed"
        assert plant.days_to_germination == 10
        assert plant.days_to_maturity == 90
        assert plant.spacing_inches == 30
        assert plant.sun_requirements == "partial_shade"
        assert plant.water_needs == "medium"
        assert plant.care_notes == "Updated care notes"
        assert plant.companion_plants == ["peppers"]
        assert plant.avoid_plants == ["brassicas"]
        assert plant.climate_zones == [4, 5, 6]

    def test_update_plant_empty_lists(self, plant_db, custom_plant_id):
        """Test updating a plant with empty companion and avoid lists."""
        updated_spec = PlantSpec(
            name="Test Tomato",
            scientific_name="Solanum lycopersicum test",
            plant_type="vegetable",
            growing=PlantGrowingInfo(
                season="summer",
                planting_method="transplant",
                days_to_germination=7,
                days_to_maturity=80,
                spacing_inches=24,
            ),
            care=PlantCareRequirements(
                sun_requirements="full_sun",
                water_needs="high",
                care_notes="Test care notes",
            ),
            compatibility=PlantCompatibility(
                companion_plants=[],
                avoid_plants=[],
                climate_zones=[],
            ),
        )

        success = plant_db.update_plant(custom_plant_id, updated_spec)
        assert success is True

        plant = plant_db.get_plant_by_id(custom_plant_id)
        assert plant.companion_plants == []
        assert plant.avoid_plants == []
        assert plant.climate_zones == []

    def test_update_plant_missing_name(self, plant_db, custom_plant_id):
        """Test that updating a plant with no name raises ValueError."""
        updated_spec = PlantSpec(
            name="",  # Empty name
            scientific_name="Test",
            plant_type="vegetable",
            growing=PlantGrowingInfo(
                season="summer",
                planting_method="transplant",
                days_to_germination=7,
                days_to_maturity=80,
                spacing_inches=24,
            ),
            care=PlantCareRequirements(
                sun_requirements="full_sun",
                water_needs="high",
                care_notes="Test",
            ),
            compatibility=PlantCompatibility(
                companion_plants=[],
                avoid_plants=[],
                climate_zones=[],
            ),
        )

        with pytest.raises(ValueError, match="Plant name is required"):
            plant_db.update_plant(custom_plant_id, updated_spec)

    def test_update_nonexistent_plant(self, plant_db):
        """Test that updating a non-existent plant returns False."""
        updated_spec = PlantSpec(
            name="Test",
            scientific_name="Test",
            plant_type="vegetable",
            growing=PlantGrowingInfo(
                season="summer",
                planting_method="transplant",
                days_to_germination=7,
                days_to_maturity=80,
                spacing_inches=24,
            ),
            care=PlantCareRequirements(
                sun_requirements="full_sun",
                water_needs="high",
                care_notes="Test",
            ),
            compatibility=PlantCompatibility(
                companion_plants=[],
                avoid_plants=[],
                climate_zones=[],
            ),
        )

        success = plant_db.update_plant(99999, updated_spec)
        assert success is False


class TestPlantDeletion:
    """Tests for deleting plants."""

    def test_delete_custom_plant(self, plant_db, custom_plant_id):
        """Test deleting a custom plant."""
        success = plant_db.delete_plant(custom_plant_id)
        assert success is True

        # Verify the plant is deleted
        plant = plant_db.get_plant_by_id(custom_plant_id)
        assert plant is None

    def test_delete_default_plant(self, plant_db):
        """Test that deleting a default plant raises ValueError."""
        # Get a default plant (these are loaded in populate_plant_data)
        plants = plant_db.get_plants_by_type("vegetable")
        assert len(plants) > 0

        default_plant = plants[0]
        assert default_plant.is_custom is False

        with pytest.raises(
            ValueError, match="Cannot delete default plants. Only custom plants can be deleted."
        ):
            plant_db.delete_plant(default_plant.id)

    def test_delete_nonexistent_plant(self, plant_db):
        """Test that deleting a non-existent plant returns False."""
        success = plant_db.delete_plant(99999)
        assert success is False


class TestPlantEditWorkflow:
    """Tests for the complete edit workflow."""

    def test_add_edit_delete_workflow(self, plant_db):
        """Test the complete workflow: add, edit, then delete a custom plant."""
        # Step 1: Add a custom plant
        original_spec = PlantSpec(
            name="Workflow Test Plant",
            scientific_name="Testus workflowus",
            plant_type="herb",
            growing=PlantGrowingInfo(
                season="spring",
                planting_method="seed",
                days_to_germination=5,
                days_to_maturity=45,
                spacing_inches=12,
            ),
            care=PlantCareRequirements(
                sun_requirements="full_sun",
                water_needs="medium",
                care_notes="Original notes",
            ),
            compatibility=PlantCompatibility(
                companion_plants=["tomatoes"],
                avoid_plants=["sage"],
                climate_zones=[5, 6, 7],
            ),
        )
        plant_id = plant_db.add_custom_plant(original_spec)
        assert plant_id is not None

        # Verify it was added
        plant = plant_db.get_plant_by_id(plant_id)
        assert plant is not None
        assert plant.name == "Workflow Test Plant"
        assert plant.is_custom is True

        # Step 2: Edit the plant
        updated_spec = PlantSpec(
            name="Workflow Test Plant - Updated",
            scientific_name="Testus workflowus editedus",
            plant_type="herb",
            growing=PlantGrowingInfo(
                season="summer",
                planting_method="transplant",
                days_to_germination=7,
                days_to_maturity=60,
                spacing_inches=18,
            ),
            care=PlantCareRequirements(
                sun_requirements="partial_shade",
                water_needs="high",
                care_notes="Updated notes with more details",
            ),
            compatibility=PlantCompatibility(
                companion_plants=["peppers", "cucumbers"],
                avoid_plants=["mint"],
                climate_zones=[6, 7, 8, 9],
            ),
        )
        success = plant_db.update_plant(plant_id, updated_spec)
        assert success is True

        # Verify the update
        plant = plant_db.get_plant_by_id(plant_id)
        assert plant.name == "Workflow Test Plant - Updated"
        assert plant.scientific_name == "Testus workflowus editedus"
        assert plant.season == "summer"
        assert plant.care_notes == "Updated notes with more details"

        # Step 3: Delete the plant
        success = plant_db.delete_plant(plant_id)
        assert success is True

        # Verify it's deleted
        plant = plant_db.get_plant_by_id(plant_id)
        assert plant is None
