"""
Tests for weather service caching functionality.

These tests verify that weather data caching works correctly to reduce
API calls and improve performance, while ensuring mock data continues to work.
"""

from unittest.mock import patch, MagicMock
from requests import RequestException
from garden_manager.services.weather_service import WeatherService


class TestWeatherCaching:
    """Test weather data caching functionality."""

    def test_cache_initialization(self):
        """Test that cache is properly initialized with default TTL."""
        weather_service = WeatherService(api_key="demo_key")

        # Verify caches exist
        assert hasattr(weather_service, '_weather_cache')
        assert hasattr(weather_service, '_forecast_cache')
        assert hasattr(weather_service, '_cache_stats')

        # Verify initial stats
        stats = weather_service.get_cache_stats()
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        assert stats['api_calls'] == 0
        assert stats['total_requests'] == 0

    def test_cache_initialization_custom_ttl(self):
        """Test cache initialization with custom TTL."""
        custom_ttl = 300  # 5 minutes
        weather_service = WeatherService(api_key="demo_key", cache_ttl=custom_ttl)

        # Verify caches are initialized
        assert weather_service._weather_cache is not None
        assert weather_service._forecast_cache is not None

    def test_mock_weather_caching(self):
        """Test that mock weather data is cached properly."""
        weather_service = WeatherService(api_key="demo_key")

        # First call - should be a cache miss
        result1 = weather_service.get_current_weather(40.7128, -74.0060)
        stats1 = weather_service.get_cache_stats()
        assert stats1['cache_misses'] == 1
        assert stats1['cache_hits'] == 0
        assert result1 is not None

        # Second call with same location - should be a cache hit
        result2 = weather_service.get_current_weather(40.7128, -74.0060)
        stats2 = weather_service.get_cache_stats()
        assert stats2['cache_hits'] == 1
        assert stats2['cache_misses'] == 1
        assert result2 == result1

    def test_mock_forecast_caching(self):
        """Test that mock forecast data is cached properly."""
        weather_service = WeatherService(api_key="demo_key")

        # First call - should be a cache miss
        result1 = weather_service.get_forecast(40.7128, -74.0060, days=5)
        stats1 = weather_service.get_cache_stats()
        assert stats1['cache_misses'] == 1
        assert stats1['cache_hits'] == 0
        assert result1 is not None
        assert len(result1) == 5

        # Second call with same location - should be a cache hit
        result2 = weather_service.get_forecast(40.7128, -74.0060, days=5)
        stats2 = weather_service.get_cache_stats()
        assert stats2['cache_hits'] == 1
        assert stats2['cache_misses'] == 1
        assert result2 == result1

    def test_cache_different_locations(self):
        """Test that different locations create separate cache entries."""
        weather_service = WeatherService(api_key="demo_key")

        # Request for location 1
        result1 = weather_service.get_current_weather(40.7128, -74.0060)

        # Request for location 2 - should be a cache miss
        weather_service.get_current_weather(34.0522, -118.2437)
        stats = weather_service.get_cache_stats()
        assert stats['cache_misses'] == 2
        assert stats['cache_hits'] == 0

        # Request for location 1 again - should be a cache hit
        result3 = weather_service.get_current_weather(40.7128, -74.0060)
        stats = weather_service.get_cache_stats()
        assert stats['cache_hits'] == 1
        assert result3 == result1

    def test_cache_bypass(self):
        """Test cache bypass functionality."""
        weather_service = WeatherService(api_key="demo_key")

        # First call - cache miss
        weather_service.get_current_weather(40.7128, -74.0060)

        # Second call with bypass - should not use cache
        weather_service.get_current_weather(40.7128, -74.0060, bypass_cache=True)
        stats = weather_service.get_cache_stats()

        # Should have 2 misses and 0 hits (bypass ignores cache)
        assert stats['cache_misses'] == 2
        assert stats['cache_hits'] == 0

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        weather_service = WeatherService(api_key="demo_key")

        # Populate cache
        weather_service.get_current_weather(40.7128, -74.0060)
        weather_service.get_forecast(40.7128, -74.0060)

        stats_before = weather_service.get_cache_stats()
        assert stats_before['weather_cache_size'] > 0
        assert stats_before['forecast_cache_size'] > 0

        # Clear cache
        weather_service.clear_cache()

        stats_after = weather_service.get_cache_stats()
        assert stats_after['weather_cache_size'] == 0
        assert stats_after['forecast_cache_size'] == 0

        # Stats counters should remain (not reset)
        assert stats_after['cache_misses'] == stats_before['cache_misses']

    def test_cache_stats_hit_rate(self):
        """Test cache statistics hit rate calculation."""
        weather_service = WeatherService(api_key="demo_key")

        # Generate some cache hits and misses
        weather_service.get_current_weather(40.7128, -74.0060)  # miss
        weather_service.get_current_weather(40.7128, -74.0060)  # hit
        weather_service.get_current_weather(40.7128, -74.0060)  # hit
        weather_service.get_current_weather(34.0522, -118.2437)  # miss

        stats = weather_service.get_cache_stats()
        assert stats['cache_hits'] == 2
        assert stats['cache_misses'] == 2
        assert stats['total_requests'] == 4
        assert stats['hit_rate_percent'] == 50.0

    def test_cache_coordinates_rounding(self):
        """Test that similar coordinates are treated as same cache key."""
        weather_service = WeatherService(api_key="demo_key")

        # Request with precise coordinates
        weather_service.get_current_weather(40.7128111, -74.0060222)

        # Request with slightly different coordinates (should round to same key)
        weather_service.get_current_weather(40.7128999, -74.0060999)
        stats = weather_service.get_cache_stats()

        # Should be a cache hit because coordinates round to the same values
        assert stats['cache_hits'] == 1
        assert stats['cache_misses'] == 1

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_real_api_caching(self, mock_get):
        """Test caching with simulated real API calls."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {
                "temp": 72.5,
                "humidity": 60,
                "pressure": 1013,
                "feels_like": 74.2
            },
            "weather": [{"description": "clear sky"}],
            "wind": {"speed": 5.3}
        }
        mock_get.return_value = mock_response

        # Use real API key (will use mocked response)
        weather_service = WeatherService(api_key="test_real_key")

        # First call - should call API
        result1 = weather_service.get_current_weather(40.7128, -74.0060)
        assert mock_get.call_count == 1
        assert result1 is not None
        assert result1['temperature'] == 72  # rounded from 72.5

        # Second call - should use cache (no additional API call)
        result2 = weather_service.get_current_weather(40.7128, -74.0060)
        assert mock_get.call_count == 1  # Still 1 (cached)
        assert result2 == result1

        stats = weather_service.get_cache_stats()
        assert stats['cache_hits'] == 1
        assert stats['cache_misses'] == 1
        assert stats['api_calls'] == 1

    @patch('garden_manager.services.weather_service.requests.Session.get')
    def test_api_error_fallback_to_mock(self, mock_get):
        """Test that API errors fall back to mock data and cache it."""
        # Mock API error (use RequestException which is caught in the code)
        mock_get.side_effect = RequestException("API Error")

        weather_service = WeatherService(api_key="test_real_key")

        # Should return mock data on error
        result1 = weather_service.get_current_weather(40.7128, -74.0060)
        assert result1 is not None
        assert result1['temperature'] == 72  # Mock data default

        # Second call should use cached mock data
        result2 = weather_service.get_current_weather(40.7128, -74.0060)
        stats = weather_service.get_cache_stats()
        assert stats['cache_hits'] == 1
        assert result2 == result1

    def test_forecast_different_days_cached_separately(self):
        """Test that forecasts with different day counts are cached separately."""
        weather_service = WeatherService(api_key="demo_key")

        # Request 3-day forecast
        result1 = weather_service.get_forecast(40.7128, -74.0060, days=3)
        assert len(result1) == 3

        # Request 5-day forecast (same location, different days)
        result2 = weather_service.get_forecast(40.7128, -74.0060, days=5)
        assert len(result2) == 5

        # Both should be cache misses (different cache keys)
        stats = weather_service.get_cache_stats()
        assert stats['cache_misses'] == 2
        assert stats['cache_hits'] == 0

        # Request 3-day again - should be cache hit
        result3 = weather_service.get_forecast(40.7128, -74.0060, days=3)
        stats = weather_service.get_cache_stats()
        assert stats['cache_hits'] == 1
        assert result3 == result1

    def test_cache_stats_structure(self):
        """Test that cache stats return proper structure."""
        weather_service = WeatherService(api_key="demo_key")
        stats = weather_service.get_cache_stats()

        # Verify all expected keys are present
        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
        assert 'api_calls' in stats
        assert 'total_requests' in stats
        assert 'hit_rate_percent' in stats
        assert 'weather_cache_size' in stats
        assert 'forecast_cache_size' in stats

        # Verify types
        assert isinstance(stats['cache_hits'], int)
        assert isinstance(stats['cache_misses'], int)
        assert isinstance(stats['api_calls'], int)
        assert isinstance(stats['total_requests'], int)
        assert isinstance(stats['hit_rate_percent'], (int, float))
        assert isinstance(stats['weather_cache_size'], int)
        assert isinstance(stats['forecast_cache_size'], int)
