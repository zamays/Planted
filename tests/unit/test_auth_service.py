"""
Tests for User Authentication Service

Tests user registration, login verification, and user management functionality.
"""

import os
import sqlite3
import tempfile
import pytest
from garden_manager.services.auth_service import AuthService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield db_path
    try:
        os.unlink(db_path)
    except (OSError, PermissionError):
        pass


@pytest.fixture
def auth_service(temp_db):
    """Create an AuthService instance with a temporary database."""
    return AuthService(temp_db)


class TestUserRegistration:
    """Tests for user registration functionality."""

    def test_register_user_success(self, auth_service):
        """Test successful user registration."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        assert user_id is not None
        assert isinstance(user_id, int)

    def test_register_duplicate_username(self, auth_service):
        """Test that duplicate usernames are rejected."""
        auth_service.register_user("testuser", "test1@example.com", "password123")
        user_id = auth_service.register_user("testuser", "test2@example.com", "password456")
        assert user_id is None

    def test_register_duplicate_email(self, auth_service):
        """Test that duplicate emails are rejected."""
        auth_service.register_user("testuser1", "test@example.com", "password123")
        user_id = auth_service.register_user("testuser2", "test@example.com", "password456")
        assert user_id is None

    def test_register_short_username(self, auth_service):
        """Test that short usernames are rejected."""
        with pytest.raises(ValueError, match="Username must be between 3 and 50 characters"):
            auth_service.register_user("ab", "test@example.com", "password123")

    def test_register_long_username(self, auth_service):
        """Test that overly long usernames are rejected."""
        long_username = "a" * 51
        with pytest.raises(ValueError, match="Username must be between 3 and 50 characters"):
            auth_service.register_user(long_username, "test@example.com", "password123")

    def test_register_invalid_email(self, auth_service):
        """Test that invalid emails are rejected."""
        with pytest.raises(ValueError, match="Invalid email address"):
            auth_service.register_user("testuser", "invalid-email", "password123")

    def test_register_short_password(self, auth_service):
        """Test that short passwords are rejected."""
        with pytest.raises(ValueError, match="Password must be at least 6 characters"):
            auth_service.register_user("testuser", "test@example.com", "pass")

    def test_register_empty_fields(self, auth_service):
        """Test that empty fields are rejected."""
        with pytest.raises(ValueError):
            auth_service.register_user("", "test@example.com", "password123")


class TestUserLogin:
    """Tests for user login verification."""

    def test_login_with_username(self, auth_service):
        """Test login with valid username and password."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        user = auth_service.verify_login("testuser", "password123")
        assert user is not None
        assert user['id'] == user_id
        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"

    def test_login_with_email(self, auth_service):
        """Test login with valid email and password."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        user = auth_service.verify_login("test@example.com", "password123")
        assert user is not None
        assert user['id'] == user_id
        assert user['username'] == "testuser"

    def test_login_wrong_password(self, auth_service):
        """Test login with wrong password."""
        auth_service.register_user("testuser", "test@example.com", "password123")
        user = auth_service.verify_login("testuser", "wrongpassword")
        assert user is None

    def test_login_nonexistent_user(self, auth_service):
        """Test login with nonexistent username."""
        user = auth_service.verify_login("nonexistent", "password123")
        assert user is None

    def test_password_hash_different_for_same_password(self, auth_service, temp_db):
        """Test that same password results in different hashes (due to different salts)."""
        auth_service.register_user("user1", "user1@example.com", "password123")
        auth_service.register_user("user2", "user2@example.com", "password123")

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = 'user1'")
            hash1 = cursor.fetchone()[0]
            cursor.execute("SELECT password_hash FROM users WHERE username = 'user2'")
            hash2 = cursor.fetchone()[0]

        assert hash1 != hash2  # Different salts should produce different hashes


class TestUserRetrieval:
    """Tests for user information retrieval."""

    def test_get_user_by_id(self, auth_service):
        """Test retrieving user by ID."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        user = auth_service.get_user_by_id(user_id)
        assert user is not None
        assert user['id'] == user_id
        assert user['username'] == "testuser"
        assert user['email'] == "test@example.com"

    def test_get_nonexistent_user(self, auth_service):
        """Test retrieving nonexistent user."""
        user = auth_service.get_user_by_id(999999)
        assert user is None

    def test_location_fields_initially_none(self, auth_service):
        """Test that location fields are initially None."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        user = auth_service.get_user_by_id(user_id)
        assert user['location'] is None


class TestLocationManagement:
    """Tests for user location management."""

    def test_update_user_location(self, auth_service):
        """Test updating user location."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        auth_service.update_user_location(
            user_id,
            40.7128,
            -74.0060,
            "New York",
            "New York",
            "USA"
        )

        user = auth_service.get_user_by_id(user_id)
        assert user['location'] is not None
        assert user['location']['latitude'] == 40.7128
        assert user['location']['longitude'] == -74.0060
        assert user['location']['city'] == "New York"
        assert user['location']['region'] == "New York"
        assert user['location']['country'] == "USA"

    def test_update_location_partial_info(self, auth_service):
        """Test updating location with partial information."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        auth_service.update_user_location(user_id, 51.5074, -0.1278)

        user = auth_service.get_user_by_id(user_id)
        assert user['location'] is not None
        assert user['location']['latitude'] == 51.5074
        assert user['location']['longitude'] == -0.1278
        assert user['location']['city'] == ""
        assert user['location']['region'] == ""
        assert user['location']['country'] == ""

    def test_login_returns_location(self, auth_service):
        """Test that login returns user's location if set."""
        user_id = auth_service.register_user("testuser", "test@example.com", "password123")
        auth_service.update_user_location(
            user_id,
            40.7128,
            -74.0060,
            "New York",
            "New York",
            "USA"
        )

        user = auth_service.verify_login("testuser", "password123")
        assert user['location'] is not None
        assert user['location']['latitude'] == 40.7128
        assert user['location']['city'] == "New York"


class TestDatabaseSchema:
    """Tests for database schema and table structure."""

    def test_users_table_created(self, auth_service, temp_db):
        """Test that users table is created properly."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'users'

    def test_username_unique_constraint(self, auth_service, temp_db):
        """Test that username has unique constraint."""
        auth_service.register_user("testuser", "test1@example.com", "password123")

        # Manually try to insert duplicate username
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                    ("testuser", "test2@example.com", "hash", "salt")
                )

    def test_email_unique_constraint(self, auth_service, temp_db):
        """Test that email has unique constraint."""
        auth_service.register_user("testuser1", "test@example.com", "password123")

        # Manually try to insert duplicate email
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                    ("testuser2", "test@example.com", "hash", "salt")
                )
