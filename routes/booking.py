from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database import get_db_connection


booking_bp = Blueprint("booking", __name__)


@booking_bp.route("/book", methods=["GET", "POST"])
def book():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "EMPLOYEE":
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get employee ID
    cursor.execute(
        """
        SELECT id
        FROM employees
        WHERE user_id = %s
        """,
        (session["user_id"],)
    )

    employee = cursor.fetchone()

    if not employee:
        cursor.close()
        connection.close()

        flash("Employee profile not found.")
        return redirect(url_for("employee.dashboard"))

    employee_id = employee["id"]

    if request.method == "POST":

        shift_id = request.form.get("shift_id")
        booking_date = request.form.get("booking_date")

        if not shift_id or not booking_date:
            flash("Please select a shift and date.")

            cursor.close()
            connection.close()

            return redirect(url_for("booking.book"))

        try:

            # Check whether employee already has this booking
            cursor.execute(
                """
                SELECT id
                FROM bookings
                WHERE employee_id = %s
                  AND shift_id = %s
                  AND booking_date = %s
                  AND status = 'ACTIVE'
                """,
                (
                    employee_id,
                    shift_id,
                    booking_date
                )
            )

            existing_booking = cursor.fetchone()

            if existing_booking:
                flash("You already have an active booking for this shift.")
                cursor.close()
                connection.close()

                return redirect(url_for("booking.book"))

            cursor.execute(
                """
                INSERT INTO bookings
                (
                    employee_id,
                    shift_id,
                    booking_date,
                    status
                )
                VALUES (%s, %s, %s, 'ACTIVE')
                """,
                (
                    employee_id,
                    shift_id,
                    booking_date
                )
            )

            connection.commit()

            flash("Cab booking created successfully.")

            cursor.close()
            connection.close()

            return redirect(url_for("booking.my_bookings"))

        except Exception as error:

            connection.rollback()

            print("Booking error:", error)

            flash("Unable to create booking.")

            cursor.close()
            connection.close()

            return redirect(url_for("booking.book"))

    # Get available shifts
    cursor.execute(
        """
        SELECT
            shifts.id,
            shifts.shift_name,
            shifts.start_time,
            shifts.max_ride_minutes,
            offices.name AS office_name
        FROM shifts
        JOIN offices
            ON shifts.office_id = offices.id
        ORDER BY shifts.start_time
        """
    )

    shifts = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "book_cab.html",
        shifts=shifts
    )


@booking_bp.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "EMPLOYEE":
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            bookings.id,
            bookings.booking_date,
            bookings.status,
            shifts.shift_name,
            shifts.start_time,
            offices.name AS office_name
        FROM bookings
        JOIN employees
            ON bookings.employee_id = employees.id
        JOIN shifts
            ON bookings.shift_id = shifts.id
        JOIN offices
            ON shifts.office_id = offices.id
        WHERE employees.user_id = %s
        ORDER BY bookings.booking_date DESC
        """,
        (session["user_id"],)
    )

    bookings = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )


@booking_bp.route("/cancel/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "EMPLOYEE":
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE bookings
        JOIN employees
            ON bookings.employee_id = employees.id
        SET bookings.status = 'CANCELLED'
        WHERE bookings.id = %s
          AND employees.user_id = %s
          AND bookings.status = 'ACTIVE'
        """,
        (
            booking_id,
            session["user_id"]
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    flash("Booking cancelled.")

    return redirect(url_for("booking.my_bookings"))