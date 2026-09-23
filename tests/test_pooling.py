import unittest

from services.pooling import (
    calculate_grid_cell,
    haversine_distance,
    group_employees_into_cabs
)


class TestPooling(unittest.TestCase):

    def setUp(self):

        self.employees = [
            {
                "id": 1,
                "latitude": 31.2500,
                "longitude": 75.7000
            },
            {
                "id": 2,
                "latitude": 31.2505,
                "longitude": 75.7005
            },
            {
                "id": 3,
                "latitude": 31.2510,
                "longitude": 75.7010
            },
            {
                "id": 4,
                "latitude": 31.2515,
                "longitude": 75.7015
            },
            {
                "id": 5,
                "latitude": 31.2520,
                "longitude": 75.7020
            }
        ]


    def test_grid_cell(self):

        cell = calculate_grid_cell(
            31.25,
            75.70
        )

        self.assertIsInstance(
            cell,
            tuple
        )

        self.assertEqual(
            len(cell),
            2
        )


    def test_distance(self):

        distance = haversine_distance(
            31.2500,
            75.7000,
            31.2505,
            75.7005
        )

        self.assertGreater(
            distance,
            0
        )


    def test_cab_capacity(self):

        cabs = group_employees_into_cabs(
            self.employees,
            cab_capacity=4
        )

        for cab in cabs:

            self.assertLessEqual(
                len(cab),
                4
            )


    def test_all_employees_assigned(self):

        cabs = group_employees_into_cabs(
            self.employees,
            cab_capacity=4
        )

        assigned_ids = []

        for cab in cabs:

            for employee in cab:

                assigned_ids.append(
                    employee["id"]
                )

        self.assertEqual(
            sorted(assigned_ids),
            [1, 2, 3, 4, 5]
        )


    def test_empty_input(self):

        cabs = group_employees_into_cabs(
            [],
            cab_capacity=4
        )

        self.assertEqual(
            cabs,
            []
        )


    def test_invalid_capacity(self):

        with self.assertRaises(ValueError):

            group_employees_into_cabs(
                self.employees,
                cab_capacity=5
            )


if __name__ == "__main__":
    unittest.main()