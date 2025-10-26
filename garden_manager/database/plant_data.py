"""
Plant Database Management

Handles plant species data including characteristics, growing requirements,
companion planting information, and care instructions. Provides search
and filtering capabilities for plant selection.
"""

import sqlite3
import json
from typing import List, Optional
from .models import Plant


class PlantDatabase:
    """
    Database interface for plant species information.

    Manages a comprehensive database of plant varieties with growing
    characteristics, companion planting data, and care requirements.
    Includes pre-populated data for common garden plants.
    """

    def __init__(self, db_path: str = "garden.db"):
        """
        Initialize plant database with schema and default data.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
        self.populate_plant_data()

    def init_database(self):
        """
        Create database tables if they don't exist.

        Sets up the complete schema for plants, garden plots, planted items,
        and care tasks with proper foreign key relationships.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    scientific_name TEXT,
                    plant_type TEXT,
                    season TEXT,
                    planting_method TEXT,
                    days_to_germination INTEGER,
                    days_to_maturity INTEGER,
                    spacing_inches INTEGER,
                    sun_requirements TEXT,
                    water_needs TEXT,
                    companion_plants TEXT,
                    avoid_plants TEXT,
                    climate_zones TEXT,
                    care_notes TEXT,
                    is_custom BOOLEAN DEFAULT FALSE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS garden_plots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    width INTEGER,
                    height INTEGER,
                    location TEXT,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS planted_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plant_id INTEGER,
                    plot_id INTEGER,
                    x_position INTEGER,
                    y_position INTEGER,
                    planted_date DATETIME,
                    expected_harvest DATETIME,
                    notes TEXT,
                    FOREIGN KEY (plant_id) REFERENCES plants (id),
                    FOREIGN KEY (plot_id) REFERENCES garden_plots (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS care_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    planted_item_id INTEGER,
                    task_type TEXT,
                    due_date DATETIME,
                    completed BOOLEAN DEFAULT FALSE,
                    notes TEXT,
                    FOREIGN KEY (planted_item_id) REFERENCES planted_items (id)
                )
            """)

    def populate_plant_data(self):
        """
        Populate database with default plant data if empty.

        Includes a comprehensive set of common garden plants with complete
        growing information, companion planting data, and care instructions.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM plants")
            if cursor.fetchone()[0] > 0:
                return  # Skip if plants already exist

            # Pre-defined plant data with comprehensive growing information
            plants_data = [
                # Spring vegetables - cool season crops
                (
                    "Lettuce",
                    "Lactuca sativa",
                    "vegetable",
                    "spring",
                    "seed",
                    7,
                    60,
                    6,
                    "partial_shade",
                    "medium",
                    json.dumps(["carrots", "radishes", "onions"]),
                    json.dumps(["broccoli"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Cool weather crop, plant 2 weeks before last frost",
                ),
                (
                    "Spinach",
                    "Spinacia oleracea",
                    "vegetable",
                    "spring",
                    "seed",
                    7,
                    45,
                    4,
                    "partial_shade",
                    "medium",
                    json.dumps(["lettuce", "peas", "radishes"]),
                    json.dumps(["fennel"]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8, 9]),
                    "Bolts in hot weather, successive plantings every 2 weeks",
                ),
                (
                    "Peas",
                    "Pisum sativum",
                    "vegetable",
                    "spring",
                    "seed",
                    10,
                    70,
                    3,
                    "full_sun",
                    "medium",
                    json.dumps(["carrots", "radishes", "lettuce"]),
                    json.dumps(["onions", "garlic"]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8]),
                    "Plant as soon as soil can be worked, nitrogen fixer",
                ),
                (
                    "Radishes",
                    "Raphanus sativus",
                    "vegetable",
                    "spring",
                    "seed",
                    4,
                    30,
                    2,
                    "full_sun",
                    "medium",
                    json.dumps(["lettuce", "spinach", "carrots"]),
                    json.dumps(["hyssop"]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8, 9]),
                    "Fast growing, helps break up soil for root vegetables",
                ),
                # Summer vegetables - warm season crops
                (
                    "Tomatoes",
                    "Solanum lycopersicum",
                    "vegetable",
                    "summer",
                    "transplant",
                    7,
                    80,
                    18,
                    "full_sun",
                    "high",
                    json.dumps(["basil", "peppers", "marigolds"]),
                    json.dumps(["fennel", "brassicas"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9, 10]),
                    "Plant after last frost, stake or cage for support",
                ),
                (
                    "Peppers",
                    "Capsicum annuum",
                    "vegetable",
                    "summer",
                    "transplant",
                    10,
                    70,
                    12,
                    "full_sun",
                    "medium",
                    json.dumps(["tomatoes", "basil", "onions"]),
                    json.dumps(["fennel"]),
                    json.dumps([4, 5, 6, 7, 8, 9, 10]),
                    "Heat-loving crop, harvest when fully colored",
                ),
                (
                    "Cucumbers",
                    "Cucumis sativus",
                    "vegetable",
                    "summer",
                    "seed",
                    7,
                    60,
                    12,
                    "full_sun",
                    "high",
                    json.dumps(["beans", "corn", "radishes"]),
                    json.dumps(["aromatic herbs"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Provide trellis for vertical growth",
                ),
                (
                    "Zucchini",
                    "Cucurbita pepo",
                    "vegetable",
                    "summer",
                    "seed",
                    7,
                    50,
                    24,
                    "full_sun",
                    "high",
                    json.dumps(["beans", "corn", "nasturtiums"]),
                    json.dumps(["potatoes"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Very productive, harvest when 6-8 inches long",
                ),
                (
                    "Green Beans",
                    "Phaseolus vulgaris",
                    "vegetable",
                    "summer",
                    "seed",
                    8,
                    60,
                    6,
                    "full_sun",
                    "medium",
                    json.dumps(["corn", "cucumbers", "tomatoes"]),
                    json.dumps(["onions", "garlic"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Bush varieties don't need support, nitrogen fixer",
                ),
                (
                    "Corn",
                    "Zea mays",
                    "vegetable",
                    "summer",
                    "seed",
                    7,
                    80,
                    12,
                    "full_sun",
                    "medium",
                    json.dumps(["beans", "squash", "cucumbers"]),
                    json.dumps(["tomatoes"]),
                    json.dumps([4, 5, 6, 7, 8, 9]),
                    "Plant in blocks for better pollination",
                ),
                # Fall vegetables - cool season crops for autumn planting
                (
                    "Broccoli",
                    "Brassica oleracea",
                    "vegetable",
                    "fall",
                    "transplant",
                    7,
                    70,
                    12,
                    "full_sun",
                    "medium",
                    json.dumps(["onions", "lettuce", "carrots"]),
                    json.dumps(["tomatoes", "peppers"]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8]),
                    "Cool weather crop, harvest before flowers open",
                ),
                (
                    "Cauliflower",
                    "Brassica oleracea",
                    "vegetable",
                    "fall",
                    "transplant",
                    7,
                    75,
                    15,
                    "full_sun",
                    "medium",
                    json.dumps(["onions", "celery", "beans"]),
                    json.dumps(["tomatoes"]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8]),
                    "Blanch heads by tying leaves over developing curds",
                ),
                (
                    "Carrots",
                    "Daucus carota",
                    "vegetable",
                    "fall",
                    "seed",
                    14,
                    70,
                    2,
                    "full_sun",
                    "medium",
                    json.dumps(["onions", "leeks", "rosemary"]),
                    json.dumps(["dill"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Direct sow, thin seedlings to prevent crowding",
                ),
                (
                    "Kale",
                    "Brassica oleracea",
                    "vegetable",
                    "fall",
                    "seed",
                    7,
                    60,
                    12,
                    "partial_shade",
                    "medium",
                    json.dumps(["onions", "garlic", "nasturtiums"]),
                    json.dumps(["tomatoes"]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8, 9]),
                    "Frost improves flavor, harvest outer leaves first",
                ),
                # Culinary and medicinal herbs
                (
                    "Basil",
                    "Ocimum basilicum",
                    "herb",
                    "summer",
                    "transplant",
                    7,
                    60,
                    8,
                    "full_sun",
                    "medium",
                    json.dumps(["tomatoes", "peppers", "oregano"]),
                    json.dumps(["rue"]),
                    json.dumps([4, 5, 6, 7, 8, 9, 10]),
                    "Pinch flowers to keep leaves tender",
                ),
                (
                    "Oregano",
                    "Origanum vulgare",
                    "herb",
                    "spring",
                    "transplant",
                    7,
                    80,
                    10,
                    "full_sun",
                    "low",
                    json.dumps(["tomatoes", "peppers", "basil"]),
                    json.dumps([]),
                    json.dumps([4, 5, 6, 7, 8, 9]),
                    "Perennial herb, drought tolerant once established",
                ),
                (
                    "Thyme",
                    "Thymus vulgaris",
                    "herb",
                    "spring",
                    "transplant",
                    14,
                    90,
                    8,
                    "full_sun",
                    "low",
                    json.dumps(["rosemary", "sage", "lavender"]),
                    json.dumps([]),
                    json.dumps([4, 5, 6, 7, 8, 9]),
                    "Perennial, excellent ground cover",
                ),
                (
                    "Rosemary",
                    "Rosmarinus officinalis",
                    "herb",
                    "spring",
                    "transplant",
                    21,
                    120,
                    18,
                    "full_sun",
                    "low",
                    json.dumps(["thyme", "sage", "carrots"]),
                    json.dumps([]),
                    json.dumps([6, 7, 8, 9, 10]),
                    "Perennial evergreen, drought tolerant",
                ),
                # Fruit plants and berry bushes
                (
                    "Strawberries",
                    "Fragaria × ananassa",
                    "fruit",
                    "spring",
                    "transplant",
                    0,
                    60,
                    12,
                    "full_sun",
                    "medium",
                    json.dumps(["thyme", "borage", "lettuce"]),
                    json.dumps(["brassicas"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Perennial, remove runners for larger berries",
                ),
                (
                    "Blueberries",
                    "Vaccinium corymbosum",
                    "fruit",
                    "spring",
                    "transplant",
                    0,
                    730,
                    48,
                    "full_sun",
                    "high",
                    json.dumps(["azaleas", "rhododendrons"]),
                    json.dumps([]),
                    json.dumps([3, 4, 5, 6, 7, 8]),
                    "Perennial shrub, needs acidic soil",
                ),
                # Winter vegetables - hardy crops for cold season
                (
                    "Winter Kale",
                    "Brassica oleracea",
                    "vegetable",
                    "winter",
                    "transplant",
                    7,
                    65,
                    12,
                    "full_sun",
                    "medium",
                    json.dumps(["onions", "garlic", "beets"]),
                    json.dumps(["tomatoes", "peppers"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Extremely cold hardy, harvest all winter",
                ),
                (
                    "Brussels Sprouts",
                    "Brassica oleracea",
                    "vegetable",
                    "winter",
                    "transplant",
                    7,
                    90,
                    18,
                    "full_sun",
                    "medium",
                    json.dumps(["thyme", "sage", "carrots"]),
                    json.dumps(["strawberries"]),
                    json.dumps([3, 4, 5, 6, 7, 8]),
                    "Frost improves flavor, harvest from bottom up",
                ),
                (
                    "Leeks",
                    "Allium ampeloprasum",
                    "vegetable",
                    "winter",
                    "transplant",
                    14,
                    120,
                    6,
                    "full_sun",
                    "medium",
                    json.dumps(["carrots", "celery", "onions"]),
                    json.dumps(["beans", "peas"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Cold hardy, hill soil around stems for blanching",
                ),
                (
                    "Garlic",
                    "Allium sativum",
                    "vegetable",
                    "winter",
                    "bulb",
                    0,
                    240,
                    4,
                    "full_sun",
                    "low",
                    json.dumps(["tomatoes", "roses", "lettuce"]),
                    json.dumps(["peas", "beans"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Plant in fall, harvest next summer, natural pest repellent",
                ),
                (
                    "Winter Lettuce",
                    "Lactuca sativa",
                    "vegetable",
                    "winter",
                    "seed",
                    7,
                    50,
                    6,
                    "partial_shade",
                    "medium",
                    json.dumps(["carrots", "radishes", "beets"]),
                    json.dumps(["broccoli"]),
                    json.dumps([4, 5, 6, 7, 8, 9]),
                    "Choose cold-hardy varieties, use row covers",
                ),
                # Additional summer crops
                (
                    "Eggplant",
                    "Solanum melongena",
                    "vegetable",
                    "summer",
                    "transplant",
                    10,
                    80,
                    18,
                    "full_sun",
                    "medium",
                    json.dumps(["beans", "peppers", "thyme"]),
                    json.dumps(["fennel"]),
                    json.dumps([5, 6, 7, 8, 9, 10]),
                    "Heat-loving crop, stake for support",
                ),
                (
                    "Watermelon",
                    "Citrullus lanatus",
                    "fruit",
                    "summer",
                    "seed",
                    7,
                    90,
                    36,
                    "full_sun",
                    "high",
                    json.dumps(["corn", "beans", "radishes"]),
                    json.dumps(["cucumbers"]),
                    json.dumps([4, 5, 6, 7, 8, 9, 10]),
                    "Needs lots of space, tap for ripeness check",
                ),
                (
                    "Cantaloupe",
                    "Cucumis melo",
                    "fruit",
                    "summer",
                    "seed",
                    7,
                    80,
                    24,
                    "full_sun",
                    "medium",
                    json.dumps(["corn", "beans", "radishes"]),
                    json.dumps(["potatoes"]),
                    json.dumps([4, 5, 6, 7, 8, 9, 10]),
                    "Sweet melon, sniff stem end for ripeness",
                ),
                (
                    "Okra",
                    "Abelmoschus esculentus",
                    "vegetable",
                    "summer",
                    "seed",
                    7,
                    60,
                    12,
                    "full_sun",
                    "medium",
                    json.dumps(["peppers", "eggplant", "basil"]),
                    json.dumps([]),
                    json.dumps([5, 6, 7, 8, 9, 10, 11]),
                    "Very heat tolerant, harvest young pods",
                ),
                # Additional spring crops
                (
                    "Arugula",
                    "Eruca vesicaria",
                    "vegetable",
                    "spring",
                    "seed",
                    5,
                    40,
                    4,
                    "partial_shade",
                    "medium",
                    json.dumps(["lettuce", "carrots", "beets"]),
                    json.dumps([]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8, 9]),
                    "Fast growing, peppery flavor, bolts in heat",
                ),
                (
                    "Swiss Chard",
                    "Beta vulgaris",
                    "vegetable",
                    "spring",
                    "seed",
                    7,
                    60,
                    8,
                    "partial_shade",
                    "medium",
                    json.dumps(["beans", "onions", "brassicas"]),
                    json.dumps([]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Heat tolerant, colorful stems, harvest outer leaves",
                ),
                (
                    "Beets",
                    "Beta vulgaris",
                    "vegetable",
                    "spring",
                    "seed",
                    7,
                    60,
                    3,
                    "full_sun",
                    "medium",
                    json.dumps(["onions", "lettuce", "brassicas"]),
                    json.dumps(["pole beans"]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8, 9]),
                    "Both roots and greens edible, needs loose soil",
                ),
                # Additional fall crops
                (
                    "Turnips",
                    "Brassica rapa",
                    "vegetable",
                    "fall",
                    "seed",
                    7,
                    50,
                    4,
                    "full_sun",
                    "medium",
                    json.dumps(["peas", "beans", "onions"]),
                    json.dumps([]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8, 9]),
                    "Quick growing, both roots and greens edible",
                ),
                (
                    "Rutabaga",
                    "Brassica napus",
                    "vegetable",
                    "fall",
                    "seed",
                    7,
                    90,
                    6,
                    "full_sun",
                    "medium",
                    json.dumps(["peas", "onions", "beans"]),
                    json.dumps([]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Needs cool weather, stores well through winter",
                ),
                (
                    "Parsnips",
                    "Pastinaca sativa",
                    "vegetable",
                    "fall",
                    "seed",
                    14,
                    120,
                    4,
                    "full_sun",
                    "medium",
                    json.dumps(["peas", "beans", "peppers"]),
                    json.dumps([]),
                    json.dumps([2, 3, 4, 5, 6, 7, 8, 9]),
                    "Frost improves flavor, long growing season",
                ),
                # Additional herbs
                (
                    "Cilantro",
                    "Coriandrum sativum",
                    "herb",
                    "spring",
                    "seed",
                    7,
                    50,
                    6,
                    "partial_shade",
                    "medium",
                    json.dumps(["tomatoes", "peppers", "beans"]),
                    json.dumps(["fennel"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Cool weather herb, bolts quickly in heat",
                ),
                (
                    "Parsley",
                    "Petroselinum crispum",
                    "herb",
                    "spring",
                    "seed",
                    14,
                    80,
                    8,
                    "partial_shade",
                    "medium",
                    json.dumps(["tomatoes", "asparagus", "carrots"]),
                    json.dumps([]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Biennial herb, slow to germinate",
                ),
                (
                    "Dill",
                    "Anethum graveolens",
                    "herb",
                    "spring",
                    "seed",
                    7,
                    70,
                    8,
                    "full_sun",
                    "medium",
                    json.dumps(["lettuce", "onions", "cucumbers"]),
                    json.dumps(["carrots"]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Self-seeding annual, attracts beneficial insects",
                ),
                (
                    "Chives",
                    "Allium schoenoprasum",
                    "herb",
                    "spring",
                    "transplant",
                    10,
                    80,
                    6,
                    "partial_shade",
                    "low",
                    json.dumps(["carrots", "tomatoes", "roses"]),
                    json.dumps([]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9]),
                    "Perennial herb, edible flowers, pest deterrent",
                ),
                (
                    "Mint",
                    "Mentha",
                    "herb",
                    "spring",
                    "transplant",
                    7,
                    90,
                    18,
                    "partial_shade",
                    "high",
                    json.dumps(["brassicas", "tomatoes"]),
                    json.dumps([]),
                    json.dumps([3, 4, 5, 6, 7, 8, 9, 10]),
                    "Very invasive, grow in containers, aromatic leaves",
                ),
                (
                    "Sage",
                    "Salvia officinalis",
                    "herb",
                    "spring",
                    "transplant",
                    14,
                    100,
                    18,
                    "full_sun",
                    "low",
                    json.dumps(["rosemary", "thyme", "brassicas"]),
                    json.dumps(["cucumbers"]),
                    json.dumps([4, 5, 6, 7, 8, 9]),
                    "Perennial herb, drought tolerant, silvery leaves",
                ),
                # Additional fruits
                (
                    "Raspberries",
                    "Rubus idaeus",
                    "fruit",
                    "spring",
                    "transplant",
                    0,
                    365,
                    24,
                    "full_sun",
                    "medium",
                    json.dumps(["garlic", "tansy", "turnips"]),
                    json.dumps(["blackberries"]),
                    json.dumps([3, 4, 5, 6, 7, 8]),
                    "Perennial canes, needs support, summer and fall varieties",
                ),
                (
                    "Blackberries",
                    "Rubus fruticosus",
                    "fruit",
                    "spring",
                    "transplant",
                    0,
                    365,
                    36,
                    "full_sun",
                    "medium",
                    json.dumps(["tansy", "mint"]),
                    json.dumps(["raspberries"]),
                    json.dumps([4, 5, 6, 7, 8, 9]),
                    "Very vigorous, thorny varieties available, perennial",
                ),
                (
                    "Grapes",
                    "Vitis vinifera",
                    "fruit",
                    "spring",
                    "transplant",
                    0,
                    730,
                    96,
                    "full_sun",
                    "medium",
                    json.dumps(["basil", "oregano", "geraniums"]),
                    json.dumps([]),
                    json.dumps([4, 5, 6, 7, 8, 9]),
                    "Perennial vine, needs strong trellis, prune annually",
                ),
            ]

            for plant_data in plants_data:
                cursor.execute(
                    """
                    INSERT INTO plants (name, scientific_name, plant_type, season, planting_method,
                                      days_to_germination, days_to_maturity, spacing_inches,
                                      sun_requirements, water_needs, companion_plants, avoid_plants,
                                      climate_zones, care_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    plant_data,
                )

    def get_plants_by_season(self, season: str) -> List[Plant]:
        """
        Retrieve plants suitable for a specific planting season.

        Args:
            season: Season name (spring, summer, fall, winter)

        Returns:
            List[Plant]: Plants suitable for the specified season
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plants WHERE season = ?", (season,))
            return [self._row_to_plant(row) for row in cursor.fetchall()]

    def get_plants_by_type(self, plant_type: str) -> List[Plant]:
        """
        Retrieve plants of a specific type.

        Args:
            plant_type: Type of plant (vegetable, fruit, herb)

        Returns:
            List[Plant]: Plants of the specified type
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plants WHERE plant_type = ?", (plant_type,))
            return [self._row_to_plant(row) for row in cursor.fetchall()]

    def search_plants(self, query: str) -> List[Plant]:
        """
        Search plants by name or scientific name.

        Args:
            query: Search term to match against plant names

        Returns:
            List[Plant]: Plants matching the search query
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM plants WHERE name LIKE ? OR scientific_name LIKE ?",
                (f"%{query}%", f"%{query}%"),
            )
            return [self._row_to_plant(row) for row in cursor.fetchall()]

    def add_custom_plant(
        self,
        name: str,
        scientific_name: str,
        plant_type: str,
        season: str,
        planting_method: str,
        days_to_germination: int,
        days_to_maturity: int,
        spacing_inches: int,
        sun_requirements: str,
        water_needs: str,
        companion_plants: List[str],
        avoid_plants: List[str],
        climate_zones: List[int],
        care_notes: str,
    ) -> Optional[int]:
        """
        Add a custom plant to the database.

        Args:
            name: Common name of the plant
            scientific_name: Scientific/botanical name
            plant_type: Category (vegetable, fruit, herb)
            season: Optimal planting season (spring, summer, fall, winter)
            planting_method: How to plant (seed, transplant, bulb)
            days_to_germination: Days from planting to germination
            days_to_maturity: Days from planting to harvest
            spacing_inches: Required spacing between plants in inches
            sun_requirements: Light needs (full_sun, partial_shade, shade)
            water_needs: Water requirements (low, medium, high)
            companion_plants: List of beneficial companion plants
            avoid_plants: List of plants to avoid growing nearby
            climate_zones: List of suitable USDA hardiness zones
            care_notes: Additional care instructions and tips

        Returns:
            int: ID of the newly created plant

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not name:
            raise ValueError("Plant name is required")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO plants (name, scientific_name, plant_type, season, planting_method,
                                  days_to_germination, days_to_maturity, spacing_inches,
                                  sun_requirements, water_needs, companion_plants, avoid_plants,
                                  climate_zones, care_notes, is_custom)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            """,
                (
                    name,
                    scientific_name,
                    plant_type,
                    season,
                    planting_method,
                    days_to_germination,
                    days_to_maturity,
                    spacing_inches,
                    sun_requirements,
                    water_needs,
                    json.dumps(companion_plants),
                    json.dumps(avoid_plants),
                    json.dumps(climate_zones),
                    care_notes,
                ),
            )

            plant_id = cursor.lastrowid
            conn.commit()
            return plant_id

    def _row_to_plant(self, row) -> Plant:
        """Convert a database row to a Plant object.

        Args:
            row: Database row containing plant data

        Returns:
            Plant: Constructed Plant object

        Raises:
            ValueError: If row data is invalid or missing required fields
        """
        if not row or len(row) < 15:  # Check minimum required fields
            raise ValueError("Invalid row data for plant conversion")

        try:
            return Plant(
                id=row[0],
                name=row[1],
                scientific_name=row[2],
                plant_type=row[3],
                season=row[4],
                planting_method=row[5],
                days_to_germination=row[6],
                days_to_maturity=row[7],
                spacing_inches=row[8],
                sun_requirements=row[9],
                water_needs=row[10],
                companion_plants=json.loads(row[11]) if row[11] else [],
                avoid_plants=json.loads(row[12]) if row[12] else [],
                climate_zones=json.loads(row[13]) if row[13] else [],
                care_notes=row[14],
                is_custom=bool(row[15]) if len(row) > 15 else False,
            )
        except (IndexError, json.JSONDecodeError) as e:
            raise ValueError(f"Error converting row to plant: {str(e)}") from e

    def get_plant_by_id(self, plant_id: int) -> Optional[Plant]:
        """
        Retrieve a specific plant by its ID.

        Args:
            plant_id: Unique identifier of the plant

        Returns:
            Optional[Plant]: The plant if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM plants WHERE id = ?", (plant_id,))
            row = cursor.fetchone()
            return self._row_to_plant(row) if row else None
