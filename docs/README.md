# Planted Documentation

Welcome to the Planted documentation directory!

## Documentation Files

- [Architecture](architecture.md) - System architecture and design decisions
- [API Reference](api.md) - API documentation for developers
- [Deployment](deployment.md) - Deployment guide for web hosting
- [Plant Data Sources](plant_data_sources.md) - Information about plant database sources and reliability

## Quick Links

- [README](../README.md) - Main project overview and quick start
- [SETUP](../SETUP.md) - Detailed setup instructions
- [CONTRIBUTING](../CONTRIBUTING.md) - How to contribute to the project

## Documentation Structure

This documentation is organized to help different audiences:

### For Users
- [README.md](../README.md) - Getting started with Planted
- [SETUP.md](../SETUP.md) - Installation and configuration
- [Plant Data Sources](plant_data_sources.md) - Plant information sources and reliability
- User guides (coming soon)

### For Contributors
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [architecture.md](architecture.md) - Understanding the codebase
- [API Reference](api.md) - Module and function documentation

### For Deployers
- [deployment.md](deployment.md) - Hosting Planted on the web
- Security considerations
- Production configuration

## Building Documentation

Future documentation will use Sphinx for auto-generated API docs:

```bash
# Install sphinx (when we add it)
pip install sphinx sphinx-rtd-theme

# Build documentation
cd docs
make html
```

## Contributing to Documentation

Documentation improvements are always welcome! Please:

1. Keep documentation up to date with code changes
2. Use clear, simple language
3. Include code examples where helpful
4. Add diagrams for complex concepts
5. Test all commands and examples

## Style Guide

- Use Markdown for documentation files
- Use code blocks with language specifiers
- Include screenshots for UI features
- Keep lines under 100 characters for readability
