"""
Authentication Service

Handles user authentication, registration, and session management.
Provides secure password hashing and user verification using bcrypt.
"""

import sqlite3
from typing import Optional, Dict
import bcrypt


class AuthService:
    """
    Service for user authentication and account management.

    Provides user registration, login verification, and session management
    with secure password hashing using bcrypt.
    """

    def __init__(self, db_path: str = "garden.db"):
        """
        Initialize authentication service.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_users_table()

    def _init_users_table(self):
        """Create users table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    location_latitude REAL,
                    location_longitude REAL,
                    location_city TEXT,
                    location_region TEXT,
                    location_country TEXT,
                    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            str: Bcrypt hash string
        """
        # Generate salt and hash password using bcrypt
        salt = bcrypt.gensalt()
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against a bcrypt hash.

        Args:
            password: Plain text password
            password_hash: Bcrypt hash to verify against

        Returns:
            bool: True if password matches, False otherwise
        """
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def register_user(self, username: str, email: str, password: str) -> Optional[int]:
        """
        Register a new user account.

        Args:
            username: Unique username (3-50 characters)
            email: Valid email address
            password: Password (minimum 6 characters)

        Returns:
            Optional[int]: User ID if successful, None if username/email already exists

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        if not username or len(username) < 3 or len(username) > 50:
            raise ValueError("Username must be between 3 and 50 characters")
        if not email or '@' not in email:
            raise ValueError("Invalid email address")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")

        # Hash password using bcrypt
        password_hash = self._hash_password(password)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (username, email, password_hash)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Username or email already exists
            return None

    def verify_login(self, username: str, password: str) -> Optional[Dict]:
        """
        Verify user login credentials.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            Optional[Dict]: User information if credentials are valid, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Try username or email
            cursor.execute(
                """
                SELECT id, username, email, password_hash,
                       location_latitude, location_longitude,
                       location_city, location_region, location_country
                FROM users
                WHERE username = ? OR email = ?
                """,
                (username, username)
            )
            row = cursor.fetchone()

            if not row:
                return None

            # Verify password using bcrypt
            user_id, db_username, email, password_hash, lat, lon, city, region, country = row

            if self._verify_password(password, password_hash):
                return {
                    'id': user_id,
                    'username': db_username,
                    'email': email,
                    'location': {
                        'latitude': lat,
                        'longitude': lon,
                        'city': city,
                        'region': region,
                        'country': country
                    } if lat and lon else None
                }

            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Get user information by ID.

        Args:
            user_id: User ID

        Returns:
            Optional[Dict]: User information if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, username, email,
                       location_latitude, location_longitude,
                       location_city, location_region, location_country
                FROM users
                WHERE id = ?
                """,
                (user_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            user_id, username, email, lat, lon, city, region, country = row
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'location': {
                    'latitude': lat,
                    'longitude': lon,
                    'city': city,
                    'region': region,
                    'country': country
                } if lat and lon else None
            }

    def update_user_location(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        city: str = "",
        region: str = "",
        country: str = ""
    ):
        """
        Update user's location information.

        Args:
            user_id: User ID
            latitude: Geographic latitude
            longitude: Geographic longitude
            city: City name
            region: State/region name
            country: Country name
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users
                SET location_latitude = ?,
                    location_longitude = ?,
                    location_city = ?,
                    location_region = ?,
                    location_country = ?
                WHERE id = ?
                """,
                (latitude, longitude, city, region, country, user_id)
            )
            conn.commit()

    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change user's password.

        Args:
            user_id: User ID
            current_password: Current plain text password for verification
            new_password: New plain text password

        Returns:
            bool: True if password was changed successfully, False if current password is incorrect

        Raises:
            ValueError: If new password is invalid
        """
        if not new_password or len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Verify current password
            cursor.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if not row:
                return False

            password_hash = row[0]
            if not self._verify_password(current_password, password_hash):
                return False

            # Update to new password
            new_hash = self._hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, user_id)
            )
            conn.commit()
            return True

    def change_email(self, user_id: int, new_email: str) -> bool:
        """
        Change user's email address.

        Args:
            user_id: User ID
            new_email: New email address

        Returns:
            bool: True if email was changed successfully, False if email is already in use

        Raises:
            ValueError: If email is invalid
        """
        if not new_email or '@' not in new_email:
            raise ValueError("Invalid email address")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET email = ? WHERE id = ?",
                    (new_email, user_id)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # Email already exists
            return False
