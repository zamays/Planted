"""
Test secret key security requirements.

Validates that the application enforces secure secret key configuration
and prevents deployment with weak or missing secret keys.
"""

import os
import sys

import pytest


class TestSecretKeySecurity:
    """Test Flask secret key security validation."""

    def test_missing_secret_key_raises_error(self, monkeypatch):
        """Test that missing FLASK_SECRET_KEY raises ValueError."""
        # Mock os.getenv to return None for FLASK_SECRET_KEY after .env is loaded
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return None
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="FLASK_SECRET_KEY must be set"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_weak_secret_key_garden_manager_raises_error(self, monkeypatch):
        """Test that weak secret key 'garden_manager_secret_key' raises ValueError."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return 'garden_manager_secret_key'
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="known weak/placeholder value"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_weak_secret_key_planted_raises_error(self, monkeypatch):
        """Test that weak secret key 'planted_secret_key_change_this_in_production' raises ValueError."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return 'planted_secret_key_change_this_in_production'
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="known weak/placeholder value"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_weak_secret_key_placeholder_raises_error(self, monkeypatch):
        """Test that placeholder 'your_secret_key_here' raises ValueError."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return 'your_secret_key_here'
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="known weak/placeholder value"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_short_secret_key_raises_error(self, monkeypatch):
        """Test that secret key less than 32 characters raises ValueError."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return 'short_key_12345'
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="must be at least 32 characters long"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_32_character_key_is_valid(self, monkeypatch):
        """Test that a 32-character secure key is accepted."""
        # 32 character hex string
        secure_key = "a" * 32
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return secure_key
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        # Should not raise any error
        import app  # pylint: disable=import-outside-toplevel,unused-import
        assert app.app.config["SECRET_KEY"] == secure_key

    def test_64_character_key_is_valid(self, monkeypatch):
        """Test that a 64-character secure key is accepted (recommended)."""
        # 64 character hex string (output of secrets.token_hex(32))
        secure_key = "15037f6fd89401e354d3b2028ef042edf2ca6b73c0344944e99613f85fca50f9"
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return secure_key
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        # Should not raise any error
        import app  # pylint: disable=import-outside-toplevel,unused-import
        assert app.app.config["SECRET_KEY"] == secure_key

    def test_cryptographically_secure_key_format(self, monkeypatch):
        """Test that a cryptographically secure key in hex format is accepted."""
        import secrets  # pylint: disable=import-outside-toplevel
        secure_key = secrets.token_hex(32)  # Generates 64 character hex string
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return secure_key
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        # Should not raise any error
        import app  # pylint: disable=import-outside-toplevel,unused-import
        assert app.app.config["SECRET_KEY"] == secure_key
        assert len(app.app.config["SECRET_KEY"]) == 64

    def test_error_message_includes_generation_command(self, monkeypatch):
        """Test that error messages include the command to generate a secure key."""
        # Mock os.getenv to return None for FLASK_SECRET_KEY
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return None
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match='python3 -c "import secrets; print\\(secrets.token_hex\\(32\\)\\)"'):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_weak_key_change_this_raises_error(self, monkeypatch):
        """Test that 'change_this' placeholder raises ValueError."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return 'change_this'
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="known weak/placeholder value"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_weak_key_secret_raises_error(self, monkeypatch):
        """Test that 'secret' placeholder raises ValueError."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return 'secret'
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="known weak/placeholder value"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_render_missing_key_shows_dashboard_instructions(self, monkeypatch):
        """Test that missing key on Render shows Dashboard-specific instructions."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return None
            if key == 'RENDER':
                return 'true'
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="Render Dashboard"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_render_weak_key_shows_dashboard_instructions(self, monkeypatch):
        """Test that weak key on Render shows Dashboard-specific instructions."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return 'planted_secret_key_change_this_in_production'
            if key == 'RENDER':
                return 'true'
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="Render Dashboard.*Edit FLASK_SECRET_KEY"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_render_short_key_shows_dashboard_instructions(self, monkeypatch):
        """Test that short key on Render shows Dashboard-specific instructions."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return 'short_key'
            if key == 'RENDER':
                return 'true'
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="Render Dashboard.*Edit FLASK_SECRET_KEY"):
            import app  # pylint: disable=import-outside-toplevel,unused-import

    def test_non_render_missing_key_shows_env_file_instructions(self, monkeypatch):
        """Test that missing key on non-Render deployment shows .env file instructions."""
        original_getenv = os.getenv

        def mock_getenv(key, default=None):
            if key == 'FLASK_SECRET_KEY':
                return None
            if key == 'RENDER':
                return None
            return original_getenv(key, default)

        monkeypatch.setattr('os.getenv', mock_getenv)

        # Clear any previously imported app module
        if 'app' in sys.modules:
            del sys.modules['app']

        with pytest.raises(ValueError, match="\\.env file"):
            import app  # pylint: disable=import-outside-toplevel,unused-import
