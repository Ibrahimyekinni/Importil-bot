import os
import sys
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

# Ensure project root is on sys.path so bot/ and config/ are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.services.db_service import (
    get_all_users,
    get_all_queries,
    approve_user,
    revoke_user,
)
from config.settings import FLASK_SECRET_KEY, ADMIN_PASSWORD

# ── App setup ────────────────────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "dashboard", "templates"
    ),
    static_folder=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "dashboard", "static"
    ),
)
app.secret_key = FLASK_SECRET_KEY


# ── Auth decorator ───────────────────────────────────────────────────────────

def require_login(f):
    """Redirects unauthenticated requests to /login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    """Show login page (GET) or validate the admin password (POST)."""
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("dashboard"))
        flash("Incorrect password. Please try again.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@require_login
def dashboard():
    """Home dashboard — shows headline stats and recent query activity."""
    users   = get_all_users()   or []
    queries = get_all_queries() or []

    total_users    = len(users)
    approved_users = sum(1 for u in users if u["approved"])
    pending_users  = total_users - approved_users

    # Count queries submitted today (UTC)
    today = datetime.now(timezone.utc).date()
    queries_today = sum(
        1 for q in queries
        if q["timestamp"] and q["timestamp"].date() == today
    )

    recent_queries = queries[:5]

    return render_template(
        "index.html",
        total_users=total_users,
        approved_users=approved_users,
        pending_users=pending_users,
        queries_today=queries_today,
        recent_queries=recent_queries,
    )


@app.route("/users")
@require_login
def users():
    """Users management page — lists all users with approve/revoke actions."""
    all_users = get_all_users() or []
    return render_template("users.html", users=all_users)


@app.route("/approve/<int:telegram_id>", methods=["POST"])
@require_login
def approve(telegram_id):
    """Approve a user and redirect back to users page."""
    approve_user(telegram_id)
    flash(f"User {telegram_id} approved.")
    return redirect(url_for("users"))


@app.route("/revoke/<int:telegram_id>", methods=["POST"])
@require_login
def revoke(telegram_id):
    """Revoke a user's access and redirect back to users page."""
    revoke_user(telegram_id)
    flash(f"User {telegram_id} revoked.")
    return redirect(url_for("users"))


@app.route("/history")
@require_login
def history():
    """Query history page — all compliance queries newest first."""
    all_queries = get_all_queries() or []
    return render_template("history.html", queries=all_queries)


# ── Vercel / local entry point ───────────────────────────────────────────────

# Vercel looks for a variable named `app` (WSGI callable) in this file.
# Running `python api/index.py` starts a local dev server.
if __name__ == "__main__":
    app.run(debug=True, port=5000)
