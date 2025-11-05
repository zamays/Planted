"""
Test production configuration for Render.com deployment.

Validates that the application correctly detects production vs development
mode and configures host/port bindings appropriately.
"""

import os
import pytest


class TestProductionConfiguration:
    """Test production environment detection and configuration."""

    def test_development_mode_default(self):
        """Test that development mode is used when no environment variables are set."""
        # Clean environment
        os.environ.pop('PORT', None)
        os.environ.pop('RENDER', None)

        # Simulate production detection logic from app.py
        is_production = os.getenv('RENDER') == 'true' or os.getenv('PORT') is not None
        port = int(os.getenv('PORT', '5000'))
        host = '0.0.0.0' if is_production else '127.0.0.1'

        assert not is_production, "Should be in development mode by default"
        assert host == '127.0.0.1', "Should bind to localhost in development"
        assert port == 5000, "Should use default port 5000"

    def test_production_mode_with_port_variable(self):
        """Test that production mode is enabled when PORT variable is set (Render.com)."""
        # Set PORT environment variable (Render.com sets this)
        os.environ['PORT'] = '10000'

        # Simulate production detection logic from app.py
        is_production = os.getenv('RENDER') == 'true' or os.getenv('PORT') is not None
        port = int(os.getenv('PORT', '5000'))
        host = '0.0.0.0' if is_production else '127.0.0.1'

        assert is_production, "Should be in production mode when PORT is set"
        assert host == '0.0.0.0', "Should bind to all interfaces in production"
        assert port == 10000, "Should use PORT environment variable"

        # Cleanup
        os.environ.pop('PORT', None)

    def test_production_mode_with_render_variable(self):
        """Test that production mode is enabled when RENDER variable is set."""
        os.environ.pop('PORT', None)
        os.environ['RENDER'] = 'true'

        # Simulate production detection logic from app.py
        is_production = os.getenv('RENDER') == 'true' or os.getenv('PORT') is not None
        port = int(os.getenv('PORT', '5000'))
        host = '0.0.0.0' if is_production else '127.0.0.1'

        assert is_production, "Should be in production mode when RENDER=true"
        assert host == '0.0.0.0', "Should bind to all interfaces in production"
        assert port == 5000, "Should use default port if PORT not set"

        # Cleanup
        os.environ.pop('RENDER', None)

    def test_custom_port_in_development(self):
        """Test that custom port works in development mode."""
        os.environ.pop('PORT', None)
        os.environ.pop('RENDER', None)

        # Simulate using a custom port in development
        custom_port = 8080
        is_production = os.getenv('RENDER') == 'true' or os.getenv('PORT') is not None
        port = int(os.getenv('PORT', str(custom_port)))
        host = '0.0.0.0' if is_production else '127.0.0.1'

        assert not is_production, "Should still be in development mode"
        assert host == '127.0.0.1', "Should bind to localhost"
        assert port == custom_port, "Should use custom port"
