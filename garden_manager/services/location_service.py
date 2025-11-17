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

            response = requests.get(url, params=params, headers=headers, timeout=5)

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

        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"Error reverse geocoding location: {e}")

        return None

    def set_manual_location(
        self,
        latitude: float,
        longitude: float,
        location_details: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Manually set user location with coordinates.

        Args:
            latitude: Geographic latitude (-90 to 90)
            longitude: Geographic longitude (-180 to 180)
            location_details: Optional dictionary with keys 'city', 'region', 'country'

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
            str: Formatted location string (e.g., "New York, NY" or coordinates)
        """
        if not self.current_location:
            return "Location not set"

        city = self.current_location.get("city", "")
        region = self.current_location.get("region", "")
        country = self.current_location.get("country", "")

        if city and region:
            return f"{city}, {region}"
        if city and country:
            return f"{city}, {country}"
        if region and country:
            return f"{region}, {country}"
        if country:
            return country
        return (
            f"Lat: {self.current_location['latitude']:.2f}, "
            f"Lon: {self.current_location['longitude']:.2f}"
        )
