from typing import List, Dict, Tuple
import math

class GardenLayoutCalculator:
    @staticmethod
    def calculate_square_foot_spacing(plant_spacing_inches: int) -> int:
        if plant_spacing_inches <= 3:
            return 16  # 16 plants per square foot
        elif plant_spacing_inches <= 4:
            return 9   # 9 plants per square foot
        elif plant_spacing_inches <= 6:
            return 4   # 4 plants per square foot
        elif plant_spacing_inches <= 12:
            return 1   # 1 plant per square foot
        else:
            return 1   # Large plants take full square or more

    @staticmethod
    def can_plants_coexist(plant1_companions: List[str], plant1_avoid: List[str],
                          plant2_name: str) -> Tuple[bool, str]:
        plant2_lower = plant2_name.lower()
        
        if any(avoid.lower() in plant2_lower or plant2_lower in avoid.lower() 
               for avoid in plant1_avoid):
            return False, f"Avoid planting {plant2_name} near this plant"
        
        if any(companion.lower() in plant2_lower or plant2_lower in companion.lower() 
               for companion in plant1_companions):
            return True, f"{plant2_name} is a beneficial companion"
        
        return True, "Neutral compatibility"
    
    @staticmethod
    def calculate_garden_efficiency(plot_width: int, plot_height: int, 
                                  planted_items: List[Dict]) -> Dict[str, object]:
        total_squares = plot_width * plot_height
        used_squares = len(planted_items)
        
        plant_types = {}
        for item in planted_items:
            plant_type = item.get('plant_type', 'unknown')
            plant_types[plant_type] = plant_types.get(plant_type, 0) + 1
        
        return {
            "utilization_percentage": (used_squares / total_squares) * 100,
            "total_squares": total_squares,
            "used_squares": used_squares,
            "available_squares": total_squares - used_squares,
            "plant_diversity": len(plant_types),
            "plant_distribution": plant_types
        }

class PlantCareCalculator:
    @staticmethod
    def calculate_water_needs(plant_water_needs: str, weather_temp: float, 
                            humidity: float, days_since_planted: int) -> str:
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
        elif need_score >= 2.5:
            return "Water every 2-3 days"
        elif need_score >= 1.5:
            return "Water weekly"
        else:
            return "Water when soil is dry"
    
    @staticmethod
    def get_fertilizer_schedule(plant_type: str, days_to_maturity: int) -> List[Dict[str, str]]:
        schedules = {
            "vegetable": [
                {"days": 0, "type": "starter", "description": "Balanced fertilizer at planting"},
                {"days": 14, "type": "growth", "description": "Nitrogen-rich for leaf development"},
                {"days": days_to_maturity // 2, "type": "flowering", 
                 "description": "Phosphorus-rich for flowering/fruiting"},
                {"days": days_to_maturity * 3 // 4, "type": "maintenance", 
                 "description": "Balanced maintenance feeding"}
            ],
            "herb": [
                {"days": 0, "type": "starter", "description": "Light balanced fertilizer"},
                {"days": 30, "type": "maintenance", "description": "Diluted balanced fertilizer"}
            ],
            "fruit": [
                {"days": 0, "type": "starter", "description": "Balanced fertilizer at planting"},
                {"days": 21, "type": "growth", "description": "Higher potassium for fruit development"},
                {"days": 60, "type": "maintenance", "description": "Balanced feeding"}
            ]
        }
        
        return schedules.get(plant_type, schedules["vegetable"])
    
    @staticmethod
    def assess_plant_health(days_planted: int, expected_germination: int,
                           expected_maturity: int, care_completed: float) -> Dict[str, object]:
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
            "care_score": care_completed * 100
        }