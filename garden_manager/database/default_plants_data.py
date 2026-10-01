"""
Default Plant Data Loader

Loads pre-defined plant data from JSON seed file and transforms it
for database insertion. Provides 40+ common garden plants across all seasons.
"""

import json
import os
from itertools import combinations
from typing import Dict, List, Set, Tuple


SEED_DEPTH_HINTS = {
    "arugula": 0.25,
    "beet greens": 0.5,
    "beets": 0.5,
    "bok choy": 0.25,
    "broccoli": 0.5,
    "brussels sprouts": 0.5,
    "cabbage": 0.5,
    "carrots": 0.25,
    "cauliflower": 0.5,
    "celery": 0.125,
    "chard": 0.5,
    "cilantro": 0.25,
    "collard greens": 0.5,
    "corn": 1.0,
    "cucumber": 1.0,
    "dill": 0.25,
    "edamame": 1.0,
    "fava beans": 1.0,
    "fennel": 0.25,
    "garlic": 2.0,
    "green beans": 1.0,
    "kale": 0.5,
    "kohlrabi": 0.5,
    "lettuce": 0.25,
    "lima beans": 1.5,
    "mustard greens": 0.5,
    "okra": 1.0,
    "onions": 0.5,
    "parsley": 0.25,
    "parsnips": 0.5,
    "peas": 1.0,
    "pole beans": 1.0,
    "pumpkin": 1.5,
    "radishes": 0.5,
    "rutabaga": 0.5,
    "spinach": 0.5,
    "summer squash": 1.0,
    "swiss chard": 0.5,
    "turnips": 0.5,
    "watermelon": 1.0,
    "winter squash": 1.0,
    "zucchini": 1.0,
}

HEAVY_FEEDER_KEYWORDS = {
    "corn",
    "broccoli",
    "brussels sprouts",
    "cabbage",
    "cauliflower",
    "eggplant",
    "melon",
    "pepper",
    "pumpkin",
    "squash",
    "tomato",
    "watermelon",
}

LIGHT_FEEDER_KEYWORDS = {
    "herb",
    "radish",
    "onion",
    "garlic",
    "turnip",
}


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

    _refine_compatibility_lists(data["plants"])

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


def _refine_compatibility_lists(plants: List[Dict]) -> None:  # pylint: disable=too-many-locals
    """Cross-check every plant pair and refine companion/avoid recommendations."""
    name_to_plant = {plant["name"].lower(): plant for plant in plants}
    companions: Dict[str, Set[str]] = {name: set() for name in name_to_plant}
    avoids: Dict[str, Set[str]] = {name: set() for name in name_to_plant}

    for plant in plants:
        name = plant["name"].lower()
        for companion in plant["compatibility"]["companion_plants"]:
            normalized = companion.lower()
            if normalized in name_to_plant:
                companions[name].add(normalized)
        for avoided in plant["compatibility"]["avoid_plants"]:
            normalized = avoided.lower()
            if normalized in name_to_plant:
                avoids[name].add(normalized)

    checked_pairs = []
    for first, second in combinations(plants, 2):
        first_name = first["name"].lower()
        second_name = second["name"].lower()
        checked_pairs.append((first_name, second_name))

        relation = _evaluate_pair_relationship(first, second, companions, avoids)
        if relation == "avoid":
            avoids[first_name].add(second_name)
            avoids[second_name].add(first_name)
            companions[first_name].discard(second_name)
            companions[second_name].discard(first_name)
        elif relation == "companion":
            if second_name not in avoids[first_name] and first_name not in avoids[second_name]:
                companions[first_name].add(second_name)
                companions[second_name].add(first_name)

    expected_pairs = len(plants) * (len(plants) - 1) // 2
    if len(checked_pairs) != expected_pairs:
        raise ValueError("Not all plant-to-plant interactions were evaluated")

    for plant in plants:
        name = plant["name"].lower()
        resolved_companions = sorted(companions[name] - avoids[name])
        resolved_avoids = sorted(avoids[name])
        plant["compatibility"]["companion_plants"] = resolved_companions
        plant["compatibility"]["avoid_plants"] = resolved_avoids


def _evaluate_pair_relationship(
    first: Dict, second: Dict, companions: Dict[str, Set[str]], avoids: Dict[str, Set[str]]
) -> str:
    """Score pair compatibility and return companion/avoid/neutral relationship."""
    first_name = first["name"].lower()
    second_name = second["name"].lower()

    explicit_avoid = second_name in avoids[first_name] or first_name in avoids[second_name]
    if explicit_avoid:
        return "avoid"

    explicit_companion = second_name in companions[first_name] or first_name in companions[second_name]
    score = 3 if explicit_companion else 0

    if first["growing"]["season"] != second["growing"]["season"]:
        return "avoid"

    score += _sun_compatibility_score(first["care"]["sun_requirements"], second["care"]["sun_requirements"])
    score += _seed_depth_score(_infer_seed_depth(first), _infer_seed_depth(second))
    score += _nutrient_synergy_score(_infer_nutrient_profile(first), _infer_nutrient_profile(second))

    if score <= -2:
        return "avoid"
    if score >= 2:
        return "companion"
    return "neutral"


def _sun_compatibility_score(first_sun: str, second_sun: str) -> int:
    if first_sun == second_sun:
        return 1
    if {"full_sun", "shade"} == {first_sun, second_sun}:
        return -2
    return -1


def _seed_depth_score(first_depth: float, second_depth: float) -> int:
    depth_difference = abs(first_depth - second_depth)
    if depth_difference <= 0.5:
        return 1
    if depth_difference >= 1.5:
        return -1
    return 0


def _nutrient_synergy_score(first_profile: str, second_profile: str) -> int:
    profile_pair = {first_profile, second_profile}
    if first_profile == "nitrogen_fixer" and second_profile == "nitrogen_fixer":
        return 0
    if profile_pair == {"nitrogen_fixer", "heavy_feeder"}:
        return 2
    if first_profile == "heavy_feeder" and second_profile == "heavy_feeder":
        return -2
    if profile_pair == {"heavy_feeder", "light_feeder"}:
        return -1
    return 0


def _infer_seed_depth(plant: Dict) -> float:
    name = plant["name"].lower()
    if name in SEED_DEPTH_HINTS:
        return SEED_DEPTH_HINTS[name]

    if plant["growing"]["planting_method"] == "transplant":
        return 1.5
    spacing = plant["growing"]["spacing_inches"]
    if spacing <= 6:
        return 0.25
    if spacing <= 12:
        return 0.5
    return 1.0


def _infer_nutrient_profile(plant: Dict) -> str:
    notes = plant["care"]["care_notes"].lower()
    name = plant["name"].lower()
    if "nitrogen fixer" in notes:
        return "nitrogen_fixer"
    if any(keyword in name for keyword in HEAVY_FEEDER_KEYWORDS):
        return "heavy_feeder"
    if plant["plant_type"] == "fruit":
        return "heavy_feeder"
    if any(keyword in name for keyword in LIGHT_FEEDER_KEYWORDS):
        return "light_feeder"
    return "moderate_feeder"
