import math


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


def haversine_distance(
    latitude1,
    longitude1,
    latitude2,
    longitude2
):
    """
    Calculate straight-line distance between
    two geographical coordinates.

    Returns distance in kilometers.
    """

    latitude1 = float(latitude1)
    longitude1 = float(longitude1)
    latitude2 = float(latitude2)
    longitude2 = float(longitude2)

    earth_radius = 6371.0

    lat1 = math.radians(latitude1)
    lat2 = math.radians(latitude2)

    delta_lat = math.radians(
        latitude2 - latitude1
    )

    delta_lon = math.radians(
        longitude2 - longitude1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


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