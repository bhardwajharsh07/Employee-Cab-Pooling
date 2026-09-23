from flask import Blueprint, render_template, session, redirect, url_for


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("auth.login"))

    return render_template(
        "admin_dashboard.html",
        username=session.get("username")
    )