from flask import Blueprint, render_template, session, redirect, url_for


employee_bp = Blueprint("employee", __name__)


@employee_bp.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "EMPLOYEE":
        return redirect(url_for("auth.login"))

    return render_template(
        "employee_dashboard.html",
        username=session.get("username")
    )