"""
Weather Service Integration

Provides weather data from OpenWeatherMap API with fallback to mock data.
Includes gardening-specific weather analysis and recommendations.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from cachetools import TTLCache
from garden_manager.config import get_logger

logger = get_logger(__name__)


class WeatherService:
    """
    Weather data service with gardening-focused features.

    Integrates with OpenWeatherMap API to provide current weather and forecasts.
    Includes specialized methods for watering recommendations, frost warnings,
    and planting condition assessments.

    Caching: Weather data is cached for 15 minutes (900 seconds) to reduce
    API calls and improve performance. Cache is keyed by location coordinates.
    """

    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 900):
        """
        Initialize weather service.

        Args:
            api_key: OpenWeatherMap API key. If None, loads from environment variable
                    OPENWEATHERMAP_API_KEY. Falls back to demo mode if not available.
            cache_ttl: Time-to-live for cached weather data in seconds (default: 900 = 15 minutes)
        """
        # Priority: 1) Provided argument, 2) Environment variable, 3) Demo mode
        self.api_key = api_key or os.getenv("OPENWEATHERMAP_API_KEY")

        if not self.api_key:
            logger.warning("No OpenWeatherMap API key found. Using mock weather data.")
            logger.info("To use real weather data, add OPENWEATHERMAP_API_KEY to your .env file")
            self.api_key = "demo_key"

        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.current_weather = None
        self.forecast = None

        # Initialize caches with TTL (time-to-live)
        # maxsize=100 allows caching for up to 100 different locations
        self._weather_cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self._forecast_cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self._cache_stats = {"hits": 0, "misses": 0, "api_calls": 0}

    def get_current_weather(self, latitude: float, longitude: float,
                           bypass_cache: bool = False) -> Optional[Dict]:
        """
        Fetch current weather conditions for a location.

        Results are cached for 15 minutes by default to reduce API calls.

        Args:
            latitude: Geographic latitude
            longitude: Geographic longitude
            bypass_cache: If True, force a fresh API call and update cache

        Returns:
            Optional[Dict]: Weather data including temperature, humidity, description,
                          wind speed, pressure, and feels-like temperature.
                          Returns None if API call fails.
        """
        # Create cache key from rounded coordinates (to avoid cache misses from tiny differences)
        cache_key = (round(latitude, 2), round(longitude, 2))

        # Check cache first unless bypass is requested
        if not bypass_cache and cache_key in self._weather_cache:
            self._cache_stats["hits"] += 1
            cached_data = self._weather_cache[cache_key]
            self.current_weather = cached_data
            return cached_data

        # Cache miss - fetch fresh data
        self._cache_stats["misses"] += 1

        if self.api_key == "demo_key":
            weather_data = self._get_mock_weather()
            self._weather_cache[cache_key] = weather_data
            self.current_weather = weather_data
            return weather_data

        try:
            self._cache_stats["api_calls"] += 1
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
                weather_data = {
                    "temperature": round(data["main"]["temp"]),
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": round(data["wind"]["speed"]),
                    "pressure": data["main"]["pressure"],
                    "feels_like": round(data["main"]["feels_like"]),
                    "timestamp": datetime.now(),
                }
                # Store in cache
                self._weather_cache[cache_key] = weather_data
                self.current_weather = weather_data
                return weather_data

            # API error - return mock data as fallback
            logger.warning("Weather API returned error, using mock data")
            weather_data = self._get_mock_weather()
            self._weather_cache[cache_key] = weather_data
            self.current_weather = weather_data
            return weather_data
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error("Error fetching weather: %s", e, exc_info=True)
            weather_data = self._get_mock_weather()
            self._weather_cache[cache_key] = weather_data
            self.current_weather = weather_data
            return weather_data

    def get_forecast(
        self, latitude: float, longitude: float, days: int = 5,
        bypass_cache: bool = False
    ) -> Optional[List[Dict]]:
        """
        Fetch weather forecast for a location.

        Results are cached for 15 minutes by default to reduce API calls.

        Args:
            latitude: Geographic latitude
            longitude: Geographic longitude
            days: Number of forecast days (default 5)
            bypass_cache: If True, force a fresh API call and update cache

        Returns:
            Optional[List[Dict]]: List of daily forecasts with date, temperature,
                                humidity, description, and precipitation data.
                                Returns None if API call fails.
        """
        # Create cache key from rounded coordinates and days
        cache_key = (round(latitude, 2), round(longitude, 2), days)

        # Check cache first unless bypass is requested
        if not bypass_cache and cache_key in self._forecast_cache:
            self._cache_stats["hits"] += 1
            cached_data = self._forecast_cache[cache_key]
            self.forecast = cached_data
            return cached_data

        # Cache miss - fetch fresh data
        self._cache_stats["misses"] += 1

        if self.api_key == "demo_key":
            forecast_data = self._get_mock_forecast(days)
            self._forecast_cache[cache_key] = forecast_data
            self.forecast = forecast_data
            return forecast_data

        try:
            self._cache_stats["api_calls"] += 1
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

                # Store in cache
                self._forecast_cache[cache_key] = forecast
                self.forecast = forecast
                return forecast

            # API error - return mock data as fallback
            logger.warning("Weather forecast API returned error, using mock data")
            forecast_data = self._get_mock_forecast(days)
            self._forecast_cache[cache_key] = forecast_data
            self.forecast = forecast_data
            return forecast_data
        except (requests.RequestException, KeyError, ValueError, IndexError) as e:
            logger.error("Error fetching forecast: %s", e, exc_info=True)
            forecast_data = self._get_mock_forecast(days)
            self._forecast_cache[cache_key] = forecast_data
            self.forecast = forecast_data
            return forecast_data

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
            "wind_speed": 5,
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

    def clear_cache(self):
        """
        Clear all cached weather data.

        Useful for forcing fresh API calls or when location changes.
        """
        self._weather_cache.clear()
        self._forecast_cache.clear()

    def get_cache_stats(self) -> Dict:
        """
        Get cache performance statistics.

        Returns:
            Dict: Statistics including cache hits, misses, API calls,
                 hit rate, and cache sizes
        """
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (
            (self._cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "cache_hits": self._cache_stats["hits"],
            "cache_misses": self._cache_stats["misses"],
            "api_calls": self._cache_stats["api_calls"],
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 1),
            "weather_cache_size": len(self._weather_cache),
            "forecast_cache_size": len(self._forecast_cache),
        }
