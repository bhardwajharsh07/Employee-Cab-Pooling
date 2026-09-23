import unittest

from services.routing import (
    travel_time_minutes,
    calculate_route_distance,
    nearest_neighbour_route,
    validate_max_ride_time,
    build_route
)


class TestRouting(unittest.TestCase):

    def setUp(self):

        self.office = {
            "latitude": 31.2536,
            "longitude": 75.7036
        }

        self.employees = [
            {
                "employee_id": 1,
                "name": "Rahul",
                "latitude": 31.2500,
                "longitude": 75.7000
            },
            {
                "employee_id": 2,
                "name": "Aman",
                "latitude": 31.2505,
                "longitude": 75.7005
            },
            {
                "employee_id": 3,
                "name": "Rohit",
                "latitude": 31.2510,
                "longitude": 75.7010
            },
            {
                "employee_id": 4,
                "name": "Priya",
                "latitude": 31.2515,
                "longitude": 75.7015
            }
        ]


    def test_travel_time(self):

        time = travel_time_minutes(30)

        self.assertEqual(
            time,
            60
        )


    def test_route_is_created(self):

        route = nearest_neighbour_route(
            self.employees,
            self.office
        )

        self.assertEqual(
            len(route),
            4
        )


    def test_route_distance(self):

        route = nearest_neighbour_route(
            self.employees,
            self.office
        )

        distance = calculate_route_distance(
            route,
            self.office
        )

        self.assertGreater(
            distance,
            0
        )


    def test_valid_route(self):

        result = build_route(
            self.employees,
            self.office,
            90
        )

        self.assertTrue(
            result["valid"]
        )


    def test_route_has_all_employees(self):

        result = build_route(
            self.employees,
            self.office,
            90
        )

        employee_ids = [
            employee["employee_id"]
            for employee in result["route"]
        ]

        self.assertEqual(
            sorted(employee_ids),
            [1, 2, 3, 4]
        )


    def test_empty_route(self):

        result = build_route(
            [],
            self.office,
            90
        )

        self.assertTrue(
            result["valid"]
        )

        self.assertEqual(
            result["route"],
            []
        )


def test_route_rejects_max_ride_violation(self):

    far_office = {
        "latitude": 31.5000,
        "longitude": 76.0000
    }

    result = build_route(
        self.employees,
        far_office,
        1
    )

    self.assertFalse(
        result["valid"]
    )

    self.assertGreater(
        len(result["invalid_employees"]),
        0
    )


if __name__ == "__main__":
    unittest.main()