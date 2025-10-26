# Planted API Reference

This document provides an overview of the main modules and their key functions in the Planted application.

## Core Modules

### garden_manager.database

#### plant_data.py - PlantDatabase

Manages the plant catalog with detailed growing information.

```python
from garden_manager.database.plant_data import PlantDatabase

db = PlantDatabase()

# Get all plants
plants = db.get_all_plants()

# Get plants by type
vegetables = db.get_plants_by_type("Vegetable")

# Get plants suitable for current season and location
seasonal = db.get_seasonal_recommendations(season="Spring", zone=7)

# Get companion planting suggestions
companions = db.get_companion_plants("Tomato")

# Search plants
results = db.search_plants("tom")  # Finds Tomato
```

#### garden_db.py - GardenDatabase

Manages garden plots, planted items, and care tasks.

```python
from garden_manager.database.garden_db import GardenDatabase

db = GardenDatabase()

# Create a garden plot
plot_id = db.create_garden_plot(
    name="Main Garden",
    width=4,
    height=4,
    location="Backyard"
)

# Get all plots
plots = db.get_all_plots()

# Add a plant to a plot
planted_id = db.add_plant_to_plot(
    plot_id=plot_id,
    plant_name="Tomato",
    grid_x=0,
    grid_y=0,
    quantity=1
)

# Get care tasks
tasks = db.get_care_tasks(overdue_only=False)

# Complete a task
db.complete_task(task_id)
```

#### models.py - Data Models

Dataclass definitions for all application data structures.

**Key Models:**
- `PlantSpec` - Basic plant information
- `PlantGrowingInfo` - Growing requirements
- `PlantCareRequirements` - Care schedules
- `PlantCompatibility` - Companion planting data
- `GardenPlot` - Garden plot information
- `PlantedItem` - Items planted in plots
- `CareTask` - Care reminders and tasks

### garden_manager.services

#### weather_service.py - WeatherService

Integrates with OpenWeatherMap API for weather data.

```python
from garden_manager.services.weather_service import WeatherService

service = WeatherService(api_key="your_key")

# Get current weather
weather = service.get_current_weather(lat=40.7128, lon=-74.0060)
# Returns: temperature, conditions, humidity, etc.

# Get watering recommendation based on weather
should_water = service.should_water_today(weather)
```

#### location_service.py - LocationService

Determines user location and climate zone.

```python
from garden_manager.services.location_service import LocationService

service = LocationService()

# Get location from IP
location = service.get_location()
# Returns: city, region, country, lat, lon

# Calculate hardiness zone
zone = service.get_hardiness_zone(lat=40.7128)
```

#### scheduler.py - CareReminder

Generates automated care task schedules.

```python
from garden_manager.services.scheduler import CareReminder

scheduler = CareReminder(garden_db)

# Generate care tasks for a planted item
scheduler.schedule_care_tasks(
    planted_item_id=1,
    plant_care=plant_care_requirements
)

# Check for overdue tasks
overdue = scheduler.get_overdue_tasks()
```

### garden_manager.utils

#### date_utils.py - SeasonCalculator

Handles season calculations and date operations.

```python
from garden_manager.utils.date_utils import SeasonCalculator
from datetime import datetime

calc = SeasonCalculator()

# Get current season
season = calc.get_current_season()

# Check if date is in season
is_spring = calc.is_season(datetime.now(), "Spring")

# Get season for specific date
season = calc.get_season_for_date(datetime(2024, 6, 15))
```

#### plant_utils.py - Plant Utilities

Helper functions for plant care calculations.

```python
from garden_manager.utils.plant_utils import (
    calculate_harvest_date,
    calculate_watering_frequency,
    get_plant_spacing_recommendations
)

# Calculate expected harvest date
harvest_date = calculate_harvest_date(
    planting_date=datetime.now(),
    days_to_maturity=65
)

# Get watering frequency based on requirements
frequency = calculate_watering_frequency(
    water_requirements="Moderate",
    temperature=75,
    humidity=60
)

# Calculate plants per square foot
spacing = get_plant_spacing_recommendations(
    spacing_inches=24,
    grid_size=12
)
```

## Flask Routes (app.py)

### Main Routes

```python
@app.route('/')
def home()
    """Dashboard - Main overview page"""

@app.route('/plants')
def plants()
    """Browse all plants with filtering"""

@app.route('/plants/<plant_name>')
def plant_detail(plant_name)
    """Detailed information for a specific plant"""

@app.route('/garden')
def garden()
    """View all garden plots"""

@app.route('/garden/create', methods=['GET', 'POST'])
def create_plot()
    """Create a new garden plot"""

@app.route('/garden/plot/<int:plot_id>')
def view_plot(plot_id)
    """View specific plot with planted items"""

@app.route('/care')
def care()
    """View care schedule and tasks"""

@app.route('/weather')
def weather()
    """Weather information and recommendations"""
```

### API Endpoints

```python
@app.route('/api/plots', methods=['GET'])
def api_get_plots()
    """Get all garden plots as JSON"""

@app.route('/api/plants/search', methods=['GET'])
def api_search_plants()
    """Search plants by name"""

@app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
def api_complete_task(task_id)
    """Mark a care task as complete"""
```

## Database Schema

### Tables

#### plants
- Plant catalog information
- Growing requirements
- Companion planting data

#### garden_plots
- id, name, width, height, location
- created_at

#### planted_items
- id, plot_id, plant_name
- grid_x, grid_y, quantity
- date_planted
- expected_harvest_date

#### care_tasks
- id, planted_item_id
- task_type (watering, fertilizing, harvesting)
- due_date, completed_at
- notes

## Configuration

### Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Weather API
api_key = os.getenv('OPENWEATHERMAP_API_KEY')

# Flask secret key
secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key')
```

## Error Handling

```python
try:
    db.create_garden_plot(name="Test", width=-1, height=4, location="Test")
except ValueError as e:
    print(f"Validation error: {e}")

try:
    weather = weather_service.get_current_weather(40.7, -74.0)
except requests.RequestException as e:
    print(f"Weather API error: {e}")
    # Fall back to mock data
```

## Testing

```python
import pytest
from garden_manager.database.garden_db import GardenDatabase

def test_create_plot():
    db = GardenDatabase(":memory:")  # In-memory database for testing
    plot_id = db.create_garden_plot("Test", 4, 4, "Test Location")
    assert plot_id > 0
    
    plots = db.get_all_plots()
    assert len(plots) == 1
    assert plots[0].name == "Test"
```

## Common Patterns

### Adding a New Plant

```python
# 1. Add to default_plants_data.py
plant_data = {
    "name": "Basil",
    "plant_type": "Herb",
    "scientific_name": "Ocimum basilicum",
    # ... more fields
}

# 2. The database will automatically load it on initialization
```

### Creating a Custom Care Schedule

```python
from garden_manager.services.scheduler import CareReminder
from garden_manager.database.models import PlantCareRequirements

care_reqs = PlantCareRequirements(
    watering_frequency_days=3,
    fertilizing_frequency_days=14,
    harvest_window_days=7
)

scheduler = CareReminder(garden_db)
scheduler.schedule_care_tasks(planted_item_id, care_reqs)
```

## Extending Planted

### Adding a New Service

```python
# garden_manager/services/my_service.py

class MyService:
    """New service for additional functionality."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
    
    def do_something(self):
        """Implement your service logic."""
        pass

# Then import and use in app.py
from garden_manager.services.my_service import MyService
my_service = MyService()
```

### Adding a New Route

```python
# In app.py

@app.route('/my-feature')
def my_feature():
    """New feature route."""
    data = my_service.get_data()
    return render_template('my_feature.html', data=data)
```

### Adding Tests

```python
# tests/unit/test_my_feature.py

def test_my_feature():
    """Test my new feature."""
    result = my_service.do_something()
    assert result is not None
```

## Performance Tips

1. **Database Queries**: Use appropriate indexes
   ```python
   cursor.execute("CREATE INDEX IF NOT EXISTS idx_plot_id ON planted_items(plot_id)")
   ```

2. **Caching**: Cache weather data to reduce API calls
   ```python
   @lru_cache(maxsize=100)
   def get_weather(lat, lon):
       return weather_service.get_current_weather(lat, lon)
   ```

3. **Batch Operations**: Process multiple items together
   ```python
   with connection:  # Transaction
       for plant in plants:
           db.add_plant_to_plot(...)
   ```

## Further Reading

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [OpenWeatherMap API](https://openweathermap.org/api)

---

For questions or contributions, see [CONTRIBUTING.md](../CONTRIBUTING.md).
