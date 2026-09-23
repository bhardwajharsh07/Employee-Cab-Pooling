from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()

        if not username or not password or not name:
            flash("Username, password and name are required.")
            return redirect(url_for("auth.register"))

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Check if username already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = %s",
                (username,)
            )

            existing_user = cursor.fetchone()

            if existing_user:
                flash("Username already exists.")
                cursor.close()
                connection.close()
                return redirect(url_for("auth.register"))

            # Create user
            password_hash = generate_password_hash(password)

            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, 'EMPLOYEE')
                """,
                (username, password_hash)
            )

            user_id = cursor.lastrowid

            # Create employee profile
            cursor.execute(
                """
                INSERT INTO employees
                (
                    user_id,
                    name,
                    phone,
                    home_latitude,
                    home_longitude
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    name,
                    phone,
                    latitude,
                    longitude
                )
            )

            connection.commit()

            cursor.close()
            connection.close()

            flash("Registration successful. Please login.")
            return redirect(url_for("auth.login"))

        except Exception as error:
            print("Registration error:", error)
            flash("Registration failed. Please try again.")

            return redirect(url_for("auth.register"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, username, password_hash, role
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "ADMIN":
                return redirect(url_for("admin.dashboard"))

            return redirect(url_for("employee.dashboard"))

        flash("Invalid username or password.")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("auth.login"))