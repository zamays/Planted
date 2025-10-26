"""
Location Service for Geographic Data

Handles user location detection and climate zone determination for gardening
recommendations. Uses IP-based geolocation with manual location override.
"""


from typing import Dict, Optional
import requests


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
            response = requests.get("http://ip-api.com/json/", timeout=5)
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
                    return self.current_location
        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Error getting location: {e}")
        return None

    def set_manual_location(
        self,
        latitude: float,
        longitude: float,
        city: str = "",
        region: str = "",
        country: str = "",
    ) -> Dict[str, str]:
        """
        Manually set user location with coordinates.

        Args:
            latitude: Geographic latitude (-90 to 90)
            longitude: Geographic longitude (-180 to 180)
            city: City name (optional)
            region: State/region name (optional)
            country: Country name (optional)

        Returns:
            Dict[str, str]: The set location data
        """
        self.current_location = {
            "city": city,
            "region": region,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "",
        }
        self.climate_zone = self._determine_climate_zone(latitude)
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
        if lat >= 60:  # Arctic regions
            return 3
        elif lat >= 50:  # Northern Canada, Alaska
            return 4
        elif lat >= 45:  # Northern US border states
            return 5
        elif lat >= 40:  # Northern US (New York, Chicago)
            return 6
        elif lat >= 35:  # Mid-latitude US (North Carolina, Tennessee)
            return 7
        elif lat >= 30:  # Southern US (Texas, Georgia)
            return 8
        elif lat >= 25:  # Subtropical (South Florida, Hawaii)
            return 9
        else:  # Tropical regions
            return 10

    def get_location_display(self) -> str:
        """
        Get a human-readable location string for display.

        Returns:
            str: Formatted location string (e.g., "New York, NY" or coordinates)
        """
        if not self.current_location:
            return "Location not set"

        city = self.current_location.get("city", "")
        region = self.current_location.get("region", "")
        country = self.current_location.get("country", "")

        if city and region:
            return f"{city}, {region}"
        elif city and country:
            return f"{city}, {country}"
        elif region and country:
            return f"{region}, {country}"
        elif country:
            return country
        else:
            return (
                f"Lat: {self.current_location['latitude']:.2f}, "
                f"Lon: {self.current_location['longitude']:.2f}"
            )
