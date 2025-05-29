import os
from pathlib import Path
from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    session,
    abort,
    flash,
)
from datetime import datetime
import time  # To format modification times

app = Flask(__name__)
# IMPORTANT: Change this secret key for any real deployment!
# Use a long, random string. You can generate one using:
# python -c 'import secrets; print(secrets.token_hex(16))'
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_super_secret_replace_me")

# --- Configuration ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
CONFIG_BASE_DIR = Path.home() / ".config"
SESSION_DIR_PREFIX = "Session-production-devprod"


# --- Context Processor ---
@app.context_processor
def inject_now():
    """Injects the 'now' function (datetime.now) into the template context."""
    # We pass the function itself, so the template can call .year on its result
    return {"now": datetime.now}


# --- Helper Functions ---
def is_logged_in():
    """Checks if the user is logged in via session."""
    return session.get("logged_in", False)


# --- Helper Functions ---
def is_logged_in():
    """Checks if the user is logged in via session."""
    return session.get("logged_in", False)


def format_timestamp(ts):
    """Formats a UNIX timestamp into a readable string."""
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"


def get_session_users():
    """Scans the config directory for Session user profiles."""
    users_found = []
    scan_time = datetime.now()

    if not CONFIG_BASE_DIR.exists() or not CONFIG_BASE_DIR.is_dir():
        flash(f"Error: Configuration directory not found: {CONFIG_BASE_DIR}", "danger")
        return [], scan_time

    try:
        for item in CONFIG_BASE_DIR.iterdir():
            if item.is_dir() and item.name.startswith(SESSION_DIR_PREFIX):
                dir_name = item.name
                username = dir_name[len(SESSION_DIR_PREFIX) :]
                if not username:
                    # Handle the base directory itself if it has the prefix but no suffix
                    # Might indicate a default or improperly named profile
                    username = "[Default/Base]"  # Or skip using 'continue'

                try:
                    # Get directory metadata (last modified time)
                    stats = os.stat(item)
                    last_modified_ts = stats.st_mtime
                    last_modified_str = format_timestamp(last_modified_ts)
                except OSError:
                    last_modified_str = "Error reading time"

                users_found.append(
                    {
                        "username": username,
                        "path": str(item),
                        "last_modified": last_modified_str,
                    }
                )

        # Sort users alphabetically by username for consistent display
        users_found.sort(key=lambda x: x["username"])

    except OSError as e:
        flash(
            f"Error scanning config directory '{CONFIG_BASE_DIR}': {e}. Check permissions.",
            "danger",
        )

    return users_found, scan_time


# --- Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USERNAME
            and request.form.get("password") == ADMIN_PASSWORD
        ):
            session["logged_in"] = True
            session.permanent = True  # Optional: make session last longer
            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid Credentials. Please try again."
            flash(error, "danger")  # Use flash for errors too

    # Pass error directly if needed for immediate display (flash is preferred)
    return render_template("login.html", immediate_error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/")
def index():
    """Redirect base route to dashboard if logged in, else to login."""
    if is_logged_in():
        return redirect(url_for("admin_dashboard"))
    else:
        return redirect(url_for("login"))


@app.route("/admin")
def admin_dashboard():
    if not is_logged_in():
        flash("Please log in to access the admin area.", "warning")
        return redirect(url_for("login"))

    users, scan_time = get_session_users()
    user_count = len(users)

    # --- "Fancy" Simulated Stats ---
    # Make these look somewhat dynamic or plausible
    active_sessions = max(
        1, user_count // 2 + (scan_time.second % 3) - 1
    )  # Example calculation
    system_health_options = ["Optimal", "Good", "Warning", "Degraded"]
    system_health = system_health_options[scan_time.minute % len(system_health_options)]
    health_color = {
        "Optimal": "success",
        "Good": "info",
        "Warning": "warning",
        "Degraded": "danger",
    }.get(system_health, "secondary")

    stats = {
        "user_count": user_count,
        "active_sessions": active_sessions,  # Simulated
        "system_health": system_health,  # Simulated
        "health_color": health_color,  # Color for health status
        "last_scan": scan_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }

    return render_template("admin_dashboard.html", users=users, stats=stats)


# --- Error Handling ---
@app.errorhandler(404)
def page_not_found(e):
    if is_logged_in():
        return render_template("404.html"), 404  # Optional: create a 404 template
    return redirect(url_for("login"))  # Redirect unauth users


@app.errorhandler(403)
def forbidden(e):
    if is_logged_in():
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("login"))


if __name__ == "__main__":
    # Use 127.0.0.1 for local access only
    # Use 0.0.0.0 to make it accessible on your local network (use with caution)
    # debug=False for production/real use
    app.run(host="127.0.0.1", port=5000, debug=True)
