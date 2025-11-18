# GitHub Copilot Instructions for Planted

## Project Overview

Planted is a comprehensive Python Flask web application for garden management. It helps users plan, plant, and maintain their gardens with seasonal recommendations, weather integration, and automated care scheduling.

**Key Technologies:**
- Python 3.9+
- Flask 3.x (web framework)
- SQLite (database)
- Jinja2 (templating)
- OpenWeatherMap API (weather integration)

## Project Structure

```
Planted/
├── app.py                          # Flask application configuration and routes
├── main.py                         # Application entry point
├── garden_manager/                 # Main application package
│   ├── database/                   # Data layer
│   │   ├── models.py              # Data models and schemas
│   │   ├── plant_data.py          # Plant database management
│   │   ├── garden_db.py           # Garden database operations
│   │   ├── default_plants_data.py # Default plant data (38 plants)
│   │   └── seeds/                 # Seed data (JSON)
│   ├── services/                   # Business logic layer
│   │   ├── weather_service.py     # Weather API integration
│   │   ├── location_service.py    # Location detection
│   │   └── scheduler.py           # Care task scheduling
│   ├── utils/                      # Utility functions
│   │   ├── date_utils.py          # Date and season calculations
│   │   └── plant_utils.py         # Plant-related utilities
│   └── web/                        # Web presentation layer
│       ├── templates/             # HTML templates (Jinja2)
│       └── static/                # CSS, JavaScript, images
├── tests/                          # Test suite
│   ├── unit/                      # Unit tests
│   └── integration/               # Integration tests
└── docs/                          # Documentation
```

## Architectural Patterns

### Repository Pattern
- Database classes encapsulate all data access
- Services don't interact directly with SQLite
- All database operations go through `garden_db.py` or `plant_data.py`

### Service Layer Pattern
- Business logic in `garden_manager/services/`
- Services are independent and reusable
- Presentation layer (`app.py`) calls services, not databases directly

### Dependency Injection
- API keys and configuration via environment variables (`.env`)
- Use `python-dotenv` for environment variable management
- Never hardcode sensitive information

## Code Style and Standards

### Python Style
- Follow PEP 8 guidelines
- Maximum line length: **120 characters** (configured in `.pylintrc` and `pyproject.toml`)
- Use meaningful variable and function names
- Type hints are encouraged but not required
- Docstrings: Not required per project configuration, but helpful for complex functions

### Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/methods: `snake_case()`
- Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Import Organization
```python
# Standard library imports
import os
from datetime import datetime

# Third-party imports
from flask import Flask, render_template
import requests

# Local application imports
from garden_manager.database import garden_db
from garden_manager.services import weather_service
```

## Development Workflow

### Setting Up Development Environment

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install development dependencies:**
   ```bash
   pip install pylint pytest pytest-cov
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenWeatherMap API key (optional - app works with mock data)
   ```

### Running the Application

```bash
# Method 1: Direct execution
python3 main.py

# Method 2: Using run scripts
./run.sh        # macOS/Linux
run.bat         # Windows
```

The application will automatically open in your browser at `http://localhost:5000`.

### Linting

**Always run linting before committing code:**

```bash
# Lint all Python files
pylint $(git ls-files '*.py')

# Lint specific file
pylint garden_manager/services/weather_service.py
```

**Pylint Configuration:**
- Configuration in `.pylintrc` and `pyproject.toml`
- Max line length: 120 characters
- Docstrings are disabled in checks (but still encouraged)
- Configured to allow up to 7 arguments per function

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=garden_manager --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_plant_data.py

# Run specific test
pytest tests/unit/test_plant_data.py::test_function_name
```

**Testing Guidelines:**
- Tests located in `tests/` directory
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Test files must start with `test_`
- Test functions must start with `test_`

### Building (if applicable)

This is a Python application without a build step. However:

```bash
# Verify dependencies are installed
pip install -r requirements.txt

# Run application to verify it works
python3 main.py
```

## Key Concepts and Domain Knowledge

### Gardening Concepts
- **Hardiness Zones**: USDA zones 1-13, determine what plants grow in an area
- **Companion Planting**: Some plants grow better together, others inhibit growth
- **Square-Foot Gardening**: Grid-based layout system used in the application
- **Days to Germination**: Time for seeds to sprout
- **Days to Maturity**: Time until plant is ready to harvest

### Application Features
1. **Plant Database**: 38 plants with verified data from USDA and university extensions
2. **Garden Layout**: Visual grid-based planning tool
3. **Care Scheduling**: Automated watering, fertilizing, and harvest reminders
4. **Weather Integration**: Location-based recommendations
5. **Seasonal Recommendations**: Climate zone and time-based plant suggestions

## Common Tasks and Patterns

### Adding a New Plant to Database

Edit `garden_manager/database/default_plants_data.py`:

```python
{
    "name": "Plant Name",
    "plant_type": "vegetable",  # or "herb", "fruit"
    "scientific_name": "Scientific Name",
    "planting_seasons": ["spring", "summer"],
    "hardiness_zones": "4-9",
    "days_to_germination": 7,
    "days_to_maturity": 60,
    "spacing_inches": 12,
    "soil_requirements": "Well-draining, rich in organic matter",
    "light_requirements": "Full sun (6-8 hours)",
    "water_requirements": "Regular watering, 1 inch per week",
    "companion_plants": "Plant1, Plant2",
    "care_notes": "Additional care information"
}
```

### Adding a New Flask Route

In `app.py`:

```python
@app.route('/your-route')
def your_route_function():
    # Get data from service or database
    data = service.get_data()
    
    # Render template with data
    return render_template('your_template.html', data=data)
```

### Creating a New Service

In `garden_manager/services/`:

```python
class NewService:
    """Service for handling specific business logic."""
    
    def __init__(self, config=None):
        """Initialize service with optional configuration."""
        self.config = config or {}
    
    def perform_action(self, param):
        """Perform the main action of this service."""
        # Business logic here
        return result
```

### Database Operations

```python
from garden_manager.database import garden_db

# Get database instance
db = garden_db.GardenDatabase()

# Create record
new_id = db.create_record(data)

# Read records
records = db.get_all_records()
record = db.get_record_by_id(record_id)

# Update record
db.update_record(record_id, updated_data)

# Delete record
db.delete_record(record_id)
```

## Important Files to Know

### Core Application Files
- `app.py`: Main Flask application, all routes defined here
- `main.py`: Entry point, starts Flask server and opens browser
- `requirements.txt`: Production dependencies
- `pyproject.toml`: Project configuration, dev dependencies, linting rules

### Database Files
- `garden_manager/database/plant_data.py`: Plant database access layer
- `garden_manager/database/garden_db.py`: Garden and care task database operations
- `garden_manager/database/default_plants_data.py`: The 38 plant records
- `garden_manager/database/models.py`: Data models using dataclasses

### Service Files
- `garden_manager/services/weather_service.py`: OpenWeatherMap integration
- `garden_manager/services/location_service.py`: IP-based geolocation
- `garden_manager/services/scheduler.py`: Care task generation logic

### Configuration Files
- `.env`: Environment variables (API keys) - **NOT in git**
- `.env.example`: Template for `.env` file
- `.pylintrc`: Pylint configuration
- `pyproject.toml`: Modern Python project configuration

## Environment Variables

```bash
# Required for real weather data (optional - falls back to mock data)
OPENWEATHERMAP_API_KEY=your_api_key_here

# Optional: Flask secret key (has default for development)
FLASK_SECRET_KEY=your_secret_key_here
```

**Important:** 
- Never commit `.env` to git (it's in `.gitignore`)
- App works without API key using mock weather data
- Copy `.env.example` to `.env` to get started

## Cross-Platform Considerations

### Path Handling
- Always use `os.path.join()` or `pathlib.Path`
- Never use hardcoded path separators (`/` or `\\`)

Example:
```python
from pathlib import Path

# Good
data_dir = Path(__file__).parent / 'data'
file_path = data_dir / 'file.txt'

# Also good
import os
file_path = os.path.join('data', 'file.txt')
```

### Scripts
- Provide both `.sh` (Unix) and `.bat` (Windows) scripts
- Use `#!/usr/bin/env python3` in shebangs

## Database Schema Overview

### Tables
1. **plants**: Plant catalog with growing information
2. **gardens**: User-created garden plots
3. **planted_items**: What's planted where and when
4. **care_tasks**: Automated reminders and task tracking

### Key Relationships
- Gardens contain PlantedItems
- PlantedItems reference Plants
- CareTasks are associated with PlantedItems

## API Integration

### Weather Service
```python
from garden_manager.services.weather_service import WeatherService

weather = WeatherService()
current = weather.get_current_weather(latitude, longitude)
forecast = weather.get_forecast(latitude, longitude)
```

Falls back to mock data if API key is not configured.

## Common Pitfalls to Avoid

1. **Don't import `app.py` from other modules** - Leads to circular imports
2. **Don't put business logic in routes** - Keep routes thin, logic in services
3. **Don't hardcode paths** - Use `os.path.join()` or `pathlib`
4. **Don't commit `.env` file** - It's in `.gitignore` for a reason
5. **Don't skip linting** - Run `pylint` before committing
6. **Don't access database directly from routes** - Use service layer
7. **Don't assume mock data is enabled** - Check if real API is being used

## Documentation References

- **README.md**: User-facing documentation, installation, features
- **CONTRIBUTING.md**: How to contribute, development workflow
- **SETUP.md**: Environment variable configuration
- **docs/architecture.md**: Detailed architecture documentation
- **docs/plant_data_sources.md**: Information about plant data sources
- **docs/deployment.md**: Deployment instructions
- **COPILOT-ISSUE-INSTRUCTIONS.md**: Guidelines for creating issues with Copilot

## When Making Changes

### Before Starting
1. Understand the architectural layer you're working in
2. Check if similar functionality exists elsewhere
3. Review relevant documentation in `docs/`

### While Coding
1. Follow existing code style and patterns
2. Keep changes focused and minimal
3. Update related documentation if needed
4. Add or update tests for new functionality

### Before Committing
1. Run linting: `pylint $(git ls-files '*.py')`
2. Run tests: `pytest`
3. Test the application manually: `python3 main.py`
4. Verify no `.env` file is being committed

## Security Considerations

- **API Keys**: Store in `.env`, never in code
- **SQL Injection**: Use parameterized queries (already implemented)
- **XSS**: Jinja2 auto-escapes by default
- **CSRF**: Consider adding for production
- **File Uploads**: Currently not implemented, be careful if adding

## Performance Notes

- SQLite is sufficient for single-user, local application
- Weather API responses are cached to reduce API calls
- Static files served by Flask in development
- Consider web server (nginx/apache) for production

## Project-Specific Terminology

- **Plot**: A garden area (grid-based layout)
- **Planted Item**: A specific plant in a specific plot location
- **Care Task**: Automated reminder (water, fertilize, harvest, etc.)
- **Companion Plants**: Plants that grow well together
- **Hardiness Zone**: USDA climate zone classification
- **Days to Maturity**: Time from planting to harvest

## Dependencies Management

### Adding New Dependencies

**IMPORTANT: Security Check Required**

Before adding any new dependencies, you MUST:

1. **Check for security vulnerabilities** using the GitHub Advisory Database
2. **Use the latest stable version** unless there's a specific reason not to
3. **Keep dependencies minimal** - only add if absolutely necessary

**Process:**

```bash
# 1. Add dependency to requirements.txt
echo "package-name>=X.Y.Z" >> requirements.txt

# 2. Install and test
pip install -r requirements.txt

# 3. Verify it works
python3 main.py

# 4. Update pyproject.toml if it's a dev dependency
# Add to [project.optional-dependencies] dev section
```

### Checking for Vulnerabilities

```bash
# Check installed packages for known vulnerabilities
pip list --outdated

# Before adding a new package, research it:
# - Check GitHub repository activity and stars
# - Review security advisories
# - Check last update date (avoid abandoned packages)
```

### Dependency Updates

```bash
# Update a specific package
pip install --upgrade package-name

# Update all packages (use with caution)
pip install --upgrade -r requirements.txt

# Always test after updates
pytest && pylint $(git ls-files '*.py')
```

## Git Workflow and Commit Conventions

### Branch Naming

Follow these patterns:

```bash
feature/short-description      # New features
bugfix/short-description       # Bug fixes
hotfix/short-description       # Urgent production fixes
docs/short-description         # Documentation only
refactor/short-description     # Code refactoring
test/short-description         # Test additions/fixes
```

**Examples:**
- `feature/companion-planting-ui`
- `bugfix/weather-api-timeout`
- `docs/setup-instructions`

### Commit Message Conventions

**Format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, no logic change)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**Examples:**

```
feat: Add companion planting recommendations to layout

Implements visual indicators for plant compatibility in the garden
layout interface. Shows beneficial, neutral, and antagonistic
relationships using color-coded icons.

Closes #123
```

```
fix: Correct watering schedule calculation for container plants

Container plants were receiving same schedule as in-ground plants.
Now correctly adjusts frequency based on container size.

Fixes #456
```

**Best Practices:**
- Use present tense ("Add feature" not "Added feature")
- Keep subject line under 50 characters
- Capitalize subject line
- No period at end of subject line
- Separate subject from body with blank line
- Wrap body at 72 characters
- Explain *what* and *why*, not *how*

## CI/CD and Automated Checks

### GitHub Actions Workflows

The repository uses GitHub Actions for automated quality checks:

#### Pylint Workflow (`.github/workflows/pylint.yml`)

**Triggers:**
- Push to main branch
- Pull request to main branch

**What it does:**
- Installs Python dependencies
- Runs pylint on all Python files
- Reports any linting errors

**If it fails:**
```bash
# Run locally to see issues
pylint $(git ls-files '*.py')

# Fix issues and commit
git add .
git commit -m "fix: Resolve linting issues"
```

### Pre-commit Checklist

Before pushing code, always:

```bash
# 1. Run linting
pylint $(git ls-files '*.py')

# 2. Run tests
pytest

# 3. Test the application
python3 main.py
# Manually test your changes in browser

# 4. Check git status
git status

# 5. Review your changes
git diff

# 6. Stage and commit
git add <files>
git commit -m "type: description"

# 7. Push
git push origin <branch-name>
```

## Debugging and Troubleshooting

### Common Issues and Solutions

#### Issue: Import Errors

```bash
# Solution: Ensure you're in the right directory and dependencies are installed
cd /path/to/Planted
pip install -r requirements.txt
```

#### Issue: Database Errors

```bash
# Solution: Database might be corrupted or need migration
# Delete and recreate (local development only!)
rm -f garden_manager/database/garden.db
python3 main.py  # Will recreate with defaults
```

#### Issue: Port Already in Use

```bash
# Solution: Kill process using port 5000
# On Unix/macOS:
lsof -ti:5000 | xargs kill -9

# On Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

#### Issue: Weather API Not Working

```bash
# Solution: Check .env file exists and has valid API key
# Or just use mock data (app works without API key)
cat .env
# If missing:
cp .env.example .env
```

### Debugging Tools and Techniques

#### Using Python Debugger (pdb)

```python
# Add to code where you want to break
import pdb; pdb.set_trace()

# Common pdb commands:
# n (next) - Execute next line
# s (step) - Step into function
# c (continue) - Continue execution
# p variable - Print variable value
# l - List code around current line
# q - Quit debugger
```

#### Flask Debug Mode

Already enabled in `main.py` for development:

```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

Benefits:
- Auto-reload on code changes
- Detailed error pages with stack traces
- Interactive debugger in browser

#### Logging

The application uses Python's logging module:

```python
import logging

# Add debug logging
logging.debug("Variable value: %s", variable)
logging.info("Operation completed")
logging.warning("Potential issue detected")
logging.error("Error occurred: %s", error)
```

View logs in terminal where you ran `python3 main.py`.

#### Database Inspection

```bash
# Use SQLite CLI to inspect database
sqlite3 garden_manager/database/garden.db

# Useful SQLite commands:
.tables              # List all tables
.schema plants       # Show table structure
SELECT * FROM plants LIMIT 5;  # Query data
.quit                # Exit
```

### Performance Profiling

If you need to profile code:

```python
import cProfile
import pstats

# Profile a function
profiler = cProfile.Profile()
profiler.enable()

# Your code here
your_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

## Getting Help

### Internal Resources

1. **Documentation**: Start with `docs/` directory
   - `docs/architecture.md` - System design
   - `docs/api.md` - API documentation
   - `docs/database_migrations.md` - Database changes
   - `docs/deployment.md` - Deployment guide

2. **Code Examples**: Look for similar implementations
   - Check existing routes in `app.py`
   - Review service classes in `garden_manager/services/`
   - Study database operations in `garden_manager/database/`

3. **Issue Tracker**: Search for similar problems
   - [Open Issues](https://github.com/zamays/Planted/issues)
   - [Closed Issues](https://github.com/zamays/Planted/issues?q=is%3Aissue+is%3Aclosed)

### External Resources

**Python & Flask:**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python Official Docs](https://docs.python.org/3/)
- [PEP 8 Style Guide](https://pep8.org/)

**Gardening Domain Knowledge:**
- USDA Plant Database
- University Extension Programs
- See `docs/plant_data_sources.md` for verified sources

**Tools:**
- [Pylint Documentation](https://pylint.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

### When Stuck

1. **Read the error message carefully** - Most errors are self-explanatory
2. **Check recent changes** - Use `git diff` to see what changed
3. **Reproduce the issue** - Create minimal test case
4. **Search existing issues** - Someone may have hit this before
5. **Add debug logging** - Print variables and execution flow
6. **Ask for help** - Create a detailed issue with:
   - What you're trying to do
   - What you've tried
   - Error messages and stack traces
   - System information (OS, Python version)

## Summary for Copilot

When working on this project:
1. **Understand the layer**: Presentation (web), Service, Database, or Utility
2. **Follow patterns**: Repository pattern for data, service layer for logic
3. **Lint and test**: Always run `pylint` and `pytest` before committing
4. **Keep it simple**: Minimal changes, follow existing patterns
5. **Document**: Update docs if making significant changes
6. **Cross-platform**: Use `os.path.join()` or `pathlib` for paths
7. **Environment**: API keys in `.env`, never in code
8. **Test manually**: Run `python3 main.py` to verify changes

This is a well-structured Flask application focused on helping gardeners plan and maintain their gardens. The code is clean, documented, and follows Python best practices.
