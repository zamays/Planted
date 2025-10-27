"""
Tests for weather service windspeed rounding functionality.
"""

from garden_manager.services.weather_service import WeatherService


class TestWindspeedRounding:
    """Test that windspeed values are rounded to the nearest whole number."""

    def test_mock_weather_windspeed_is_integer(self):
        """Test that mock weather returns integer windspeed."""
        weather_service = WeatherService(api_key="demo_key")
        # pylint: disable=protected-access
        weather_data = weather_service._get_mock_weather()

        assert "wind_speed" in weather_data
        assert isinstance(weather_data["wind_speed"], int)
        assert weather_data["wind_speed"] == 5

    def test_windspeed_formatting_in_mock_data(self):
        """Test that windspeed in mock weather data is a whole number."""
        weather_service = WeatherService(api_key="demo_key")
        result = weather_service.get_current_weather(40.7128, -74.0060)

        assert result is not None
        assert "wind_speed" in result
        # Verify it's an integer (whole number)
        assert result["wind_speed"] == int(result["wind_speed"])
