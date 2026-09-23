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

from services.pooling import (
    group_employees_into_cabs,
    fit_late_booking
)

from services.routing import (
    build_route,
    haversine_distance,
    travel_time_minutes
)

from datetime import datetime, timedelta


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
        employees.gender,
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
            f"CAB-{booking_date}-"
            f"SHIFT-{shift_id}-"
            f"{index + 1}"
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
        WHERE cabs.status = 'ACTIVE'
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


@pooling_bp.route(
    "/route/<int:cab_id>",
    methods=["GET"]
)
def generate_route(cab_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # -----------------------------------------
    # Get cab information
    # -----------------------------------------

    cursor.execute(
        """
        SELECT
            cabs.id AS cab_id,
            cabs.cab_number,
            cabs.capacity,
            cabs.booking_date,
            shifts.id AS shift_id,
            shifts.shift_name,
            shifts.start_time,
            shifts.max_ride_minutes,
            offices.name AS office_name,
            offices.latitude AS office_latitude,
            offices.longitude AS office_longitude
        FROM cabs
        JOIN shifts
            ON cabs.shift_id = shifts.id
        JOIN offices
            ON shifts.office_id = offices.id
        WHERE cabs.id = %s
        """,
        (cab_id,)
    )

    cab = cursor.fetchone()

    if not cab:

        cursor.close()
        connection.close()

        flash("Cab not found.")

        return redirect(
            url_for("pooling.view_pools")
        )

    # -----------------------------------------
    # Get employees in this cab
    # -----------------------------------------

    cursor.execute(
        """
        SELECT
            bookings.id AS booking_id,
            employees.id AS employee_id,
            employees.name,
            employees.gender,
            employees.home_latitude AS latitude,
            employees.home_longitude AS longitude
        FROM cab_members
        JOIN bookings
            ON cab_members.booking_id = bookings.id
        JOIN employees
            ON bookings.employee_id = employees.id
        WHERE cab_members.cab_id = %s
        """,
        (cab_id,)
    )

    employees = cursor.fetchall()

    office = {
        "latitude": cab["office_latitude"],
        "longitude": cab["office_longitude"]
    }

    # -----------------------------------------
    # Build route
    # -----------------------------------------

    result = build_route(
        employees,
        office,
        cab["max_ride_minutes"],
        cab["start_time"]
    )

    # -----------------------------------------
    # Calculate pickup ETAs
    # -----------------------------------------

    route = result["route"]

    total_duration = result[
        "total_duration_minutes"
    ]

    shift_time = cab["start_time"]

    # MySQL TIME may be returned as datetime.timedelta
    # by mysql-connector-python.
    if isinstance(shift_time, timedelta):

        shift_datetime = datetime.combine(
            cab["booking_date"],
            datetime.min.time()
        ) + shift_time

    else:

        shift_datetime = datetime.combine(
            cab["booking_date"],
            shift_time
        )

    first_pickup_time = (
        shift_datetime
        - timedelta(minutes=total_duration)
    )

    current_time = first_pickup_time

    for index, employee in enumerate(route):

        employee["pickup_order"] = index + 1

        employee["pickup_eta"] = current_time

        if index < len(route) - 1:

            next_employee = route[index + 1]

            distance = haversine_distance(
                employee["latitude"],
                employee["longitude"],
                next_employee["latitude"],
                next_employee["longitude"]
            )

        else:

            distance = haversine_distance(
                employee["latitude"],
                employee["longitude"],
                office["latitude"],
                office["longitude"]
            )

        current_time += timedelta(
            minutes=travel_time_minutes(distance)
        )

    # -----------------------------------------
    # Store route information
    # -----------------------------------------

    cursor.execute(
        """
        DELETE FROM routes
        WHERE cab_id = %s
        """,
        (cab_id,)
    )

    cursor.execute(
        """
        INSERT INTO routes
        (
            cab_id,
            total_distance_km,
            estimated_duration_minutes,
            is_valid
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            cab_id,
            result["total_distance_km"],
            result["total_duration_minutes"],
            result["valid"]
        )
    )

    # -----------------------------------------
    # Update pickup order + ETA
    # -----------------------------------------

    for employee in route:

        cursor.execute(
            """
            UPDATE cab_members
            SET
                pickup_order = %s,
                pickup_eta = %s
            WHERE cab_id = %s
              AND booking_id = %s
            """,
            (
                employee["pickup_order"],
                employee["pickup_eta"],
                cab_id,
                employee["booking_id"]
            )
        )

    connection.commit()

    cursor.close()
    connection.close()

    return render_template(
        "route.html",
        cab=cab,
        route=route,
        result=result,
        office=office
    )


@pooling_bp.route("/cancel/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # -----------------------------------------
        # Find the cab containing this booking
        # -----------------------------------------

        cursor.execute(
            """
            SELECT
                cab_members.cab_id,
                cab_members.booking_id
            FROM cab_members
            JOIN bookings
                ON cab_members.booking_id = bookings.id
            WHERE cab_members.booking_id = %s
              AND bookings.status = 'ACTIVE'
            """,
            (booking_id,)
        )

        membership = cursor.fetchone()

        if not membership:
            return "Active booking not found", 404

        cab_id = membership["cab_id"]

        # -----------------------------------------
        # Mark booking as cancelled
        # -----------------------------------------

        cursor.execute(
            """
            UPDATE bookings
            SET status = 'CANCELLED'
            WHERE id = %s
            """,
            (booking_id,)
        )

        # -----------------------------------------
        # Remove employee from this cab
        # -----------------------------------------

        cursor.execute(
            """
            DELETE FROM cab_members
            WHERE booking_id = %s
              AND cab_id = %s
            """,
            (booking_id, cab_id)
        )

        # -----------------------------------------
        # Check whether cab is now empty
        # -----------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS member_count
            FROM cab_members
            WHERE cab_id = %s
            """,
            (cab_id,)
        )

        member_count = cursor.fetchone()["member_count"]

        # -----------------------------------------
        # Cancel cab if no employees remain
        # -----------------------------------------

        if member_count == 0:

            cursor.execute(
                """
                UPDATE cabs
                SET status = 'CANCELLED'
                WHERE id = %s
                """,
                (cab_id,)
            )

        # -----------------------------------------
        # Save all database changes
        # -----------------------------------------

        connection.commit()

        # -----------------------------------------
        # Re-plan only the affected cab
        # -----------------------------------------

        return redirect(
            url_for(
                "pooling.generate_route",
                cab_id=cab_id
            )
        )

    except Exception as error:

        connection.rollback()

        return f"Cancellation failed: {error}", 500

    finally:

        cursor.close()
        connection.close()


@pooling_bp.route(
    "/late-booking/<int:booking_id>",
    methods=["POST"]
)
def late_booking(booking_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return redirect(url_for("auth.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # -----------------------------------------
        # Get booking information
        # -----------------------------------------

        cursor.execute(
            """
            SELECT
                bookings.id AS booking_id,
                bookings.employee_id,
                bookings.shift_id,
                bookings.booking_date
            FROM bookings
            WHERE bookings.id = %s
              AND bookings.status = 'ACTIVE'
            """,
            (booking_id,)
        )

        booking = cursor.fetchone()

        if not booking:
            flash("Active booking not found.")

            return redirect(
                url_for("pooling.view_pools")
            )

        # -----------------------------------------
        # Try to fit booking into existing cab
        # -----------------------------------------

        result = fit_late_booking(
            booking["booking_id"],
            booking["employee_id"],
            booking["shift_id"],
            booking["booking_date"]
        )

        if not result["success"]:

            flash(
                "No suitable cab found for this late booking."
            )

            return redirect(
                url_for("pooling.view_pools")
            )

        cab_id = result["cab_id"]

        # -----------------------------------------
        # Recalculate the affected cab route
        # -----------------------------------------

        return redirect(
            url_for(
                "pooling.generate_route",
                cab_id=cab_id
            )
        )

    finally:

        cursor.close()
        connection.close()