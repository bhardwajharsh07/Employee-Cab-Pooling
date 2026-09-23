from datetime import datetime, timedelta
from itertools import permutations
import math


AVERAGE_SPEED_KMPH = 30
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6

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
    max_ride_minutes,
    shift_time=None
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

    safety_result = {
        "safe": True,
        "guard_required": False
    }

    if shift_time is not None:

        if is_night_time(shift_time):

            route, safety_result = (
                fix_night_safety(route)
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
        "valid": (
            validation["valid"]
            and safety_result["safe"]
        ),
        "ride_times": validation["ride_times"],
        "invalid_employees": validation[
            "invalid_employees"
        ],
        "night_safe": safety_result["safe"],
        "guard_required": safety_result[
            "guard_required"
        ]
    }


def is_night_time(shift_time):
    """
    Return True if the shift starts during
    configured night hours.

    MySQL TIME may be returned as either
    datetime.time or datetime.timedelta.
    """

    if isinstance(shift_time, timedelta):

        total_seconds = shift_time.total_seconds()

        hour = int(total_seconds // 3600) % 24

    else:

        hour = shift_time.hour

    return (
        hour >= NIGHT_START_HOUR
        or hour < NIGHT_END_HOUR
    )


def violates_night_safety(route):
    """
    Check whether a night route violates
    the women-safety rule.

    If there is only one female employee,
    she must not be the first pickup or
    last drop.
    """

    if not route:
        return False

    female_employees = [
        employee
        for employee in route
        if str(employee.get("gender", "")).strip().lower()
        == "female"
    ]

    # No female employee -> safe
    if len(female_employees) == 0:
        return False

    # With multiple female employees, the
    # current prototype does not consider
    # the route unsafe.
    if len(female_employees) > 1:
        return False

    female_id = female_employees[0]["employee_id"]

    # Only one female employee:
    # she cannot be first or last.
    if route[0]["employee_id"] == female_id:
        return True

    if route[-1]["employee_id"] == female_id:
        return True

    return False


def fix_night_safety(route):
    """
    Try to find a safe ordering for a night route.

    Cab capacity is limited to 4 or 6, so checking
    all permutations is practical for this prototype.
    """

    if not route:
        return route, {
            "safe": True,
            "guard_required": False
        }

    # Check current route first.
    if not violates_night_safety(route):

        return route, {
            "safe": True,
            "guard_required": False
        }

    # Try every possible ordering.
    for candidate in permutations(route):

        candidate = list(candidate)

        if not violates_night_safety(candidate):

            return candidate, {
                "safe": True,
                "guard_required": False
            }

    # No safe ordering exists.
    return route, {
        "safe": False,
        "guard_required": True
    }


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