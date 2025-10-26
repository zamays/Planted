"""
Default Plant Data Loader

Loads pre-defined plant data from JSON seed file and transforms it
for database insertion. Provides 40+ common garden plants across all seasons.
"""

import json
import os
from typing import List, Tuple


def get_default_plants_data() -> List[Tuple]:
    """
    Load default plant data from JSON seed file.

    Reads the default_plants.json file and transforms the nested structure
    into flat tuples suitable for database insertion.

    Returns:
        List[Tuple]: List of plant data tuples, each containing:
            (name, scientific_name, plant_type, season, planting_method,
             days_to_germination, days_to_maturity, spacing_inches,
             sun_requirements, water_needs, companion_plants, avoid_plants,
             climate_zones, care_notes)

    Raises:
        FileNotFoundError: If the JSON seed file cannot be found
        json.JSONDecodeError: If the JSON file is malformed
    """
    # Get the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "seeds", "default_plants.json")

    # Load the JSON file
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Transform each plant into a tuple for database insertion
    plants = []
    for plant in data["plants"]:
        plant_tuple = (
            plant["name"],
            plant["scientific_name"],
            plant["plant_type"],
            plant["growing"]["season"],
            plant["growing"]["planting_method"],
            plant["growing"]["days_to_germination"],
            plant["growing"]["days_to_maturity"],
            plant["growing"]["spacing_inches"],
            plant["care"]["sun_requirements"],
            plant["care"]["water_needs"],
            json.dumps(plant["compatibility"]["companion_plants"]),
            json.dumps(plant["compatibility"]["avoid_plants"]),
            json.dumps(plant["compatibility"]["climate_zones"]),
            plant["care"]["care_notes"],
        )
        plants.append(plant_tuple)

    return plants
