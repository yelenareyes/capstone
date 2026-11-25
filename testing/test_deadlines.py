import unittest
from datetime import date
from unittest.mock import patch

import helpers


class DeadlineTests(unittest.TestCase):
    def test_deadline_status_boundaries(self):
        # These values check both sides of each deadline-color cutoff.
        cases = [
            (-1, "passed"),
            (0, "urgent"),
            (14, "urgent"),
            (15, "upcoming"),
            (45, "upcoming"),
            (46, "later"),
        ]

        for days_left, expected_status in cases:
            # subTest reports which cutoff failed without stopping the other checks.
            with self.subTest(days_left=days_left):
                self.assertEqual(helpers.deadline_status(days_left), expected_status)

    def test_add_status_calculates_days_and_readable_date(self):
        item = {"deadline": "2026-12-09"}

        # Freeze today's date so the expected days-left value stays consistent.
        with patch.object(helpers, "date") as mocked_date:
            mocked_date.today.return_value = date(2026, 11, 25)
            result = helpers.add_status(item)

        self.assertEqual(result["days_left"], 14)
        self.assertEqual(result["status"], "urgent")
        self.assertEqual(result["deadline_pretty"], "Dec 9, 2026")


if __name__ == "__main__":
    unittest.main()
