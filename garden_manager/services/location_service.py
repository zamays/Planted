"""
Location Service for Geographic Data

Handles user location detection and climate zone determination for gardening
recommendations. Uses IP-based geolocation with manual location override.
"""


import os
from typing import Dict, Optional

import requests
from requests.exceptions import Timeout

from garden_manager.config import get_logger
from garden_manager.services.http_session import create_retry_session

logger = get_logger(__name__)


class LocationService:
    """
    Service for managing user location and climate information.

    Provides automatic location detection via IP geolocation and manual
    location setting. Calculates USDA hardiness zones based on latitude
    for plant compatibility recommendations.
    """

    def __init__(self):
        """
        Initialize location service with no set location.
        """
        self.current_location = None
        self.climate_zone = None
        self.is_default_location = False  # Track if using fallback default location

        # Configure API timeout from environment (default: 10 seconds)
        self.api_timeout = int(os.getenv("API_TIMEOUT", "10"))

        self._session = create_retry_session()

    def get_location_by_ip(self) -> Optional[Dict[str, str]]:
        """
        Automatically detect user location using IP geolocation.

        Uses the ip-api.com service to determine location from user's IP address.
        Automatically calculates and sets the climate zone.

        Returns:
            Optional[Dict[str, str]]: Location data including city, region, country,
                                    coordinates, and timezone. Returns None if detection fails.
        """
        try:
            url = "http://ip-api.com/json/"
            response = self._session.get(url, timeout=self.api_timeout)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success":
                    self.current_location = {
                        "city": data["city"],
                        "region": data["regionName"],
                        "country": data["country"],
                        "latitude": data["lat"],
                        "longitude": data["lon"],
                        "timezone": data["timezone"],
                    }
                    self.climate_zone = self._determine_climate_zone(data["lat"])
                    logger.info("Location detected: %s, %s (%s)", data["city"], data["regionName"], data["country"])
                    return self.current_location
        except Timeout:
            logger.warning(
                "Request to %s timed out after %d seconds",
                url, self.api_timeout
            )
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error("Error getting location by IP: %s", e, exc_info=True)
        return None

    def _reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Optional[Dict[str, str]]:
        """
        Convert coordinates to location names using reverse geocoding.

        Uses Nominatim (OpenStreetMap) API to convert latitude/longitude
        to human-readable city, region, and country names.

        Args:
            latitude: Geographic latitude
            longitude: Geographic longitude

        Returns:
            Optional[Dict[str, str]]: Dictionary with 'city', 'region', 'country'
                                     keys, or None if geocoding fails
        """
        try:
            # Use Nominatim API (OpenStreetMap) for reverse geocoding
            # Free service, no API key required
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1,
            }
            headers = {
                # Nominatim requires a User-Agent header
                "User-Agent": "Planted-Garden-App/1.0"
            }

            response = self._session.get(url, params=params, headers=headers, timeout=self.api_timeout)

            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})

                # Extract location information
                # Try various fields for city (in order of preference)
                city = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or address.get("municipality")
                    or address.get("hamlet")
                    or ""
                )

                # Get region/state
                region = address.get("state") or address.get("province") or ""

                # Get country
                country = address.get("country") or ""

                return {"city": city, "region": region, "country": country}

        except Timeout:
            logger.warning(
                "Request to %s timed out after %d seconds",
                url, self.api_timeout
            )
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error("Error reverse geocoding location: %s", e, exc_info=True)

        return None

    def set_manual_location(
        self,
        latitude: float,
        longitude: float,
        location_details: Optional[Dict[str, str]] = None,
        is_default: bool = False,
    ) -> Dict[str, str]:
        """
        Manually set user location with coordinates.

        Args:
            latitude: Geographic latitude (-90 to 90)
            longitude: Geographic longitude (-180 to 180)
            location_details: Optional dictionary with keys 'city', 'region', 'country'
            is_default: Whether this is the default fallback location

        Returns:
            Dict[str, str]: The set location data
        """
        if location_details is None:
            location_details = {}

        # If no city information provided, try reverse geocoding
        if not location_details.get("city"):
            geocoded = self._reverse_geocode(latitude, longitude)
            if geocoded:
                location_details = geocoded

        self.current_location = {
            "city": location_details.get("city", ""),
            "region": location_details.get("region", ""),
            "country": location_details.get("country", ""),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "",
        }
        self.climate_zone = self._determine_climate_zone(latitude)
        self.is_default_location = is_default
        return self.current_location

    def get_climate_zone(self) -> int:
        """
        Get the USDA hardiness zone for the current location.

        Returns:
            int: USDA hardiness zone (3-10), defaults to 6 if no location set
        """
        if self.climate_zone is None and self.current_location:
            self.climate_zone = self._determine_climate_zone(
                self.current_location["latitude"]
            )
        return self.climate_zone or 6  # Default to zone 6

    def _determine_climate_zone(self, latitude: float) -> int:
        """
        Calculate USDA hardiness zone based on latitude.

        Provides approximate hardiness zones based on latitude bands.
        More northern latitudes get lower zone numbers (colder).

        Args:
            latitude: Geographic latitude

        Returns:
            int: USDA hardiness zone (3-10)
        """
        lat = abs(latitude)  # Use absolute value for both hemispheres

        # Map latitude bands to USDA hardiness zones
        # Higher latitudes = colder climates = lower zone numbers
        # Tuples of (min_latitude, zone, description)
        zone_bands = [
            (60, 3, "Arctic regions"),
            (50, 4, "Northern Canada, Alaska"),
            (45, 5, "Northern US border states"),
            (40, 6, "Northern US (New York, Chicago)"),
            (35, 7, "Mid-latitude US (North Carolina, Tennessee)"),
            (30, 8, "Southern US (Texas, Georgia)"),
            (25, 9, "Subtropical (South Florida, Hawaii)"),
            (0, 10, "Tropical regions"),
        ]

        for min_lat, zone, _ in zone_bands:
            if lat >= min_lat:
                return zone

        return 10  # Default to tropical

    def get_location_display(self) -> str:
        """
        Get a human-readable location string for display.

        Returns:
            str: Formatted location string (e.g., "New York, NY")
        """
        if not self.current_location:
            return "Location not set"

        city = self.current_location.get("city", "")
        region = self.current_location.get("region", "")
        country = self.current_location.get("country", "")

        location_parts = [part for part in (city, region, country) if part]
        if location_parts:
            return ", ".join(location_parts[:2])
        # Fallback to a friendly message instead of raw coordinates
        return "Your location"

    def get_location_info(self) -> dict:
        """
        Get complete location information for display purposes.

        Returns:
            dict: Location info with display string, coordinates,
                  climate zone, and default location status
        """
        return {
            "display": self.get_location_display(),
            "latitude": self.current_location.get("latitude") if self.current_location else None,
            "longitude": self.current_location.get("longitude") if self.current_location else None,
            "climate_zone": self.get_climate_zone(),
            "is_default": self.is_default_location,
            "city": self.current_location.get("city", "") if self.current_location else "",
            "region": self.current_location.get("region", "") if self.current_location else "",
            "country": self.current_location.get("country", "") if self.current_location else "",
        }
