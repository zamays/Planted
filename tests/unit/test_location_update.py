"""
Tests for location update functionality.
"""

import pytest
from garden_manager.services.auth_service import AuthService
from garden_manager.services.location_service import LocationService


class TestLocationUpdate:
    """Test user location update functionality."""

    @pytest.fixture
    def auth_service(self, tmp_path):
        """Create a test auth service with temporary database."""
        db_path = tmp_path / "test_auth.db"
        return AuthService(str(db_path))

    @pytest.fixture
    def test_user(self, auth_service):
        """Create a test user."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        return user_id

    def test_update_user_location(self, auth_service, test_user):
        """Test updating user location."""
        # Update location
        auth_service.update_user_location(
            test_user,
            40.7128,
            -74.0060,
            "New York",
            "NY",
            "USA"
        )

        # Verify location was saved
        user = auth_service.get_user_by_id(test_user)
        assert user is not None
        assert user['location'] is not None
        assert user['location']['latitude'] == 40.7128
        assert user['location']['longitude'] == -74.0060
        assert user['location']['city'] == "New York"
        assert user['location']['region'] == "NY"
        assert user['location']['country'] == "USA"

    def test_update_user_location_partial_info(self, auth_service, test_user):
        """Test updating location with only coordinates."""
        # Update location with just coordinates
        auth_service.update_user_location(
            test_user,
            51.5074,
            -0.1278
        )

        # Verify location was saved
        user = auth_service.get_user_by_id(test_user)
        assert user is not None
        assert user['location'] is not None
        assert user['location']['latitude'] == 51.5074
        assert user['location']['longitude'] == -0.1278
        assert user['location']['city'] == ""
        assert user['location']['region'] == ""
        assert user['location']['country'] == ""

    def test_login_returns_location(self, auth_service, test_user):
        """Test that login returns user's location."""
        # Set location
        auth_service.update_user_location(
            test_user,
            34.0522,
            -118.2437,
            "Los Angeles",
            "CA",
            "USA"
        )

        # Login
        user = auth_service.verify_login("testuser", "password123")

        # Verify location is returned
        assert user is not None
        assert user['location'] is not None
        assert user['location']['latitude'] == 34.0522
        assert user['location']['longitude'] == -118.2437
        assert user['location']['city'] == "Los Angeles"


class TestLocationService:
    """Test location service functionality."""

    def test_set_manual_location(self):
        """Test setting manual location."""
        service = LocationService()

        # Set location
        location = service.set_manual_location(
            40.7128,
            -74.0060,
            {"city": "New York", "region": "NY", "country": "USA"}
        )

        assert location is not None
        assert location['latitude'] == 40.7128
        assert location['longitude'] == -74.0060
        assert location['city'] == "New York"
        assert location['region'] == "NY"
        assert location['country'] == "USA"

    def test_climate_zone_calculation(self):
        """Test climate zone calculation based on latitude."""
        service = LocationService()

        # Test various latitudes
        # New York (40.7N) should be zone 6
        service.set_manual_location(40.7128, -74.0060)
        assert service.get_climate_zone() == 6

        # Miami (25.8N) should be zone 9
        service.set_manual_location(25.7617, -80.1918)
        assert service.get_climate_zone() == 9

        # Minneapolis (44.9N) should be zone 6 (just below 45° threshold)
        service.set_manual_location(44.9778, -93.2650)
        assert service.get_climate_zone() == 6

        # Northern latitude (46N) should be zone 5
        service.set_manual_location(46.0, -93.0)
        assert service.get_climate_zone() == 5

    def test_location_display(self):
        """Test location display string generation."""
        service = LocationService()

        # With full info
        service.set_manual_location(
            40.7128,
            -74.0060,
            {"city": "New York", "region": "NY", "country": "USA"}
        )
        display = service.get_location_display()
        assert "New York" in display
        assert "NY" in display

        # With just coordinates
        service.set_manual_location(40.7128, -74.0060, {})
        display = service.get_location_display()
        assert "40.71" in display
        assert "-74.01" in display
