"""
Unit tests for plant suggestion functionality.

Tests the is_plant_suggested utility function that determines whether
a plant should be suggested to users based on season and climate zone.
"""

import pytest
from garden_manager.utils.plant_utils import is_plant_suggested


class TestPlantSuggestions:
    """Test plant suggestion logic."""

    def test_plant_suggested_matching_season_and_zone(self):
        """Test that a plant is suggested when season and zone match."""
        result = is_plant_suggested(
            plant_season="spring",
            plant_climate_zones=[5, 6, 7],
            current_season="spring",
            user_climate_zone=6
        )
        assert result is True

    def test_plant_not_suggested_wrong_season(self):
        """Test that a plant is not suggested when season doesn't match."""
        result = is_plant_suggested(
            plant_season="summer",
            plant_climate_zones=[5, 6, 7],
            current_season="spring",
            user_climate_zone=6
        )
        assert result is False

    def test_plant_not_suggested_wrong_zone(self):
        """Test that a plant is not suggested when zone doesn't match."""
        result = is_plant_suggested(
            plant_season="spring",
            plant_climate_zones=[3, 4, 5],
            current_season="spring",
            user_climate_zone=8
        )
        assert result is False

    def test_plant_not_suggested_wrong_season_and_zone(self):
        """Test that a plant is not suggested when both season and zone don't match."""
        result = is_plant_suggested(
            plant_season="summer",
            plant_climate_zones=[3, 4, 5],
            current_season="spring",
            user_climate_zone=8
        )
        assert result is False

    def test_plant_suggested_empty_zones(self):
        """Test that plant with no zones specified is suggested if season matches."""
        result = is_plant_suggested(
            plant_season="spring",
            plant_climate_zones=[],
            current_season="spring",
            user_climate_zone=6
        )
        assert result is True

    def test_plant_not_suggested_empty_zones_wrong_season(self):
        """Test that plant with no zones is not suggested if season doesn't match."""
        result = is_plant_suggested(
            plant_season="summer",
            plant_climate_zones=[],
            current_season="spring",
            user_climate_zone=6
        )
        assert result is False

    def test_plant_suggested_case_insensitive_season(self):
        """Test that season matching is case-insensitive."""
        result = is_plant_suggested(
            plant_season="Spring",
            plant_climate_zones=[5, 6, 7],
            current_season="SPRING",
            user_climate_zone=6
        )
        assert result is True

    def test_plant_suggested_boundary_zone_low(self):
        """Test that plant is suggested when user is at lower boundary of zone range."""
        result = is_plant_suggested(
            plant_season="spring",
            plant_climate_zones=[5, 6, 7],
            current_season="spring",
            user_climate_zone=5
        )
        assert result is True

    def test_plant_suggested_boundary_zone_high(self):
        """Test that plant is suggested when user is at upper boundary of zone range."""
        result = is_plant_suggested(
            plant_season="spring",
            plant_climate_zones=[5, 6, 7],
            current_season="spring",
            user_climate_zone=7
        )
        assert result is True

    def test_plant_suggested_all_seasons(self):
        """Test suggestions for different seasons with same zone."""
        for season in ["spring", "summer", "fall", "winter"]:
            result = is_plant_suggested(
                plant_season=season,
                plant_climate_zones=[6, 7, 8],
                current_season=season,
                user_climate_zone=7
            )
            assert result is True, f"Failed for season: {season}"

    def test_plant_not_suggested_multiple_wrong_seasons(self):
        """Test that plant is not suggested for wrong seasons."""
        for wrong_season in ["summer", "fall", "winter"]:
            result = is_plant_suggested(
                plant_season="spring",
                plant_climate_zones=[6, 7, 8],
                current_season=wrong_season,
                user_climate_zone=7
            )
            assert result is False, f"Should not be suggested for season: {wrong_season}"
