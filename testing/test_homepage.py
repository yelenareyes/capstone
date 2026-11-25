import unittest
from copy import deepcopy
from datetime import date
from unittest.mock import patch

import app as app_module


SAMPLE_INTERNSHIPS = [
    {
        "title": "Hawaii MIS Internship",
        "company": "Example Company",
        "island": "Oahu",
        "major": "MIS",
        "season": "Summer",
        "paid": True,
        "deadline": "2026-12-01",
        "source": "Handshake",
        "url": "https://example.com/mis",
        "id": 1,
    },
    {
        "title": "Finance Internship",
        "company": "Finance Company",
        "island": "Maui",
        "major": "Finance",
        "season": "Spring",
        "paid": False,
        "deadline": "2027-01-20",
        "source": "LinkedIn",
        "url": "https://example.com/finance",
        "id": 2,
    },
    {
        "title": "Past MIS Internship",
        "company": "Past Company",
        "island": "Oahu",
        "major": "MIS",
        "season": "Fall",
        "paid": True,
        "deadline": "2026-11-20",
        "source": "Handshake",
        "url": "https://example.com/past",
        "id": 3,
    },
]


class HomepageTests(unittest.TestCase):
    def setUp(self):
        # Give each request fresh data because filtering adds deadline details to records.
        self.data_patch = patch.object(
            app_module.helpers,
            "load_internships",
            side_effect=lambda: deepcopy(SAMPLE_INTERNSHIPS),
        )
        self.date_patch = patch.object(app_module.helpers, "date")
        self.data_patch.start()
        mocked_date = self.date_patch.start()
        # A fixed date makes which cards are urgent or passed predictable.
        mocked_date.today.return_value = date(2026, 11, 25)
        self.client = app_module.app.test_client()

    def tearDown(self):
        self.data_patch.stop()
        self.date_patch.stop()

    def test_homepage_displays_internship_cards(self):
        response = self.client.get("/")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Find your next internship", html)
        self.assertIn("Hawaii MIS Internship", html)
        self.assertEqual(html.count('class="internship-card '), 3)

    def test_major_filter_only_shows_matching_internships(self):
        response = self.client.get("/?major=MIS")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Hawaii MIS Internship", html)
        self.assertNotIn("<h3>Finance Internship</h3>", html)
        self.assertEqual(html.count('class="internship-card '), 2)

    def test_hide_passed_filter_hides_past_internships(self):
        response = self.client.get("/?hide_passed=on")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Past MIS Internship", html)
        self.assertEqual(html.count('class="internship-card '), 2)

    def test_paid_filter_shows_unpaid_internships(self):
        response = self.client.get("/?paid=no")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Finance Internship", html)
        self.assertEqual(html.count('class="internship-card '), 1)

    def test_stylesheet_is_available(self):
        response = self.client.get("/static/style.css")
        stylesheet = response.get_data(as_text=True)
        response.close()

        self.assertEqual(response.status_code, 200)
        self.assertIn(".internship-card.urgent", stylesheet)


if __name__ == "__main__":
    unittest.main()
