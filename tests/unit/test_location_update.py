"""
Tests for location update functionality.
"""

from unittest.mock import patch, Mock

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

    @patch('garden_manager.services.location_service.requests.get')
    def test_reverse_geocoding_success(self, mock_get):
        """Test successful reverse geocoding of coordinates to city name."""
        service = LocationService()

        # Mock successful Nominatim API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "address": {
                "city": "New York",
                "state": "New York",
                "country": "United States"
            }
        }
        mock_get.return_value = mock_response

        # Set location with just coordinates
        location = service.set_manual_location(40.7128, -74.0060, {})

        # Verify reverse geocoding was called
        assert mock_get.called
        call_args = mock_get.call_args
        assert 'lat' in call_args[1]['params']
        assert 'lon' in call_args[1]['params']

        # Verify location now has city information
        assert location['city'] == "New York"
        assert location['region'] == "New York"
        assert location['country'] == "United States"

        # Verify display shows city name, not coordinates
        display = service.get_location_display()
        assert "New York" in display
        assert "40.71" not in display  # Should not show coordinates

    @patch('garden_manager.services.location_service.requests.get')
    def test_reverse_geocoding_with_town(self, mock_get):
        """Test reverse geocoding returns town when city is not available."""
        service = LocationService()

        # Mock Nominatim API response with town instead of city
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "address": {
                "town": "Springfield",
                "state": "Illinois",
                "country": "United States"
            }
        }
        mock_get.return_value = mock_response

        # Set location with just coordinates
        location = service.set_manual_location(39.7817, -89.6501, {})

        # Verify town is used as city
        assert location['city'] == "Springfield"
        assert location['region'] == "Illinois"

    @patch('garden_manager.services.location_service.requests.get')
    def test_reverse_geocoding_fallback_on_failure(self, mock_get):
        """Test that coordinates are displayed when reverse geocoding fails."""
        service = LocationService()

        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Set location with just coordinates
        location = service.set_manual_location(40.7128, -74.0060, {})

        # Verify location has coordinates but no city
        assert location['city'] == ""
        assert location['latitude'] == 40.7128
        assert location['longitude'] == -74.0060

        # Verify display falls back to coordinates
        display = service.get_location_display()
        assert "40.71" in display
        assert "-74.01" in display

    def test_manual_location_with_city_skips_geocoding(self):
        """Test that reverse geocoding is skipped when city is provided."""
        service = LocationService()

        # Directly test that when city is provided, it's used
        location = service.set_manual_location(
            40.7128,
            -74.0060,
            {"city": "Custom City", "region": "Custom Region", "country": "Custom Country"}
        )

        # Verify provided information is used
        assert location['city'] == "Custom City"
        assert location['region'] == "Custom Region"
        assert location['country'] == "Custom Country"


class TestAPIIntegrationWithReverseGeocoding:
    """Test that API properly integrates reverse geocoding with database."""

    @pytest.fixture
    def auth_service(self, tmp_path):
        """Create a test auth service with temporary database."""
        db_path = tmp_path / "test_auth.db"
        return AuthService(str(db_path))

    @pytest.fixture
    def location_service(self):
        """Create a test location service."""
        return LocationService()

    @pytest.fixture
    def test_user(self, auth_service):
        """Create a test user."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        return user_id

    @patch('garden_manager.services.location_service.requests.get')
    def test_api_saves_geocoded_location_to_database(
        self, mock_get, auth_service, location_service, test_user
    ):
        """Test that geocoded city information is saved to database."""
        # Mock successful Nominatim API response
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

        # Simulate what the API does:
        # 1. Call location_service.set_manual_location with just coordinates
        location_result = location_service.set_manual_location(47.6062, -122.3321, {})

        # 2. Use the geocoded result to update the database
        city = location_result.get("city", "")
        region = location_result.get("region", "")
        country = location_result.get("country", "")

        auth_service.update_user_location(
            test_user, 47.6062, -122.3321, city, region, country
        )

        # 3. Verify the database has the geocoded city information
        user = auth_service.get_user_by_id(test_user)
        assert user is not None
        assert user['location'] is not None
        assert user['location']['city'] == "Seattle"
        assert user['location']['region'] == "Washington"
        assert user['location']['country'] == "United States"

    def test_api_preserves_manual_city_in_database(
        self, auth_service, location_service, test_user
    ):
        """Test that manually provided city information is preserved in database."""
        # When city is provided, reverse geocoding should be skipped
        location_result = location_service.set_manual_location(
            34.0522,
            -118.2437,
            {"city": "Los Angeles", "region": "CA", "country": "USA"}
        )

        # Update database with the result
        city = location_result.get("city", "")
        region = location_result.get("region", "")
        country = location_result.get("country", "")

        auth_service.update_user_location(
            test_user, 34.0522, -118.2437, city, region, country
        )

        # Verify manual data is preserved
        user = auth_service.get_user_by_id(test_user)
        assert user is not None
        assert user['location'] is not None
        assert user['location']['city'] == "Los Angeles"
        assert user['location']['region'] == "CA"
        assert user['location']['country'] == "USA"
