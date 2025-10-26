# Planted - Garden Management System

A comprehensive Python web application for managing your garden. This browser-based application helps you plan, plant, and maintain your garden with seasonal recommendations, weather integration, and automated care scheduling.

## 🌱 Features

### Plant Database & Recommendations

- **38 Plants**: Vegetables, herbs, and fruits with detailed growing information from reliable sources
- **Seasonal Recommendations**: Location and climate zone-based plant suggestions
- **Companion Planting**: Smart recommendations for plant compatibility
- **Growing Guides**: Days to germination, maturity, spacing, and care notes
- **Verified Data**: All plant information sourced from USDA, university extensions, and reputable horticultural organizations

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

1. **Clone or download this repository**

2. **Configure environment (for real weather data):**

   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env and add your OpenWeatherMap API key
   # Get a free API key at: https://openweathermap.org/api
   ```

   > **Note:** The app works without an API key using mock weather data. See [SETUP.md](SETUP.md) for detailed instructions.

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**

   **On Windows:**
   ```bash
   run.bat
   ```

   **On macOS/Linux:**
   ```bash
   ./run.sh
   # or
   python3 main.py
   ```

The application will automatically open in your default browser at `http://localhost:5000`.

> **Note:** The startup scripts (`run.bat` and `run.sh`) automatically check for dependencies and provide helpful error messages if anything is missing.

## 🚀 Quick Start

1. **Launch the App**: Run `python3 main.py`
2. **Browser Opens**: App loads automatically in your browser
3. **Browse Plants**: Click "Browse Plants" to see seasonal recommendations
4. **Create a Garden**: Go to "Garden Layout" and create your first plot
5. **Care Schedule**: Check "Care Schedule" for automated reminders

## 🌐 Web Interface

The application features a responsive web design with:

- **Green Color Scheme**: Earth tones and natural colors
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

The database includes 38 plants with scientifically verified growing information:

### Vegetables (21 plants)

- **Spring**: Lettuce, Spinach, Peas, Radishes, Onions, Beets, Swiss Chard, Arugula
- **Summer**: Tomatoes, Peppers, Cucumbers, Zucchini, Green Beans, Corn, Eggplant, Pumpkin, Watermelon, Cantaloupe
- **Fall**: Broccoli, Cauliflower, Carrots, Kale, Garlic

### Herbs (10 plants)

- Basil, Oregano, Thyme, Rosemary, Parsley, Cilantro, Mint, Dill, Chives, Sage

### Fruits (7 plants)

- Strawberries, Blueberries, Raspberries, Blackberries, Grapes, Watermelon, Cantaloupe

Each plant includes complete growing information, companion planting guides, and care schedules. All data is sourced from reliable authorities including USDA, university extension programs, and established horticultural organizations. See [Plant Data Sources](docs/plant_data_sources.md) for detailed information about our data sources.

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

The web interface follows clean design principles:

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

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed information on:
- Development workflow
- Code style guidelines
- Testing requirements
- How to add new plants

## 📚 Documentation

- [Setup Guide](SETUP.md) - Detailed installation and configuration
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [Plant Data Sources](docs/plant_data_sources.md) - Information about plant database sources
- [Architecture Documentation](docs/architecture.md) - System design and structure
- [Deployment Guide](docs/deployment.md) - How to deploy to the web
- [Changelog](CHANGELOG.md) - Version history and updates

## 📋 Project Structure

See [Architecture Documentation](docs/architecture.md) for detailed information about the codebase structure and design decisions.

## 🚀 Deployment

Ready to host Planted on the web? Check out our [Deployment Guide](docs/deployment.md) for instructions on deploying to various platforms including Heroku, PythonAnywhere, and your own server.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Happy Gardening! 🌱**

*Now accessible from any device with a web browser!*
