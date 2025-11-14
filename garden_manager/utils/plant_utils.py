"""
Plant Care and Garden Layout Utilities

Provides calculators for garden layout optimization, plant spacing,
companion planting, and care scheduling based on plant needs.
"""

from typing import List, Dict, Tuple


def is_plant_suggested(plant_season: str, plant_climate_zones: List[int],
                       current_season: str, user_climate_zone: int) -> bool:
    """
    Determine if a plant is suggested for the user based on season and climate.

    A plant is suggested when it matches both the current season and is compatible
    with the user's climate zone.

    Args:
        plant_season: Plant's optimal planting season (spring, summer, fall, winter)
        plant_climate_zones: List of USDA climate zones where plant can grow
        current_season: Current season (spring, summer, fall, winter)
        user_climate_zone: User's USDA climate zone

    Returns:
        bool: True if plant is suggested for the user
    """
    # Check if plant matches current season
    season_match = plant_season.lower() == current_season.lower()

    # Check if plant is compatible with user's climate zone
    # If no zones specified, assume it's compatible with all zones
    climate_match = (not plant_climate_zones or
                     user_climate_zone in plant_climate_zones)

    return season_match and climate_match


class GardenLayoutCalculator:
    """
    Utility class for garden layout calculations and optimization.

    Provides methods for calculating optimal plant spacing, companion
    planting compatibility, and garden space utilization metrics.
    """

    @staticmethod
    def calculate_square_foot_spacing(plant_spacing_inches: int) -> int:
        """
        Calculate how many plants fit in one square foot based on spacing needs.

        Uses square-foot gardening principles to determine plant density.

        Args:
            plant_spacing_inches: Required spacing between plants in inches

        Returns:
            int: Number of plants that can fit in one square foot
        """
        if plant_spacing_inches <= 3:
            return 16  # 16 plants per square foot
        if plant_spacing_inches <= 4:
            return 9  # 9 plants per square foot
        if plant_spacing_inches <= 6:
            return 4  # 4 plants per square foot
        if plant_spacing_inches <= 12:
            return 1  # 1 plant per square foot
        return 1  # Large plants take full square or more

    @staticmethod
    def can_plants_coexist(
        plant1_companions: List[str], plant1_avoid: List[str], plant2_name: str
    ) -> Tuple[bool, str]:
        """
        Check if two plants can be planted together based on companion planting rules.

        Evaluates compatibility using companion and avoid lists to determine
        if plants benefit from proximity or should be kept apart.

        Args:
            plant1_companions: List of beneficial companion plants for plant1
            plant1_avoid: List of plants to avoid planting near plant1
            plant2_name: Name of the second plant to check compatibility with

        Returns:
            Tuple[bool, str]: (can_coexist, compatibility_message)
                - can_coexist: True if plants are compatible
                - compatibility_message: Description of relationship
        """
        plant2_lower = plant2_name.lower()

        if any(
            avoid.lower() in plant2_lower or plant2_lower in avoid.lower()
            for avoid in plant1_avoid
        ):
            return False, f"Avoid planting {plant2_name} near this plant"

        if any(
            companion.lower() in plant2_lower or plant2_lower in companion.lower()
            for companion in plant1_companions
        ):
            return True, f"{plant2_name} is a beneficial companion"

        return True, "Neutral compatibility"

    @staticmethod
    def calculate_garden_efficiency(
        plot_width: int, plot_height: int, planted_items: List[Dict]
    ) -> Dict[str, object]:
        """
        Calculate garden plot utilization and diversity metrics.

        Analyzes how effectively garden space is being used and tracks
        plant diversity for healthy garden ecosystems.

        Args:
            plot_width: Width of the garden plot in squares
            plot_height: Height of the garden plot in squares
            planted_items: List of planted items with plant_type information

        Returns:
            Dict[str, object]: Metrics including:
                - utilization_percentage: Percentage of squares being used
                - total_squares: Total available garden squares
                - used_squares: Number of squares with plants
                - available_squares: Number of empty squares
                - plant_diversity: Number of different plant types
                - plant_distribution: Count of each plant type
        """
        total_squares = plot_width * plot_height
        used_squares = len(planted_items)

        plant_types = {}
        for item in planted_items:
            plant_type = item.get("plant_type", "unknown")
            plant_types[plant_type] = plant_types.get(plant_type, 0) + 1

        return {
            "utilization_percentage": (used_squares / total_squares) * 100,
            "total_squares": total_squares,
            "used_squares": used_squares,
            "available_squares": total_squares - used_squares,
            "plant_diversity": len(plant_types),
            "plant_distribution": plant_types,
        }


class PlantCareCalculator:
    """
    Utility class for calculating plant care requirements.

    Provides methods for determining watering needs, fertilizer schedules,
    and plant health assessments based on growing conditions.
    """

    @staticmethod
    def calculate_water_needs(
        plant_water_needs: str,
        weather_temp: float,
        humidity: float,
        days_since_planted: int,
    ) -> str:
        """
        Calculate watering recommendation based on plant needs and weather.

        Considers plant water requirements, temperature, humidity, and plant age
        to provide specific watering guidance.

        Args:
            plant_water_needs: Plant's water requirement level (low, medium, high)
            weather_temp: Current temperature in Fahrenheit
            humidity: Current humidity percentage
            days_since_planted: Number of days since plant was planted

        Returns:
            str: Specific watering recommendation
        """
        base_needs = {"low": 1, "medium": 2, "high": 3}
        need_score = base_needs.get(plant_water_needs, 2)

        if weather_temp > 85:
            need_score += 1
        elif weather_temp < 60:
            need_score -= 0.5

        if humidity < 30:
            need_score += 0.5
        elif humidity > 70:
            need_score -= 0.5

        if days_since_planted < 14:
            need_score += 0.5

        if need_score >= 3.5:
            return "Water daily - high stress conditions"
        if need_score >= 2.5:
            return "Water every 2-3 days"
        if need_score >= 1.5:
            return "Water weekly"
        return "Water when soil is dry"

    @staticmethod
    def get_fertilizer_schedule(
        plant_type: str, days_to_maturity: int
    ) -> List[Dict[str, str]]:
        """
        Generate fertilizer application schedule based on plant type and growth cycle.

        Provides customized fertilizer schedules with timing and type recommendations
        for optimal plant growth.

        Args:
            plant_type: Type of plant (vegetable, herb, fruit)
            days_to_maturity: Total days from planting to harvest

        Returns:
            List[Dict[str, str]]: Schedule entries with 'days', 'type', and 'description'
        """
        schedules = {
            "vegetable": [
                {
                    "days": 0,
                    "type": "starter",
                    "description": "Balanced fertilizer at planting",
                },
                {
                    "days": 14,
                    "type": "growth",
                    "description": "Nitrogen-rich for leaf development",
                },
                {
                    "days": days_to_maturity // 2,
                    "type": "flowering",
                    "description": "Phosphorus-rich for flowering/fruiting",
                },
                {
                    "days": days_to_maturity * 3 // 4,
                    "type": "maintenance",
                    "description": "Balanced maintenance feeding",
                },
            ],
            "herb": [
                {
                    "days": 0,
                    "type": "starter",
                    "description": "Light balanced fertilizer",
                },
                {
                    "days": 30,
                    "type": "maintenance",
                    "description": "Diluted balanced fertilizer",
                },
            ],
            "fruit": [
                {
                    "days": 0,
                    "type": "starter",
                    "description": "Balanced fertilizer at planting",
                },
                {
                    "days": 21,
                    "type": "growth",
                    "description": "Higher potassium for fruit development",
                },
                {"days": 60, "type": "maintenance", "description": "Balanced feeding"},
            ],
        }

        return schedules.get(plant_type, schedules["vegetable"])

    @staticmethod
    def assess_plant_health(
        days_planted: int,
        expected_germination: int,
        expected_maturity: int,
        care_completed: float,
    ) -> Dict[str, object]:
        """
        Assess plant health status and provide care recommendations.

        Evaluates plant progress against expected growth milestones and
        care task completion to determine health status.

        Args:
            days_planted: Number of days since plant was planted
            expected_germination: Expected days to germination
            expected_maturity: Expected days to maturity/harvest
            care_completed: Percentage of care tasks completed (0.0 to 1.0)

        Returns:
            Dict[str, object]: Health assessment with:
                - status: Plant health status (healthy, needs_attention, ready_harvest)
                - progress_percentage: Growth progress percentage
                - recommendations: List of care recommendations
                - care_score: Care completion score (0-100)
        """
        status = "healthy"
        recommendations = []

        if days_planted > expected_germination + 7 and care_completed < 0.7:
            status = "needs_attention"
            recommendations.append("Increase watering frequency")
            recommendations.append("Check soil temperature")

        if days_planted > expected_maturity and status == "healthy":
            status = "ready_harvest"
            recommendations.append("Check for harvest readiness")

        progress_percentage = min((days_planted / expected_maturity) * 100, 100)

        return {
            "status": status,
            "progress_percentage": progress_percentage,
            "recommendations": recommendations,
            "care_score": care_completed * 100,
        }
