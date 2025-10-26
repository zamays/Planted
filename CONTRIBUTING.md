# Contributing to Planted

Thank you for your interest in contributing to Planted! We welcome contributions from the community.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

   ```bash
   git clone https://github.com/YOUR-USERNAME/Planted.git
   cd Planted
   ```

3. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   pip install pylint pytest pytest-cov  # For development
   ```

## Development Workflow

1. **Create a new branch** for your feature or bugfix:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards:
   - Follow PEP 8 style guidelines
   - Write clear, descriptive commit messages
   - Add docstrings to new functions and classes
   - Keep changes focused and atomic

3. **Test your changes**:

   ```bash
   # Run the application
   python3 main.py
   
   # Run linting
   pylint $(git ls-files '*.py')
   ```

4. **Commit your changes**:

   ```bash
   git add .
   git commit -m "Brief description of your changes"
   ```

5. **Push to your fork**:

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

## Code Style

- Follow PEP 8 Python style guidelines
- Maximum line length: 120 characters
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and concise

## Linting

We use Pylint to maintain code quality. Before submitting a PR, run:

```bash
pylint $(git ls-files '*.py')
```

Configuration is in `.pylintrc` and `pyproject.toml`.

## Adding New Features

When adding new features:

1. **Update documentation** in README.md if needed
2. **Add examples** of how to use the feature
3. **Consider cross-platform compatibility** (Windows, macOS, Linux)
4. **Test on multiple Python versions** (3.9+)

## Adding Plants to the Database

To add new plants:

1. Edit `garden_manager/database/default_plants_data.py`
2. Add your plant data to the `plants_data` list
3. Follow the existing plant data structure
4. Include all required fields:
   - name, plant_type, scientific_name
   - planting_seasons, hardiness_zones
   - days_to_germination, days_to_maturity
   - spacing_inches, soil_requirements
   - light_requirements, water_requirements
   - care_notes

## Reporting Bugs

When reporting bugs, please include:

1. **Description** of the issue
2. **Steps to reproduce** the problem
3. **Expected behavior**
4. **Actual behavior**
5. **System information** (OS, Python version)
6. **Error messages** or stack traces if applicable

## Feature Requests

We welcome feature requests! Please:

1. **Check existing issues** to avoid duplicates
2. **Describe the feature** clearly
3. **Explain the use case** and benefits
4. **Consider implementation** complexity

## Questions?

If you have questions about contributing:

1. Check existing [Issues](https://github.com/zamays/Planted/issues)
2. Open a new issue with the "question" label
3. Be patient - we're all volunteers!

## Code of Conduct

Be respectful and constructive in all interactions. We're all here to learn and improve Planted together.

## License

By contributing to Planted, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Planted! 🌱**
