"""
Authentication blueprint for Planted application.

Handles user login, signup, logout, guest mode, and settings management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from garden_manager.web.blueprints.utils import get_current_user_id, is_logged_in

auth_bp = Blueprint('auth', __name__)


def init_blueprint(services):
    """
    Initialize the blueprint with required services.
    
    Args:
        services: Dictionary containing service instances
    """
    global auth_service, location_service, weather_service
    auth_service = services.get('auth_service')
    location_service = services.get('location_service')
    weather_service = services.get('weather_service')


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login with username and password.

    GET: Display login form
    POST: Authenticate user credentials and establish session

    Returns:
        str: Rendered login page or redirect to dashboard
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password are required", "error")
            return render_template("login.html")

        if auth_service is None:
            flash("Authentication service unavailable", "error")
            return render_template("login.html")

        user = auth_service.verify_login(username, password)
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_guest"] = False
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("main.dashboard"))

        flash("Invalid username or password", "error")
        return render_template("login.html")

    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """
    Handle new user registration.

    GET: Display signup form
    POST: Create new user account with validation

    Returns:
        str: Rendered signup page or redirect to dashboard on success
    """
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validation
        if not all([username, email, password, confirm_password]):
            flash("All fields are required", "error")
            return render_template("signup.html")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("signup.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters", "error")
            return render_template("signup.html")

        if auth_service is None:
            flash("Authentication service unavailable", "error")
            return render_template("signup.html")

        # Create user
        try:
            user_id = auth_service.register_user(username, email, password)
            
            if user_id is None:
                flash("Username or email already exists", "error")
                return render_template("signup.html")

            session.clear()
            session["user_id"] = user_id
            session["username"] = username
            session["is_guest"] = False
            flash(f"Welcome to Planted, {username}!", "success")
            return redirect(url_for("main.dashboard"))
        
        except ValueError as e:
            flash(str(e), "error")
            return render_template("signup.html")

    return render_template("signup.html")


@auth_bp.route("/guest-mode", methods=["GET", "POST"])
def guest_mode():
    """
    Enable guest mode for exploring the application without account.

    Guest mode provides limited functionality without persistence.

    Returns:
        str: Rendered guest mode page or redirect to dashboard
    """
    if request.method == "POST":
        session.clear()
        session["is_guest"] = True
        session["username"] = "Guest"
        flash("You're now in guest mode. Your data will not be saved.", "info")
        return redirect(url_for("main.dashboard"))

    return render_template("guest_mode.html")


@auth_bp.route("/logout")
def logout():
    """
    Log out the current user and clear session.

    Returns:
        redirect: Redirect to login page
    """
    username = session.get("username", "Guest")
    session.clear()
    flash(f"Goodbye, {username}!", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """
    Display and update user settings.

    Handles location preferences, account settings, and user profile updates.

    Returns:
        str: Rendered settings page
    """
    user_id = get_current_user_id()

    if request.method == "POST":
        # Handle location update
        if "latitude" in request.form:
            latitude = float(request.form.get("latitude"))
            longitude = float(request.form.get("longitude"))
            city = request.form.get("city", "")
            region = request.form.get("region", "")
            country = request.form.get("country", "")

            if user_id and auth_service:
                auth_service.update_user_location(
                    user_id, latitude, longitude, city, region, country
                )
                
                # Update location service
                if location_service:
                    location_service.set_manual_location(
                        latitude, longitude,
                        {'city': city, 'region': region, 'country': country}
                    )
                
                # Update weather for new location
                if weather_service:
                    weather_service.get_current_weather(latitude, longitude)
                    weather_service.get_forecast(latitude, longitude)
                
                flash("Location updated successfully", "success")
            else:
                flash("Unable to update location in guest mode", "error")

        return redirect(url_for("auth.settings"))

    # Get user data
    user = None
    if user_id and auth_service:
        user = auth_service.get_user_by_id(user_id)

    # Get current location
    current_location = None
    if location_service and location_service.current_location:
        current_location = location_service.current_location

    return render_template(
        "settings.html",
        user=user,
        location=current_location,
        is_guest=session.get("is_guest", False)
    )


@auth_bp.route("/settings/change-password", methods=["POST"])
def change_password():
    """
    Change user password with current password verification.

    Returns:
        redirect: Redirect to settings page
    """
    user_id = get_current_user_id()

    if not user_id:
        flash("Password change not available in guest mode", "error")
        return redirect(url_for("auth.settings"))

    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not all([current_password, new_password, confirm_password]):
        flash("All password fields are required", "error")
        return redirect(url_for("auth.settings"))

    if new_password != confirm_password:
        flash("New passwords do not match", "error")
        return redirect(url_for("auth.settings"))

    if len(new_password) < 8:
        flash("Password must be at least 8 characters", "error")
        return redirect(url_for("auth.settings"))

    if auth_service is None:
        flash("Authentication service unavailable", "error")
        return redirect(url_for("auth.settings"))

    result = auth_service.change_password(user_id, current_password, new_password)
    
    if result.get("success"):
        flash("Password changed successfully", "success")
    else:
        flash(result.get("message", "Password change failed"), "error")

    return redirect(url_for("auth.settings"))


@auth_bp.route("/settings/update-email", methods=["POST"])
def update_user_email():
    """
    Update user email address with password verification.

    Returns:
        redirect: Redirect to settings page
    """
    user_id = get_current_user_id()

    if not user_id:
        flash("Email update not available in guest mode", "error")
        return redirect(url_for("auth.settings"))

    new_email = request.form.get("new_email")
    password = request.form.get("password")

    if not new_email or not password:
        flash("Email and password are required", "error")
        return redirect(url_for("auth.settings"))

    if auth_service is None:
        flash("Authentication service unavailable", "error")
        return redirect(url_for("auth.settings"))

    # Verify password first
    user = auth_service.get_user_by_id(user_id)
    if not user or not auth_service.verify_password(password, user.get("password_hash", "")):
        flash("Invalid password", "error")
        return redirect(url_for("auth.settings"))

    # Update email
    result = auth_service.update_user_email(user_id, new_email)
    
    if result.get("success"):
        flash("Email updated successfully", "success")
    else:
        flash(result.get("message", "Email update failed"), "error")

    return redirect(url_for("auth.settings"))
