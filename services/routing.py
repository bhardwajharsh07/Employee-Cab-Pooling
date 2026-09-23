from datetime import datetime, timedelta

from services.pooling import haversine_distance


AVERAGE_SPEED_KMPH = 30


def travel_time_minutes(distance_km):
    """
    Convert distance in kilometers into
    estimated travel time in minutes.

    Uses the prototype average speed.
    """

    if distance_km <= 0:
        return 0

    return (
        distance_km
        / AVERAGE_SPEED_KMPH
        * 60
    )


def calculate_route_distance(stops, office):
    """
    Calculate total route distance.

    Route:
        stop 1
        -> stop 2
        -> ...
        -> office
    """

    if not stops:
        return 0

    total_distance = 0

    for index in range(len(stops) - 1):

        total_distance += haversine_distance(
            stops[index]["latitude"],
            stops[index]["longitude"],
            stops[index + 1]["latitude"],
            stops[index + 1]["longitude"]
        )

    # Last employee -> office
    total_distance += haversine_distance(
        stops[-1]["latitude"],
        stops[-1]["longitude"],
        office["latitude"],
        office["longitude"]
    )

    return total_distance


def calculate_ride_times(stops, office):
    """
    Calculate ride time for every employee.

    The first picked employee has the longest ride.
    """

    ride_times = {}

    for index, employee in enumerate(stops):

        total_distance = 0

        # Current employee -> remaining employees
        for next_index in range(
            index,
            len(stops) - 1
        ):

            current_stop = stops[next_index]
            next_stop = stops[next_index + 1]

            total_distance += haversine_distance(
                current_stop["latitude"],
                current_stop["longitude"],
                next_stop["latitude"],
                next_stop["longitude"]
            )

        # Last employee -> office
        last_stop = stops[-1]

        total_distance += haversine_distance(
            last_stop["latitude"],
            last_stop["longitude"],
            office["latitude"],
            office["longitude"]
        )

        ride_times[employee["employee_id"]] = (
            travel_time_minutes(total_distance)
        )

    return ride_times


def validate_max_ride_time(
    stops,
    office,
    max_ride_minutes
):
    """
    Ensure no employee's ride exceeds
    the configured maximum.
    """

    ride_times = calculate_ride_times(
        stops,
        office
    )

    invalid_employees = []

    for employee_id, ride_time in ride_times.items():

        if ride_time > max_ride_minutes:

            invalid_employees.append(
                {
                    "employee_id": employee_id,
                    "ride_minutes": round(
                        ride_time,
                        2
                    )
                }
            )

    return {
        "valid": len(invalid_employees) == 0,
        "ride_times": ride_times,
        "invalid_employees": invalid_employees
    }


def nearest_neighbour_route(
    employees,
    office
):
    """
    Generate a pickup sequence using the
    nearest-neighbour heuristic.

    The employee farthest from the office
    is used as the initial pickup.
    """

    if not employees:
        return []

    remaining = employees.copy()

    # Start with employee farthest from office
    current = max(
        remaining,
        key=lambda employee: haversine_distance(
            employee["latitude"],
            employee["longitude"],
            office["latitude"],
            office["longitude"]
        )
    )

    remaining.remove(current)

    route = [current]

    while remaining:

        nearest_employee = min(
            remaining,
            key=lambda employee: haversine_distance(
                current["latitude"],
                current["longitude"],
                employee["latitude"],
                employee["longitude"]
            )
        )

        route.append(nearest_employee)

        remaining.remove(nearest_employee)

        current = nearest_employee

    return route


def build_route(
    employees,
    office,
    max_ride_minutes
):
    """
    Build and validate a pickup route.
    """

    if not employees:

        return {
            "route": [],
            "total_distance_km": 0,
            "total_duration_minutes": 0,
            "valid": True,
            "ride_times": {},
            "invalid_employees": []
        }

    # Generate route
    route = nearest_neighbour_route(
        employees,
        office
    )

    # Calculate total distance
    total_distance = calculate_route_distance(
        route,
        office
    )

    # Calculate duration
    total_duration = travel_time_minutes(
        total_distance
    )

    # Validate maximum ride time
    validation = validate_max_ride_time(
        route,
        office,
        max_ride_minutes
    )

    return {
        "route": route,
        "total_distance_km": round(
            total_distance,
            2
        ),
        "total_duration_minutes": round(
            total_duration,
            2
        ),
        "valid": validation["valid"],
        "ride_times": validation["ride_times"],
        "invalid_employees": validation[
            "invalid_employees"
        ]
    }