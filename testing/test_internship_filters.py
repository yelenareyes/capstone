import unittest
from datetime import date
from unittest.mock import patch

import helpers


def make_internship(**changes):
    # A complete sample record keeps each filter test small and readable.
    item = {
        "title": "Sample internship",
        "company": "Example Company",
        "island": "Oahu",
        "major": "MIS",
        "season": "Summer",
        "paid": True,
        "deadline": "2026-12-10",
        "source": "Handshake",
        "url": "https://example.com/internship",
        "id": 1,
        "status": "urgent",
    }
    item.update(changes)
    return item


class InternshipFilterTests(unittest.TestCase):
    def setUp(self):
        self.filters = {
            "source": "Handshake",
            "major": "MIS",
            "season": "Summer",
            "island": "Oahu",
            "company": "Example Company",
            "paid": "",
            "hide_passed": False,
        }

    def test_matches_selected_filter_values(self):
        item = make_internship()
        fields = ["source", "major", "season", "island", "company"]

        for field in fields:
            with self.subTest(field=field):
                filters = self.filters.copy()
                filters[field] = item[field]
                self.assertTrue(helpers.matches(item, filters))

                filters[field] = "Different value"
                self.assertFalse(helpers.matches(item, filters))

    def test_paid_filter_includes_only_matching_internships(self):
        paid_item = make_internship(paid=True)
        unpaid_item = make_internship(paid=False)

        self.assertTrue(helpers.matches(paid_item, {**self.filters, "paid": "yes"}))
        self.assertFalse(helpers.matches(unpaid_item, {**self.filters, "paid": "yes"}))
        self.assertTrue(helpers.matches(unpaid_item, {**self.filters, "paid": "no"}))
        self.assertFalse(helpers.matches(paid_item, {**self.filters, "paid": "no"}))

    def test_hide_passed_filter_removes_past_deadlines(self):
        filters = {**self.filters, "hide_passed": True}

        self.assertFalse(helpers.matches(make_internship(status="passed"), filters))
        self.assertTrue(helpers.matches(make_internship(status="urgent"), filters))

    def test_filter_results_sort_open_deadlines_before_passed(self):
        internships = [
            make_internship(title="Later", deadline="2026-12-10"),
            make_internship(title="Passed", deadline="2026-11-20"),
            make_internship(title="Soon", deadline="2026-11-30"),
        ]
        empty_filters = {
            "source": "",
            "major": "",
            "season": "",
            "island": "",
            "company": "",
            "paid": "",
            "hide_passed": False,
        }

        with patch.object(helpers, "date") as mocked_date:
            # Use a fixed date to make the deadline ordering repeatable.
            mocked_date.today.return_value = date(2026, 11, 25)
            results = helpers.filter_internships(internships, empty_filters)

        self.assertEqual([item["title"] for item in results], ["Soon", "Later", "Passed"])


if __name__ == "__main__":
    unittest.main()
