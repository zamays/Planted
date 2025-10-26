"""
Weather Service Integration

Provides weather data from OpenWeatherMap API with fallback to mock data.
Includes gardening-specific weather analysis and recommendations.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests


class WeatherService:
    """
    Weather data service with gardening-focused features.

    Integrates with OpenWeatherMap API to provide current weather and forecasts.
    Includes specialized methods for watering recommendations, frost warnings,
    and planting condition assessments.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather service.

        Args:
            api_key: OpenWeatherMap API key. If None, loads from environment variable
                    OPENWEATHERMAP_API_KEY. Falls back to demo mode if not available.
        """
        # Priority: 1) Provided argument, 2) Environment variable, 3) Demo mode
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")

        if not self.api_key:
            print("⚠️  No OpenWeatherMap API key found. Using mock weather data.")
            print(
                "   To use real weather data, add OPENWEATHERMAP_API_KEY to your .env file"
            )
            self.api_key = "demo_key"

        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.current_weather = None
        self.forecast = None

    def get_current_weather(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Fetch current weather conditions for a location.

        Args:
            latitude: Geographic latitude
            longitude: Geographic longitude

        Returns:
            Optional[Dict]: Weather data including temperature, humidity, description,
                          wind speed, pressure, and feels-like temperature.
                          Returns None if API call fails.
        """
        if self.api_key == "demo_key":
            return self._get_mock_weather()

        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "imperial",
            }

            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.current_weather = {
                    "temperature": round(data["main"]["temp"]),
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "pressure": data["main"]["pressure"],
                    "feels_like": round(data["main"]["feels_like"]),
                    "timestamp": datetime.now(),
                }
                return self.current_weather
            return self._get_mock_weather()
        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Error fetching weather: {e}")
            return self._get_mock_weather()

    def get_forecast(
        self, latitude: float, longitude: float, days: int = 5
    ) -> Optional[List[Dict]]:
        """
        Fetch weather forecast for a location.

        Args:
            latitude: Geographic latitude
            longitude: Geographic longitude
            days: Number of forecast days (default 5)

        Returns:
            Optional[List[Dict]]: List of daily forecasts with date, temperature,
                                humidity, description, and precipitation data.
                                Returns None if API call fails.
        """
        if self.api_key == "demo_key":
            return self._get_mock_forecast(days)

        try:
            url = f"{self.base_url}/forecast"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "imperial",
                "cnt": days * 8,  # 8 forecasts per day (every 3 hours)
            }

            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                forecast = []

                for item in data["list"][::8]:  # Take every 8th item (daily)
                    forecast.append(
                        {
                            "date": datetime.fromtimestamp(item["dt"]),
                            "temperature": round(item["main"]["temp"]),
                            "humidity": item["main"]["humidity"],
                            "description": item["weather"][0]["description"],
                            "precipitation": item.get("rain", {}).get("3h", 0)
                            + item.get("snow", {}).get("3h", 0),
                        }
                    )

                self.forecast = forecast
                return forecast
            return self._get_mock_forecast(days)
        except (requests.RequestException, KeyError, ValueError, IndexError) as e:
            print(f"Error fetching forecast: {e}")
            return self._get_mock_forecast(days)

    def get_watering_recommendation(self, plant_water_needs: str) -> str:
        """
        Generate watering recommendation based on weather and plant needs.

        Considers current temperature, humidity, and plant water requirements
        to provide actionable watering guidance.

        Args:
            plant_water_needs: Plant's water requirement level (low, medium, high)

        Returns:
            str: Specific watering recommendation
        """
        if not self.current_weather:
            return "Check soil moisture"

        temp = self.current_weather["temperature"]
        humidity = self.current_weather["humidity"]

        # Base watering need score based on plant requirements
        base_needs = {"low": 1, "medium": 2, "high": 3}
        need_score = base_needs.get(plant_water_needs, 2)

        # Adjust for temperature conditions
        if temp > 85:
            need_score += 1  # Hot weather increases water needs
            if humidity < 30:
                need_score += 1  # Hot and dry conditions need extra water
        elif temp < 60:
            need_score -= 0.5  # Cool weather reduces water needs

        # Adjust for humidity levels
        if humidity > 70:
            need_score -= 0.5  # High humidity reduces water needs

        if need_score >= 3.5:
            return "Water immediately - hot and dry conditions"
        if need_score >= 2.5:
            return "Water today"
        if need_score >= 1.5:
            return "Water if soil feels dry"
        return "Skip watering today"

    def check_frost_warning(self) -> bool:
        """
        Check for frost conditions in the next 3 days.

        Returns:
            bool: True if freezing temperatures (≤32°F) are forecasted
        """
        if not self.forecast:
            return False

        for day in self.forecast[:3]:  # Check next 3 days
            if day["temperature"] <= 32:
                return True
        return False

    def get_planting_conditions(self) -> Dict[str, str]:
        """
        Assess current conditions for outdoor planting.

        Evaluates temperature and humidity to determine planting suitability.

        Returns:
            Dict[str, str]: Contains 'status' (excellent/good/fair/poor) and
                           'recommendation' with specific guidance
        """
        if not self.current_weather:
            return {"status": "unknown", "recommendation": "Check weather conditions"}

        temp = self.current_weather["temperature"]
        humidity = self.current_weather["humidity"]

        if temp < 40:
            return {
                "status": "poor",
                "recommendation": "Too cold for most plants. Wait for warmer weather.",
            }
        if temp > 95:
            return {
                "status": "poor",
                "recommendation": "Too hot for planting. Wait for cooler temperatures.",
            }
        if 50 <= temp <= 80 and 40 <= humidity <= 70:
            return {
                "status": "excellent",
                "recommendation": "Perfect conditions for planting!",
            }
        if 45 <= temp <= 85:
            return {
                "status": "good",
                "recommendation": "Good conditions for planting most crops.",
            }
        return {
            "status": "fair",
            "recommendation": "Acceptable for planting hardy varieties.",
        }

    def _get_mock_weather(self) -> Dict:
        """
        Generate mock weather data for demo mode.

        Returns:
            Dict: Simulated current weather conditions
        """
        return {
            "temperature": 72,
            "humidity": 55,
            "description": "partly cloudy",
            "wind_speed": 5.2,
            "pressure": 1013,
            "feels_like": 74,
            "timestamp": datetime.now(),
        }

    def _get_mock_forecast(self, days: int) -> List[Dict]:
        """
        Generate mock forecast data for demo mode.

        Args:
            days: Number of forecast days to generate

        Returns:
            List[Dict]: Simulated daily forecast data
        """
        forecast = []
        base_temp = 70

        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            temp_variation = (i * 2) - days  # Slight temperature variation

            forecast.append(
                {
                    "date": date,
                    "temperature": round(base_temp + temp_variation),
                    "humidity": 50 + (i * 5),
                    "description": [
                        "sunny",
                        "partly cloudy",
                        "cloudy",
                        "light rain",
                        "clear",
                    ][i % 5],
                    "precipitation": 0.1 if i % 4 == 3 else 0,
                }
            )

        return forecast
