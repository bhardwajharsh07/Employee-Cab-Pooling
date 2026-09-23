import math
from services.routing import (
    build_route,
    haversine_distance
)
from database import get_db_connection

DEFAULT_GRID_SIZE = 0.01


def calculate_grid_cell(latitude, longitude, grid_size=DEFAULT_GRID_SIZE):
    """
    Convert latitude/longitude into a geographic grid cell.
    """

    latitude = float(latitude)
    longitude = float(longitude)
    grid_size = float(grid_size)

    latitude_cell = math.floor(latitude / grid_size)
    longitude_cell = math.floor(longitude / grid_size)

    return latitude_cell, longitude_cell


def get_nearby_cells(cell):
    """
    Return the current grid cell and its 8 neighboring cells.
    """

    row, column = cell

    nearby_cells = []

    for row_offset in (-1, 0, 1):

        for column_offset in (-1, 0, 1):

            nearby_cells.append(
                (
                    row + row_offset,
                    column + column_offset
                )
            )

    return nearby_cells


def group_employees_into_cabs(
    employees,
    cab_capacity=4,
    max_distance_km=5
):
    """
    Group employees into geographically nearby cabs.

    employees:
        List of dictionaries containing:
        id, latitude, longitude

    cab_capacity:
        Maximum number of employees per cab.

    max_distance_km:
        Maximum allowed distance from the
        first employee used as the group's anchor.
    """

    if cab_capacity not in (4, 6):
        raise ValueError(
            "Cab capacity must be either 4 or 6."
        )

    if not employees:
        return []

    # Add grid information
    for employee in employees:

        employee["grid_cell"] = calculate_grid_cell(
            employee["latitude"],
            employee["longitude"]
        )

    # Group employees by grid
    grid = {}

    for employee in employees:

        cell = employee["grid_cell"]

        if cell not in grid:
            grid[cell] = []

        grid[cell].append(employee)

    unassigned = {}

    for employee in employees:

        employee_id = employee.get(
            "employee_id",
            employee.get("id")
        )

        if employee_id is None:
            raise ValueError(
                "Employee data must contain an employee ID."
            )

        unassigned[employee_id] = employee

    cabs = []

    while unassigned:

        # Pick one unassigned employee as anchor
        anchor = next(iter(unassigned.values()))

        anchor_cell = anchor["grid_cell"]

        candidate_cells = get_nearby_cells(anchor_cell)

        candidates = []

        for cell in candidate_cells:

            for employee in grid.get(cell, []):

                employee_id = employee.get(
                    "employee_id",
                    employee.get("id")
                )

                if employee_id not in unassigned:
                    continue

                distance = haversine_distance(
                    anchor["latitude"],
                    anchor["longitude"],
                    employee["latitude"],
                    employee["longitude"]
                )

                if distance <= max_distance_km:
                    candidates.append(
                        (distance, employee)
                    )

        # Closest employees first
        candidates.sort(
            key=lambda item: item[0]
        )

        cab_members = []

        for _, employee in candidates:

            if len(cab_members) >= cab_capacity:
                break

            cab_members.append(employee)

        # Safety fallback:
        # every employee must eventually get a cab
        if not cab_members:
            cab_members.append(anchor)

        # Remove assigned employees
        for employee in cab_members:

            employee_id = employee.get(
                "employee_id",
                employee.get("id")
            )

            unassigned.pop(
                employee_id,
                None
            )

        cabs.append(cab_members)

    return cabs


def fit_late_booking(
    booking_id,
    employee_id,
    shift_id,
    booking_date
):
    """
    Try to fit a late booking into an existing active cab.

    The booking is placed only if:
    - the cab belongs to the same shift
    - the cab is on the same date
    - the cab has free capacity
    - the resulting route is valid
    """

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT cab_id
            FROM cab_members
            WHERE booking_id = %s
            """,
            (booking_id,)
        )

        existing_membership = cursor.fetchone()

        if existing_membership:
            return {
                "success": True,
                "cab_id": existing_membership["cab_id"]
            }

        # -----------------------------------------
        # Get the late employee
        # -----------------------------------------

        cursor.execute(
            """
            SELECT
                id AS employee_id,
                name,
                gender,
                home_latitude AS latitude,
                home_longitude AS longitude
            FROM employees
            WHERE id = %s
            """,
            (employee_id,)
        )

        new_employee = cursor.fetchone()

        if not new_employee:

            return {
                "success": False,
                "cab_id": None
            }

        # -----------------------------------------
        # Find active cabs for same shift/date
        # -----------------------------------------

        cursor.execute(
            """
            SELECT
                cabs.id AS cab_id,
                cabs.capacity,
                shifts.max_ride_minutes,
                shifts.start_time,
                offices.latitude AS office_latitude,
                offices.longitude AS office_longitude
            FROM cabs
            JOIN shifts
                ON cabs.shift_id = shifts.id
            JOIN offices
                ON shifts.office_id = offices.id
            WHERE cabs.shift_id = %s
              AND cabs.booking_date = %s
              AND cabs.status = 'ACTIVE'
            ORDER BY cabs.id
            """,
            (
                shift_id,
                booking_date
            )
        )

        cabs = cursor.fetchall()

        # -----------------------------------------
        # Try each existing cab
        # -----------------------------------------

        for cab in cabs:

            cab_id = cab["cab_id"]
            capacity = cab["capacity"]

            # -------------------------------------
            # Get current members
            # -------------------------------------

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
                  AND bookings.status = 'ACTIVE'
                ORDER BY cab_members.id
                """,
                (cab_id,)
            )

            employees = cursor.fetchall()

            # -------------------------------------
            # Check capacity
            # -------------------------------------

            if len(employees) >= capacity:
                continue

            # -------------------------------------
            # Temporarily include late employee
            # -------------------------------------

            test_employees = employees + [
                {
                    **new_employee,
                    "booking_id": booking_id
                }
            ]

            office = {
                "latitude": cab["office_latitude"],
                "longitude": cab["office_longitude"]
            }

            # -------------------------------------
            # Test complete route
            # -------------------------------------

            result = build_route(
                test_employees,
                office,
                cab["max_ride_minutes"],
                cab["start_time"]
            )

            # -------------------------------------
            # Add booking if route is valid
            # -------------------------------------

            if result["valid"]:

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
                        booking_id
                    )
                )

                connection.commit()

                return {
                    "success": True,
                    "cab_id": cab_id
                }

        # -----------------------------------------
        # No suitable cab found
        # -----------------------------------------

        return {
            "success": False,
            "cab_id": None
        }

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()