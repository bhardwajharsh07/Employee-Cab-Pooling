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
from services.pooling import group_employees_into_cabs


pooling_bp = Blueprint(
    "pooling",
    __name__
)


@pooling_bp.route("/generate", methods=["GET", "POST"])
def generate():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            shifts.id,
            shifts.shift_name,
            shifts.start_time,
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

    if request.method == "GET":

        return render_template(
            "generate_pool.html",
            shifts=shifts
        )

    shift_id = request.form.get("shift_id")
    booking_date = request.form.get("booking_date")
    capacity = int(
        request.form.get("capacity", 4)
    )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            bookings.id AS booking_id,
            employees.id AS employee_id,
            employees.name,
            employees.home_latitude AS latitude,
            employees.home_longitude AS longitude
        FROM bookings
        JOIN employees
            ON bookings.employee_id = employees.id
        WHERE bookings.shift_id = %s
          AND bookings.booking_date = %s
          AND bookings.status = 'ACTIVE'
        """,
        (
            shift_id,
            booking_date
        )
    )

    employees = cursor.fetchall()

    if not employees:

        cursor.close()
        connection.close()

        flash("No active bookings found.")
        return redirect(
            url_for("pooling.generate")
        )

    cabs = group_employees_into_cabs(
        employees,
        cab_capacity=capacity
    )

    # Remove existing cabs for this shift/date
    cursor.execute(
        """
        DELETE FROM cabs
        WHERE shift_id = %s
          AND booking_date = %s
        """,
        (
            shift_id,
            booking_date
        )
    )

    connection.commit()

    # Create new cabs
    for index, cab_members in enumerate(cabs):

        cab_number = (
            f"CAB-{booking_date}-{index + 1}"
        )

        cursor.execute(
            """
            INSERT INTO cabs
            (
                cab_number,
                capacity,
                booking_date,
                shift_id
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                cab_number,
                capacity,
                booking_date,
                shift_id
            )
        )

        cab_id = cursor.lastrowid

        for employee in cab_members:

            cursor.execute(
                """
                INSERT INTO cab_members
                (
                    cab_id,
                    booking_id
                )
                VALUES (%s, %s)
                """,
                (
                    cab_id,
                    employee["booking_id"]
                )
            )

    connection.commit()

    cursor.close()
    connection.close()

    flash(
        f"{len(cabs)} cab(s) created successfully."
    )

    return redirect(
        url_for("pooling.view_pools")
    )


@pooling_bp.route("/view")
def view_pools():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            cabs.id AS cab_id,
            cabs.cab_number,
            cabs.capacity,
            cabs.booking_date,
            shifts.shift_name,
            offices.name AS office_name
        FROM cabs
        JOIN shifts
            ON cabs.shift_id = shifts.id
        JOIN offices
            ON shifts.office_id = offices.id
        ORDER BY
            cabs.booking_date DESC,
            cabs.id
        """
    )

    cabs = cursor.fetchall()

    for cab in cabs:

        cursor.execute(
            """
            SELECT
                employees.name,
                employees.home_latitude,
                employees.home_longitude
            FROM cab_members
            JOIN bookings
                ON cab_members.booking_id = bookings.id
            JOIN employees
                ON bookings.employee_id = employees.id
            WHERE cab_members.cab_id = %s
            ORDER BY cab_members.id
            """,
            (cab["cab_id"],)
        )

        cab["members"] = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "cab_pools.html",
        cabs=cabs
    )