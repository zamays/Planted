# Garden Manager - GrowIt Style (Web Version)

A comprehensive Python web application inspired by the popular GrowIt mobile app. This browser-based application helps you plan, plant, and maintain your garden with seasonal recommendations, weather integration, and automated care scheduling.

## 🌱 Features

### Plant Database & Recommendations

- **20+ Plants**: Vegetables, herbs, and fruits with detailed growing information
- **Seasonal Recommendations**: Location and climate zone-based plant suggestions
- **Companion Planting**: Smart recommendations for plant compatibility
- **Growing Guides**: Days to germination, maturity, spacing, and care notes

### Garden Planning & Layout

- **Square-Foot Gardening**: Visual grid-based garden plot planning
- **Multiple Plots**: Create and manage multiple garden areas
- **Plant Tracking**: Track what's planted where and when

### Care Management

- **Automated Scheduling**: Smart watering, fertilizing, and harvest reminders
- **Weather Integration**: Location-based weather recommendations
- **Task Management**: Track completed and overdue care tasks

### Smart Recommendations

- **Climate Zone Integration**: Recommendations based on your specific zone
- **Seasonal Guidance**: Know what to plant when in your location
- **Weather-Aware Care**: Adjust watering based on current conditions

## 📦 Installation

### Requirements

- Python 3.9 or higher
- pip (Python package manager)

### Setup

1. Clone or download this repository
2. Install dependencies:

   ```bash
   pip install flask requests
   ```

3. Run the application:

   ```bash
   python3 main.py
   ```

The application will automatically open in your default browser at `http://localhost:5000`.

## 🚀 Quick Start

1. **Launch the App**: Run `python3 main.py`
2. **Browser Opens**: App loads automatically in your browser
3. **Browse Plants**: Click "Browse Plants" to see seasonal recommendations
4. **Create a Garden**: Go to "Garden Layout" and create your first plot
5. **Care Schedule**: Check "Care Schedule" for automated reminders

## 🌐 Web Interface

The application features a responsive web design with:

- **Green Color Scheme**: GrowIt-inspired earth tones and natural colors
- **Mobile-Friendly**: Works on desktop, tablet, and mobile devices
- **Intuitive Navigation**: Clean sidebar navigation
- **Weather Integration**: Current conditions and recommendations
- **Interactive Features**: Click to complete tasks, view plant details

## 🗂️ Application Structure

```bash
garden_manager/
├── database/          # SQLite database management
│   ├── plant_data.py     # 20+ plant database
│   ├── garden_db.py      # Garden plots and care tasks
│   └── models.py         # Data models
├── services/          # External integrations
│   ├── weather_service.py    # Weather API integration
│   ├── location_service.py   # Location detection
│   └── scheduler.py          # Task scheduling
├── utils/             # Utility functions
│   ├── date_utils.py         # Season calculations
│   └── plant_utils.py        # Plant care calculations
└── web/               # Flask web application
    ├── app.py                # Main Flask application
    └── templates/            # HTML templates
```

## 🌿 Available Plants

### Vegetables

- **Spring**: Lettuce, Spinach, Peas, Radishes
- **Summer**: Tomatoes, Peppers, Cucumbers, Zucchini, Green Beans, Corn
- **Fall**: Broccoli, Cauliflower, Carrots, Kale

### Herbs

- Basil, Oregano, Thyme, Rosemary

### Fruits

- Strawberries, Blueberries

Each plant includes complete growing information, companion planting guides, and care schedules.

## 🌦️ Weather Integration

- **Automatic Location Detection**: Uses IP geolocation
- **Climate Zone Calculation**: Determines your hardiness zone
- **Weather-Based Care**: Adjusts recommendations based on conditions
- **Offline Mode**: Works with default location if network unavailable

## 📅 Care Scheduling

Automated reminders for:

- **Watering**: Based on plant needs and weather
- **Fertilizing**: Timed nutrient applications
- **Harvesting**: Optimal harvest timing
- **Maintenance**: Pruning and general care

## 🎨 Design

The web interface follows GrowIt's design principles:

- **Natural Colors**: Greens, earth tones, organic palette
- **Card-Based Layout**: Clean, modern information display
- **Responsive Design**: Works on all screen sizes
- **Accessible**: Keyboard navigation and screen reader friendly

## 🔧 Customization

### Weather API

To use real weather data instead of mock data:

1. Get a free OpenWeatherMap API key
2. Edit `services/weather_service.py`
3. Replace `demo_key` with your actual API key

### Adding Plants

To add more plants:

1. Edit `database/plant_data.py`
2. Add plant data to the `plants_data` list
3. Restart the application

## 🌟 Advantages of Web Version

- **Cross-Platform**: Works on any device with a browser
- **No Installation Issues**: No GUI framework dependencies
- **Mobile Friendly**: Responsive design works on phones/tablets
- **Easy Updates**: Refresh browser to see changes
- **Shareable**: Can be accessed by multiple users on same network

## 🚀 Running the App

```bash
# Install dependencies
pip install flask requests

# Start the application
python3 main.py

# App opens automatically in browser at:
# http://localhost:5000
```

## 🤝 Contributing

Feel free to enhance the application:

- Add more plants to the database
- Improve the web interface design
- Add new features (pest tracking, harvest logging, etc.)
- Optimize performance

---

**Happy Gardening! 🌱**

*Now accessible from any device with a web browser!*
