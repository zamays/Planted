"""
Shared utilities for Flask blueprints.

This module contains common helper functions used across multiple blueprints,
including authentication checks and user management.
"""

from flask import session


def get_current_user_id():
    """
    Get the current user ID from session.

    Returns:
        Optional[int]: User ID if logged in, None if guest mode or not logged in
    """
    if session.get('is_guest'):
        return None
    return session.get('user_id')


def is_logged_in():
    """Check if user is logged in (not guest mode)."""
    return session.get('user_id') is not None and not session.get('is_guest')
