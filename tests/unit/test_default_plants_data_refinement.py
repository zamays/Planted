"""Tests for default plant compatibility refinement logic."""

from garden_manager.database.default_plants_data import _refine_compatibility_lists


def _plant(name, *, season, sun, notes, plant_type="vegetable", companions=None, avoids=None):
    return {
        "name": name,
        "scientific_name": f"{name} scientificus",
        "plant_type": plant_type,
        "growing": {
            "season": season,
            "planting_method": "seed",
            "days_to_germination": 7,
            "days_to_maturity": 70,
            "spacing_inches": 6,
        },
        "care": {
            "sun_requirements": sun,
            "water_needs": "medium",
            "care_notes": notes,
        },
        "compatibility": {
            "companion_plants": companions or [],
            "avoid_plants": avoids or [],
            "climate_zones": [5, 6, 7],
        },
    }


def test_refine_symmetry():
    plants = [
        _plant("Peas", season="spring", sun="full_sun", notes="Nitrogen fixer"),
        _plant("Corn", season="spring", sun="full_sun", notes="Warm season grain"),
        _plant("Lettuce", season="spring", sun="partial_shade", notes="Cool weather crop"),
    ]

    _refine_compatibility_lists(plants)

    peas_companions = plants[0]["compatibility"]["companion_plants"]
    corn_companions = plants[1]["compatibility"]["companion_plants"]
    assert "corn" in peas_companions
    assert "peas" in corn_companions


def test_refine_season_avoid():
    plants = [
        _plant("Peas", season="spring", sun="full_sun", notes="Nitrogen fixer"),
        _plant("Tomato", season="summer", sun="full_sun", notes="Needs warm soil"),
    ]

    _refine_compatibility_lists(plants)

    assert "tomato" in plants[0]["compatibility"]["avoid_plants"]
    assert "peas" in plants[1]["compatibility"]["avoid_plants"]


def test_refine_explicit_avoid():
    plants = [
        _plant("Basil", season="summer", sun="full_sun", notes="Aromatic herb", companions=["fennel"]),
        _plant(
            "Fennel",
            season="summer",
            sun="full_sun",
            notes="Can inhibit nearby plants",
            avoids=["basil"],
        ),
    ]

    _refine_compatibility_lists(plants)

    assert "fennel" in plants[0]["compatibility"]["avoid_plants"]
    assert "fennel" not in plants[0]["compatibility"]["companion_plants"]
