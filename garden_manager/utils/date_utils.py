"""
Date and Season Utilities for Garden Management

Provides seasonal calculations, planting schedules, and climate-aware
gardening recommendations based on geographic location and time of year.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Union


class SeasonCalculator:
    """
    Utility class for calculating seasons and growing conditions.

    Handles hemisphere-aware season detection and provides seasonal
    planting recommendations based on climate zones.
    """

    @staticmethod
    def get_current_season(latitude: float = 40.0) -> str:
        """
        Determine current season based on date and hemisphere.

        Uses astronomical season dates adjusted for hemisphere location.
        Northern hemisphere uses standard seasons, southern hemisphere
        seasons are reversed.

        Args:
            latitude: Geographic latitude (positive=north, negative=south)

        Returns:
            str: Current season (spring, summer, fall, winter)
        """
        now = datetime.now()
        month = now.month
        day = now.day

        if latitude >= 0:  # Northern Hemisphere - standard seasons
            if (
                (month == 3 and day >= 20)
                or (month in [4, 5])
                or (month == 6 and day < 21)
            ):
                return "spring"
            elif (
                (month == 6 and day >= 21)
                or (month in [7, 8])
                or (month == 9 and day < 23)
            ):
                return "summer"
            elif (
                (month == 9 and day >= 23)
                or (month in [10, 11])
                or (month == 12 and day < 21)
            ):
                return "fall"
            else:
                return "winter"
        else:  # Southern Hemisphere - seasons are reversed
            if (
                (month == 3 and day >= 20)
                or (month in [4, 5])
                or (month == 6 and day < 21)
            ):
                return "fall"
            elif (
                (month == 6 and day >= 21)
                or (month in [7, 8])
                or (month == 9 and day < 23)
            ):
                return "winter"
            elif (
                (month == 9 and day >= 23)
                or (month in [10, 11])
                or (month == 12 and day < 21)
            ):
                return "spring"
            else:
                return "summer"

    @staticmethod
    def get_seasonal_recommendations(
        season: str, climate_zone: int
    ) -> Dict[str, List[str]]:
        """
        Get plant recommendations for a specific season and climate zone.

        Provides lists of plants to plant now, prepare for future seasons,
        and harvest during the current season.

        Args:
            season: Current season (spring, summer, fall, winter)
            climate_zone: USDA hardiness zone

        Returns:
            Dict[str, List[str]]: Recommendations with 'plant_now', 'prepare_for',
                                and 'harvest' categories
        """
        recommendations = {
            "spring": {
                "plant_now": [
                    "lettuce",
                    "spinach",
                    "peas",
                    "radishes",
                    "carrots",
                    "kale",
                ],
                "prepare_for": ["tomatoes", "peppers", "cucumbers", "beans"],
                "harvest": ["stored_crops", "winter_herbs"],
            },
            "summer": {
                "plant_now": [
                    "tomatoes",
                    "peppers",
                    "cucumbers",
                    "beans",
                    "corn",
                    "zucchini",
                ],
                "prepare_for": ["fall_brassicas", "winter_crops"],
                "harvest": ["spring_vegetables", "summer_fruits"],
            },
            "fall": {
                "plant_now": ["broccoli", "cauliflower", "kale", "carrots", "spinach"],
                "prepare_for": ["winter_protection", "spring_planning"],
                "harvest": ["summer_vegetables", "root_crops"],
            },
            "winter": {
                "plant_now": ["microgreens", "indoor_herbs"]
                if climate_zone < 8
                else ["cool_season_vegetables"],
                "prepare_for": ["seed_starting", "garden_planning"],
                "harvest": ["stored_crops", "winter_vegetables"],
            },
        }

        return recommendations.get(season, recommendations["spring"])

    @staticmethod
    def calculate_planting_windows(climate_zone: int) -> Dict[str, Union[str, int]]:
        """
        Calculate planting windows based on climate zone.

        Provides estimated last frost, first frost dates, and growing season
        length for garden planning.

        Args:
            climate_zone: USDA hardiness zone (3-10)

        Returns:
            Dict[str, Union[str, int]]: Contains 'last_frost', 'first_frost'
                                      dates and 'growing_season_days'
        """
        base_last_frost = {
            3: "April 30",
            4: "April 15",
            5: "April 1",
            6: "March 15",
            7: "March 1",
            8: "February 15",
            9: "February 1",
            10: "January 15",
        }

        base_first_frost = {
            3: "October 1",
            4: "October 15",
            5: "November 1",
            6: "November 15",
            7: "December 1",
            8: "December 15",
            9: "December 31",
            10: "January 15",
        }

        return {
            "last_frost": base_last_frost.get(climate_zone, "April 15"),
            "first_frost": base_first_frost.get(climate_zone, "October 15"),
            "growing_season_days": 180 + (climate_zone - 5) * 30,
        }


class PlantingScheduler:
    """
    Utility class for calculating optimal planting schedules.

    Provides methods for determining planting dates, succession planting
    schedules, and seasonal compatibility assessments.
    """

    @staticmethod
    def calculate_optimal_planting_date(
        plant_name: str,
        target_harvest: datetime,
        days_to_maturity: int,
        climate_zone: int,
    ) -> datetime:
        """
        Calculate when to plant for a target harvest date.

        Args:
            plant_name: Name of the plant (for reference)
            target_harvest: Desired harvest date
            days_to_maturity: Plant's days from planting to harvest
            climate_zone: USDA hardiness zone

        Returns:
            datetime: Recommended planting date
        """
        return target_harvest - timedelta(days=days_to_maturity)

    @staticmethod
    def get_succession_planting_dates(
        plant_name: str, start_date: datetime, interval_days: int = 14, count: int = 4
    ) -> List[datetime]:
        """
        Generate succession planting schedule for continuous harvest.

        Args:
            plant_name: Name of the plant (for reference)
            start_date: First planting date
            interval_days: Days between plantings (default 14)
            count: Number of succession plantings (default 4)

        Returns:
            List[datetime]: List of planting dates
        """
        dates = []
        for i in range(count):
            dates.append(start_date + timedelta(days=i * interval_days))
        return dates

    @staticmethod
    def is_good_planting_time(
        plant_season: str, current_season: str, days_to_maturity: int, climate_zone: int
    ) -> bool:
        """
        Determine if current season is suitable for planting a specific crop.

        Args:
            plant_season: Plant's preferred planting season
            current_season: Current season
            days_to_maturity: Plant's maturation time
            climate_zone: USDA hardiness zone

        Returns:
            bool: True if current season is suitable for planting
        """
        season_compatibility = {
            "spring": ["spring", "fall"]
            if climate_zone < 8
            else ["spring", "fall", "winter"],
            "summer": ["summer", "spring"] if climate_zone > 6 else ["summer"],
            "fall": ["fall", "spring"]
            if climate_zone < 8
            else ["fall", "winter", "spring"],
            "winter": ["winter"] if climate_zone > 7 else [],
        }

        return current_season in season_compatibility.get(plant_season, [])
