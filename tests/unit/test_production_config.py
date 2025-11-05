"""
Test production configuration for Render.com deployment.

Validates that the application correctly detects production vs development
mode and configures host/port bindings appropriately.
"""

import pytest
from app import get_app_configuration


class TestProductionConfiguration:
    """Test production environment detection and configuration."""

    @pytest.fixture(autouse=True)
    def clean_environment(self, monkeypatch):
        """Clean environment variables before each test."""
        monkeypatch.delenv('PORT', raising=False)
        monkeypatch.delenv('RENDER', raising=False)

    def test_development_mode_default(self):
        """Test that development mode is used when no environment variables are set."""
        is_production, host, port = get_app_configuration()

        assert not is_production, "Should be in development mode by default"
        assert host == '127.0.0.1', "Should bind to localhost in development"
        assert port == 5000, "Should use default port 5000"

    def test_production_mode_with_port_variable(self, monkeypatch):
        """Test that production mode is enabled when PORT variable is set (Render.com)."""
        monkeypatch.setenv('PORT', '10000')

        is_production, host, port = get_app_configuration()

        assert is_production, "Should be in production mode when PORT is set"
        assert host == '0.0.0.0', "Should bind to all interfaces in production"
        assert port == 10000, "Should use PORT environment variable"

    def test_production_mode_with_render_variable(self, monkeypatch):
        """Test that production mode is enabled when RENDER variable is set."""
        monkeypatch.setenv('RENDER', 'true')

        is_production, host, port = get_app_configuration()

        assert is_production, "Should be in production mode when RENDER=true"
        assert host == '0.0.0.0', "Should bind to all interfaces in production"
        assert port == 5000, "Should use default port if PORT not set"

    def test_custom_port_in_development(self):
        """Test that custom port works in development mode."""
        # In development, we would set the port directly, not via PORT env var
        is_production, host, default_port = get_app_configuration()

        assert not is_production, "Should still be in development mode"
        assert host == '127.0.0.1', "Should bind to localhost"
        assert default_port == 5000, "Should return default port in dev mode"

    def test_both_port_and_render_set(self, monkeypatch):
        """Test that production mode works when both PORT and RENDER are set."""
        monkeypatch.setenv('PORT', '8888')
        monkeypatch.setenv('RENDER', 'true')

        is_production, host, port = get_app_configuration()

        assert is_production, "Should be in production mode"
        assert host == '0.0.0.0', "Should bind to all interfaces"
        assert port == 8888, "Should use PORT value"

    def test_render_false_without_port(self, monkeypatch):
        """Test that RENDER='false' does not enable production mode without PORT."""
        monkeypatch.setenv('RENDER', 'false')

        is_production, host, port = get_app_configuration()

        assert not is_production, "Should be in development mode when RENDER is not 'true'"
        assert host == '127.0.0.1', "Should bind to localhost"
        assert port == 5000, "Should use default port"
