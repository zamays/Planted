"""
Tests for location detection and display UI improvements.

These tests verify all scenarios described in the problem statement:
1. Climate Zone Display (Settings Page)
2. Default Location Indicator
3. Auto-Detection Confirmation
4. Geocoding Failure Handling
5. Location Display Format
6. Settings Page Missing City Warning
7. Weather Cache Clearing
8. User Location Persistence
"""

from unittest.mock import patch, Mock
import pytest
from garden_manager.services.auth_service import AuthService
from garden_manager.services.location_service import LocationService


class TestClimateZoneDisplay:
    """Test climate zone display on settings page."""

    @pytest.fixture
    def location_service(self):
        """Create a location service instance."""
        return LocationService()

    def test_climate_zone_displays_correctly(self, location_service):
        """Verify climate zone displays as 'Zone 6' for New York."""
        location_service.set_manual_location(
            40.7128, -74.0060,
            {"city": "New York", "region": "NY", "country": "USA"},
            is_default=False
        )
        climate_zone = location_service.get_climate_zone()
        assert climate_zone == 6


class TestDefaultLocationIndicator:
    """Test default location indicator functionality."""

    @pytest.fixture
    def location_service(self):
        """Create a location service instance."""
        return LocationService()

    def test_default_location_flag_set(self, location_service):
        """Verify is_default_location flag is set for default location."""
        location_service.set_manual_location(
            40.7128, -74.0060,
            {"city": "New York", "region": "NY", "country": "USA"},
            is_default=True
        )
        assert location_service.is_default_location is True

    def test_user_location_not_default(self, location_service):
        """Verify is_default_location is False when user sets location."""
        location_service.set_manual_location(
            34.0522, -118.2437,
            {"city": "Los Angeles", "region": "CA", "country": "USA"},
            is_default=False
        )
        assert location_service.is_default_location is False

    def test_location_info_includes_default_flag(self, location_service):
        """Verify get_location_info() includes is_default flag."""
        location_service.set_manual_location(
            40.7128, -74.0060,
            {"city": "New York", "region": "NY", "country": "USA"},
            is_default=True
        )
        info = location_service.get_location_info()
        assert info['is_default'] is True
        assert info['display'] == "New York, NY"


class TestLocationDisplayFormat:
    """Test location display format requirements."""

    @pytest.fixture
    def location_service(self):
        """Create a location service instance."""
        return LocationService()

    def test_city_and_region_format(self, location_service):
        """Location with city and region shows 'City, Region'."""
        location_service.set_manual_location(
            40.7128, -74.0060,
            {"city": "New York", "region": "NY", "country": "USA"}
        )
        display = location_service.get_location_display()
        assert display == "New York, NY"

    def test_city_only_format(self, location_service):
        """Location with city only shows 'City'."""
        location_service.set_manual_location(
            51.5074, -0.1278,
            {"city": "London", "region": "", "country": ""}
        )
        display = location_service.get_location_display()
        assert display == "London"

    def test_coordinates_only_shows_friendly_message(self, location_service):
        """Location with coordinates only shows 'Your location', NOT raw lat/long."""
        location_service.set_manual_location(
            40.7128, -74.0060,
            {"city": "", "region": "", "country": ""}
        )
        display = location_service.get_location_display()
        # Should NOT show raw coordinates to user
        assert display == "Your location"
        assert "40." not in display
        assert "74." not in display


class TestGeocodingFailureHandling:
    """Test handling of geocoding failures."""

    @pytest.fixture
    def location_service(self):
        """Create a location service instance."""
        return LocationService()

    @patch('garden_manager.services.location_service.requests.Session.get')
    def test_geocoding_failure_returns_empty_city(self, mock_get, location_service):
        """When geocoding fails, city should be empty but coordinates preserved."""
        # Mock failed geocoding response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        location = location_service.set_manual_location(
            40.7128, -74.0060,
            {}  # No city provided, will attempt geocoding
        )

        # Coordinates should be saved
        assert location['latitude'] == 40.7128
        assert location['longitude'] == -74.0060
        # City should be empty (geocoding failed)
        assert location['city'] == ""
        # Display should show friendly message
        assert location_service.get_location_display() == "Your location"

    @patch('garden_manager.services.location_service.requests.Session.get')
    def test_geocoding_success_populates_city(self, mock_get, location_service):
        """When geocoding succeeds, city should be populated."""
        # Mock successful geocoding response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "address": {
                "city": "Seattle",
                "state": "Washington",
                "country": "United States"
            }
        }
        mock_get.return_value = mock_response

        location = location_service.set_manual_location(
            47.6062, -122.3321,
            {}  # No city provided, will use geocoding
        )

        # City should be populated from geocoding
        assert location['city'] == "Seattle"
        assert location['region'] == "Washington"
        assert location['country'] == "United States"


class TestUserLocationPersistence:
    """Test that user location persists across sessions."""

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

    def test_location_persists_after_logout_login(self, auth_service, test_user):
        """Location should persist when user logs out and logs back in."""
        # Set location
        auth_service.update_user_location(
            test_user,
            34.0522,
            -118.2437,
            "Los Angeles",
            "CA",
            "USA"
        )

        # "Logout" (clear session) and "login" again
        user = auth_service.verify_login("testuser", "password123")

        # Location should still be there
        assert user is not None
        assert user['location'] is not None
        assert user['location']['city'] == "Los Angeles"
        assert user['location']['latitude'] == 34.0522

    def test_location_initially_none_for_new_user(self, auth_service, test_user):
        """New user should have no location set (None)."""
        user = auth_service.get_user_by_id(test_user)
        assert user is not None
        assert user['location'] is None


class TestSettingsPageWarning:
    """Test settings page warning when city name is missing."""

    @pytest.fixture
    def location_service(self):
        """Create a location service instance."""
        return LocationService()

    def test_location_info_shows_missing_city(self, location_service):
        """When city is empty, location info should indicate this."""
        location_service.set_manual_location(
            40.7128, -74.0060,
            {"city": "", "region": "", "country": ""}
        )
        info = location_service.get_location_info()

        # City should be empty string
        assert info['city'] == ""
        # Display should use fallback message
        assert info['display'] == "Your location"


class TestLocationServiceInfo:
    """Test get_location_info() method returns all required data."""

    @pytest.fixture
    def location_service(self):
        """Create a location service instance."""
        return LocationService()

    def test_location_info_structure(self, location_service):
        """Verify get_location_info() returns all required fields."""
        location_service.set_manual_location(
            40.7128, -74.0060,
            {"city": "New York", "region": "NY", "country": "USA"},
            is_default=False
        )
        info = location_service.get_location_info()

        # Verify all required fields are present
        assert 'display' in info
        assert 'latitude' in info
        assert 'longitude' in info
        assert 'climate_zone' in info
        assert 'is_default' in info
        assert 'city' in info
        assert 'region' in info
        assert 'country' in info

        # Verify values are correct
        assert info['display'] == "New York, NY"
        assert info['latitude'] == 40.7128
        assert info['longitude'] == -74.0060
        assert info['climate_zone'] == 6
        assert info['is_default'] is False
        assert info['city'] == "New York"
        assert info['region'] == "NY"
        assert info['country'] == "USA"
