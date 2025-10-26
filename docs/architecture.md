# Planted Architecture

## Overview

Planted is a Flask-based web application following a modular architecture pattern that separates concerns into distinct layers.

## Directory Structure

```
Planted/
├── app.py                    # Flask application configuration and routes
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Modern Python project configuration
├── garden_manager/          # Main application package
│   ├── database/            # Data layer
│   │   ├── models.py        # Data models and schemas
│   │   ├── plant_data.py    # Plant database management
│   │   ├── garden_db.py     # Garden database operations
│   │   ├── default_plants_data.py  # Default plant data
│   │   └── seeds/           # Seed data (JSON)
│   ├── services/            # Business logic layer
│   │   ├── weather_service.py   # Weather API integration
│   │   ├── location_service.py  # Location detection
│   │   └── scheduler.py         # Care task scheduling
│   ├── utils/               # Utility functions
│   │   ├── date_utils.py    # Date and season calculations
│   │   └── plant_utils.py   # Plant-related utilities
│   └── web/                 # Web presentation layer
│       ├── templates/       # HTML templates (Jinja2)
│       └── static/          # CSS, JavaScript, images
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
└── docs/                   # Documentation
```

## Architectural Layers

### 1. Presentation Layer (Web)
- **Location**: `garden_manager/web/`
- **Purpose**: User interface and HTTP handling
- **Technology**: Flask, Jinja2 templates, HTML/CSS/JavaScript
- **Responsibilities**:
  - Render HTML templates
  - Handle HTTP requests/responses
  - Serve static assets
  - Client-side interactivity

### 2. Business Logic Layer (Services)
- **Location**: `garden_manager/services/`
- **Purpose**: Core application logic and external integrations
- **Components**:
  - **WeatherService**: Integrates with OpenWeatherMap API
  - **LocationService**: IP-based geolocation
  - **Scheduler**: Automated care task generation
- **Responsibilities**:
  - External API integration
  - Business rule implementation
  - Task scheduling logic

### 3. Data Layer (Database)
- **Location**: `garden_manager/database/`
- **Purpose**: Data persistence and retrieval
- **Technology**: SQLite
- **Components**:
  - **Models**: Data schemas (dataclasses)
  - **PlantDatabase**: Plant catalog management
  - **GardenDatabase**: Garden plot and care task CRUD
- **Responsibilities**:
  - Database schema management
  - CRUD operations
  - Data validation
  - Default data seeding

### 4. Utility Layer (Utils)
- **Location**: `garden_manager/utils/`
- **Purpose**: Shared helper functions
- **Components**:
  - **date_utils**: Season calculations, date formatting
  - **plant_utils**: Plant care calculations
- **Responsibilities**:
  - Common calculations
  - Date/time utilities
  - Formatting functions

## Data Flow

```
User Request
    ↓
Flask Route (app.py)
    ↓
Service Layer (business logic)
    ↓
Database Layer (data operations)
    ↓
Service Layer (data processing)
    ↓
Template Rendering (Jinja2)
    ↓
HTTP Response
```

## Key Design Patterns

### 1. Repository Pattern
- Database classes encapsulate all data access
- Services don't interact directly with SQLite
- Enables easy database switching in the future

### 2. Service Layer Pattern
- Business logic separated from presentation and data layers
- Services are reusable across different interfaces
- Easy to test in isolation

### 3. Dependency Injection
- Services receive their dependencies (e.g., API keys via environment variables)
- Makes testing easier with mocks
- Reduces coupling between components

## Database Schema

### Plants
- Comprehensive plant information
- Growing requirements and schedules
- Companion planting data

### Garden Plots
- User-created garden layouts
- Grid-based square-foot gardening system
- Position tracking for planted items

### Planted Items
- Tracks what's planted where
- Planting dates and timelines
- Links plots to plants

### Care Tasks
- Automated task generation
- Completion tracking
- Due date management

## External Dependencies

### Required
- **Flask**: Web framework
- **SQLite**: Database (built into Python)
- **python-dotenv**: Environment variable management
- **requests**: HTTP client for API calls

### Optional
- **OpenWeatherMap API**: Real weather data
  - Falls back to mock data if unavailable

## Cross-Platform Considerations

### Path Handling
- Uses `os.path.join()` and `pathlib.Path` for cross-platform path construction
- No hardcoded path separators (/ or \\)

### File Encoding
- All Python files use UTF-8 encoding
- Cross-platform text file handling

### Execution
- Shebang lines use `#!/usr/bin/env python3` for Unix-like systems
- Batch/shell scripts provided for Windows and Unix

## Security Considerations

### Environment Variables
- Sensitive data (API keys) stored in `.env`
- `.env` excluded from version control
- `.env.example` provided as template

### Database
- SQLite files excluded from version control
- No SQL injection vulnerabilities (parameterized queries)

### Flask Secret Key
- Configurable via environment variable
- Default key for development only

## Future Architecture Considerations

### Scalability
- Current: Single-user, local SQLite
- Future: Multi-user with PostgreSQL/MySQL
- Future: RESTful API for mobile apps

### Testing
- Test infrastructure established
- Need comprehensive test coverage
- CI/CD pipeline in place (GitHub Actions)

### Documentation
- API documentation using Sphinx (planned)
- Inline code documentation (docstrings)
- User guides (planned)

## Technology Choices

### Why Flask?
- Lightweight and flexible
- Easy to learn and use
- Excellent for small to medium applications
- Large ecosystem of extensions

### Why SQLite?
- Zero configuration
- Cross-platform
- Sufficient for single-user application
- Easy to upgrade to client-server database

### Why Jinja2?
- Integrated with Flask
- Powerful template inheritance
- Familiar syntax
- Secure by default (auto-escaping)

## Performance Considerations

- SQLite is fast enough for expected load
- Static assets served directly by Flask (dev) or web server (production)
- Database queries optimized with proper indexing
- Caching strategy for weather data (reduce API calls)

## Maintainability

- Modular architecture allows independent component updates
- Clear separation of concerns
- Comprehensive documentation
- Type hints for better IDE support
- Linting with Pylint for code quality
