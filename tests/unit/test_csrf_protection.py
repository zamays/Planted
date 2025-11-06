"""
Test CSRF protection implementation.

Tests that CSRF tokens are required for all POST requests and that
AJAX requests include proper CSRF tokens.
"""

import pytest
from flask import session
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(client):
    """Create a test client with a logged-in user."""
    # Create a user and login
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'testuser'
        sess['is_guest'] = False
    return client


class TestCSRFProtection:
    """Test CSRF protection on forms."""

    def test_login_without_csrf_token_fails(self, client):
        """Test that login POST without CSRF token is rejected."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=False)
        
        # Should get a 400 Bad Request due to missing CSRF token
        assert response.status_code == 400

    def test_signup_without_csrf_token_fails(self, client):
        """Test that signup POST without CSRF token is rejected."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'testpass',
            'confirm_password': 'testpass'
        }, follow_redirects=False)
        
        # Should get a 400 Bad Request due to missing CSRF token
        assert response.status_code == 400

    def test_guest_mode_without_csrf_token_fails(self, client):
        """Test that guest mode activation without CSRF token is rejected."""
        response = client.post('/guest-mode', follow_redirects=False)
        
        # Should get a 400 Bad Request due to missing CSRF token
        assert response.status_code == 400

    def test_create_plot_without_csrf_token_fails(self, logged_in_client):
        """Test that create plot POST without CSRF token is rejected."""
        response = logged_in_client.post('/garden/create', data={
            'name': 'Test Plot',
            'width': 4,
            'height': 4,
            'location': 'Backyard'
        }, follow_redirects=False)
        
        # Should get a 400 Bad Request due to missing CSRF token
        assert response.status_code == 400

    def test_delete_plot_without_csrf_token_fails(self, logged_in_client):
        """Test that delete plot POST without CSRF token is rejected."""
        response = logged_in_client.post('/garden/1/delete', follow_redirects=False)
        
        # Should get a 400 Bad Request due to missing CSRF token
        assert response.status_code == 400

    def test_add_plant_without_csrf_token_fails(self, logged_in_client):
        """Test that add plant POST without CSRF token is rejected."""
        response = logged_in_client.post('/plants/add', data={
            'name': 'Test Plant',
            'plant_type': 'vegetable'
        }, follow_redirects=False)
        
        # Should get a 400 Bad Request due to missing CSRF token
        assert response.status_code == 400

    def test_settings_update_without_csrf_token_fails(self, logged_in_client):
        """Test that settings update POST without CSRF token is rejected."""
        response = logged_in_client.post('/settings', data={
            'latitude': '40.7128',
            'longitude': '-74.0060'
        }, follow_redirects=False)
        
        # Should get a 400 Bad Request due to missing CSRF token
        assert response.status_code == 400


class TestCSRFAjaxRequests:
    """Test CSRF protection on AJAX endpoints."""

    def test_complete_task_without_csrf_token_fails(self, logged_in_client):
        """Test that complete task AJAX without CSRF token is rejected."""
        response = logged_in_client.post('/api/complete_task',
                                        json={'task_id': 1},
                                        follow_redirects=False)
        
        # Should get a 400 Bad Request due to missing CSRF token
        assert response.status_code == 400

    def test_update_location_without_csrf_token_fails(self, logged_in_client):
        """Test that update location AJAX without CSRF token is rejected."""
        response = logged_in_client.post('/api/update_location',
                                        json={
                                            'latitude': 40.7128,
                                            'longitude': -74.0060
                                        },
                                        follow_redirects=False)
        
        # Should get a 400 Bad Request due to missing CSRF token
        assert response.status_code == 400


class TestCSRFTokenGeneration:
    """Test that CSRF tokens are properly generated."""

    def test_csrf_token_in_login_page(self, client):
        """Test that login page includes CSRF token."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'csrf_token' in response.data

    def test_csrf_token_in_meta_tag(self, client):
        """Test that pages include CSRF meta tag for JavaScript."""
        with client.session_transaction() as sess:
            sess['is_guest'] = True
        response = client.get('/')
        assert response.status_code == 200
        assert b'name="csrf-token"' in response.data

    def test_csrf_token_in_signup_page(self, client):
        """Test that signup page includes CSRF token."""
        response = client.get('/signup')
        assert response.status_code == 200
        assert b'csrf_token' in response.data

    def test_csrf_token_in_create_plot_page(self, logged_in_client):
        """Test that create plot page includes CSRF token."""
        response = logged_in_client.get('/garden/create')
        assert response.status_code == 200
        assert b'csrf_token' in response.data
