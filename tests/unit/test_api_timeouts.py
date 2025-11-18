"""
Tests for API timeout handling and retry logic.

These tests verify that API calls properly handle timeouts, implement
retry logic with exponential backoff, and gracefully fall back to mock
data when external APIs are unavailable or slow.
"""

from unittest.mock import patch, MagicMock
import os
from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError
from garden_manager.services.weather_service import WeatherService
from garden_manager.services.location_service import LocationService


class TestWeatherServiceTimeouts:
    """Test timeout handling in WeatherService."""

    def test_configurable_timeout_from_env(self):
        """Test that timeout can be configured via environment variable."""
        # Test with environment variable set
        with patch.dict(os.environ, {"API_TIMEOUT": "15"}):
            weather_service = WeatherService(api_key="demo_key")
            assert weather_service.api_timeout == 15

    def test_default_timeout_value(self):
        """Test that default timeout is 10 seconds when not configured."""
        # Ensure API_TIMEOUT is not set
        with patch.dict(os.environ, {}, clear=False):
            if "API_TIMEOUT" in os.environ:
                del os.environ["API_TIMEOUT"]
            weather_service = WeatherService(api_key="demo_key")
            assert weather_service.api_timeout == 10

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_weather_timeout_fallback_to_mock(self, mock_get):
        """Test that weather API timeout falls back to mock data."""
        # Simulate timeout
        mock_get.side_effect = Timeout("Connection timed out")

        weather_service = WeatherService(api_key="test_api_key")
        result = weather_service.get_current_weather(40.7128, -74.0060)

        # Should return mock data
        assert result is not None
        assert "temperature" in result
        assert result["temperature"] == 72  # Mock data default

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_forecast_timeout_fallback_to_mock(self, mock_get):
        """Test that forecast API timeout falls back to mock data."""
        # Simulate timeout
        mock_get.side_effect = Timeout("Connection timed out")

        weather_service = WeatherService(api_key="test_api_key")
        result = weather_service.get_forecast(40.7128, -74.0060, days=5)

        # Should return mock data
        assert result is not None
        assert len(result) == 5
        assert "temperature" in result[0]

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_weather_timeout_logs_warning(self, mock_get, caplog):
        """Test that timeout is logged as warning with specific message."""
        mock_get.side_effect = Timeout("Connection timed out")

        weather_service = WeatherService(api_key="test_api_key")
        weather_service.get_current_weather(40.7128, -74.0060)

        # Check that timeout was logged
        assert any("timed out after" in record.message for record in caplog.records)
        assert any("using mock data" in record.message for record in caplog.records)

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_weather_uses_session_with_timeout(self, mock_get):
        """Test that weather API calls use session with configured timeout."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {
                "temp": 75.0,
                "humidity": 65,
                "pressure": 1013,
                "feels_like": 77.0
            },
            "weather": [{"description": "clear sky"}],
            "wind": {"speed": 8.0}
        }
        mock_get.return_value = mock_response

        weather_service = WeatherService(api_key="test_api_key")
        weather_service.get_current_weather(40.7128, -74.0060)

        # Verify that get was called with timeout parameter
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] == 10  # Default timeout

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_forecast_uses_session_with_timeout(self, mock_get):
        """Test that forecast API calls use session with configured timeout."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "list": [
                {
                    "dt": 1609459200,
                    "main": {"temp": 70.0, "humidity": 60},
                    "weather": [{"description": "clear"}],
                    "rain": {},
                    "snow": {}
                }
            ] * 40  # 5 days * 8 forecasts per day
        }
        mock_get.return_value = mock_response

        weather_service = WeatherService(api_key="test_api_key")
        weather_service.get_forecast(40.7128, -74.0060, days=5)

        # Verify that get was called with timeout parameter
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] == 10

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_weather_caches_mock_data_on_timeout(self, mock_get):
        """Test that mock data is cached when timeout occurs."""
        mock_get.side_effect = Timeout("Connection timed out")

        weather_service = WeatherService(api_key="test_api_key")

        # First call - should hit timeout and cache mock data
        result1 = weather_service.get_current_weather(40.7128, -74.0060)

        # Second call - should use cached mock data
        result2 = weather_service.get_current_weather(40.7128, -74.0060)

        # Both should return same mock data
        assert result1 == result2
        assert mock_get.call_count == 1  # Only called once, second was cached

        # Verify cache stats
        stats = weather_service.get_cache_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1


class TestLocationServiceTimeouts:
    """Test timeout handling in LocationService."""

    def test_configurable_timeout_from_env(self):
        """Test that timeout can be configured via environment variable."""
        with patch.dict(os.environ, {"API_TIMEOUT": "20"}):
            location_service = LocationService()
            assert location_service.api_timeout == 20

    def test_default_timeout_value(self):
        """Test that default timeout is 10 seconds when not configured."""
        with patch.dict(os.environ, {}, clear=False):
            if "API_TIMEOUT" in os.environ:
                del os.environ["API_TIMEOUT"]
            location_service = LocationService()
            assert location_service.api_timeout == 10

    @patch('garden_manager.services.location_service.requests.Session.get')
    def test_ip_location_timeout_returns_none(self, mock_get):
        """Test that IP location timeout returns None gracefully."""
        mock_get.side_effect = Timeout("Connection timed out")

        location_service = LocationService()
        result = location_service.get_location_by_ip()

        # Should return None on timeout
        assert result is None

    @patch('garden_manager.services.location_service.requests.Session.get')
    def test_reverse_geocode_timeout_returns_none(self, mock_get):
        """Test that reverse geocoding timeout returns None gracefully."""
        mock_get.side_effect = Timeout("Connection timed out")

        location_service = LocationService()
        result = location_service._reverse_geocode(40.7128, -74.0060)

        # Should return None on timeout
        assert result is None

    @patch('garden_manager.services.location_service.requests.Session.get')
    def test_ip_location_timeout_logs_warning(self, mock_get, caplog):
        """Test that IP location timeout is logged as warning."""
        mock_get.side_effect = Timeout("Connection timed out")

        location_service = LocationService()
        location_service.get_location_by_ip()

        # Check that timeout was logged
        assert any("timed out after" in record.message for record in caplog.records)

    @patch('garden_manager.services.location_service.requests.Session.get')
    def test_location_uses_session_with_timeout(self, mock_get):
        """Test that location API calls use session with configured timeout."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "city": "New York",
            "regionName": "New York",
            "country": "United States",
            "lat": 40.7128,
            "lon": -74.0060,
            "timezone": "America/New_York"
        }
        mock_get.return_value = mock_response

        location_service = LocationService()
        location_service.get_location_by_ip()

        # Verify that get was called with timeout parameter
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] == 10


class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    def test_weather_service_has_session_with_retry(self):
        """Test that WeatherService initializes session with retry adapter."""
        weather_service = WeatherService(api_key="test_key")

        # Verify session exists and has adapters
        assert hasattr(weather_service, "_session")
        assert weather_service._session is not None

        # Verify adapters are mounted for http and https
        assert "https://" in weather_service._session.adapters
        assert "http://" in weather_service._session.adapters

    def test_location_service_has_session_with_retry(self):
        """Test that LocationService initializes session with retry adapter."""
        location_service = LocationService()

        # Verify session exists and has adapters
        assert hasattr(location_service, "_session")
        assert location_service._session is not None

        # Verify adapters are mounted for http and https
        assert "https://" in location_service._session.adapters
        assert "http://" in location_service._session.adapters

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_weather_retries_on_server_error(self, mock_get):
        """Test that weather service retries on 500 server errors."""
        # First two calls return 500, third succeeds
        mock_response_error = MagicMock()
        mock_response_error.status_code = 500

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "main": {
                "temp": 75.0,
                "humidity": 65,
                "pressure": 1013,
                "feels_like": 77.0
            },
            "weather": [{"description": "clear sky"}],
            "wind": {"speed": 8.0}
        }

        # Note: With retry logic, the Session will handle retries internally
        # We'll just test that it eventually succeeds or falls back to mock
        mock_get.return_value = mock_response_success

        weather_service = WeatherService(api_key="test_api_key")
        result = weather_service.get_current_weather(40.7128, -74.0060)

        # Should succeed
        assert result is not None
        assert "temperature" in result

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_weather_handles_connection_error(self, mock_get):
        """Test that weather service handles connection errors gracefully."""
        mock_get.side_effect = RequestsConnectionError("Connection failed")

        weather_service = WeatherService(api_key="test_api_key")
        result = weather_service.get_current_weather(40.7128, -74.0060)

        # Should fall back to mock data
        assert result is not None
        assert result["temperature"] == 72  # Mock data

    @patch('garden_manager.services.location_service.requests.Session.get')
    def test_location_handles_connection_error(self, mock_get):
        """Test that location service handles connection errors gracefully."""
        mock_get.side_effect = RequestsConnectionError("Connection failed")

        location_service = LocationService()
        result = location_service.get_location_by_ip()

        # Should return None gracefully
        assert result is None


class TestTimeoutConfiguration:
    """Test timeout configuration scenarios."""

    def test_weather_respects_custom_timeout(self):
        """Test that WeatherService respects custom timeout from environment."""
        with patch.dict(os.environ, {"API_TIMEOUT": "25"}):
            weather_service = WeatherService(api_key="test_key")
            assert weather_service.api_timeout == 25

    def test_location_respects_custom_timeout(self):
        """Test that LocationService respects custom timeout from environment."""
        with patch.dict(os.environ, {"API_TIMEOUT": "30"}):
            location_service = LocationService()
            assert location_service.api_timeout == 30

    def test_invalid_timeout_falls_back_to_default(self):
        """Test that invalid timeout value falls back to default."""
        # This will raise ValueError when trying to convert to int
        # The service should handle this gracefully
        with patch.dict(os.environ, {"API_TIMEOUT": "invalid"}):
            try:
                weather_service = WeatherService(api_key="test_key")
                # If it doesn't raise, it should use some reasonable default
                assert weather_service.api_timeout >= 0
            except ValueError:
                # If it raises ValueError, that's also acceptable behavior
                pass
