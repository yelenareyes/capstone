import unittest
from copy import deepcopy
from unittest.mock import patch

import app as app_module


SAVED_INTERNSHIP = {
    "title": "Sample saved internship",
    "company": "Example Company",
    "island": "Oahu",
    "major": "MIS",
    "season": "Summer",
    "paid": True,
    "deadline": "2026-12-01",
    "source": "Handshake",
    "url": "https://example.com/internship",
    "id": 1,
}


class SavedActionTests(unittest.TestCase):
    def setUp(self):
        # Keep test account data in memory instead of reading or writing users.json.
        self.users = {
            "student@example.com": {
                "password_hash": "",
                "cart": [],
                "likes": [],
            }
        }
        self.get_users_patch = patch.object(app_module, "get_users", return_value=self.users)
        self.save_users_patch = patch.object(app_module, "save_users")
        self.internships_patch = patch.object(
            app_module.helpers,
            "load_internships",
            side_effect=lambda: [deepcopy(SAVED_INTERNSHIP)],
        )
        self.get_users_patch.start()
        self.save_users = self.save_users_patch.start()
        self.internships_patch.start()
        self.client = app_module.app.test_client()
        # The session email makes this test client act like the saved-in user.
        with self.client.session_transaction() as session:
            session["email"] = "student@example.com"

    def tearDown(self):
        self.get_users_patch.stop()
        self.save_users_patch.stop()
        self.internships_patch.stop()

    def test_add_to_list_does_not_add_duplicates(self):
        self.client.post("/cart/add/1")
        response = self.client.post("/cart/add/1")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.users["student@example.com"]["cart"], [1])

    def test_remove_from_list_removes_internship(self):
        self.users["student@example.com"]["cart"] = [1]

        response = self.client.post("/cart/remove/1")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.users["student@example.com"]["cart"], [])

    def test_like_action_toggles_on_and_off(self):
        self.client.post("/like/1")
        self.assertEqual(self.users["student@example.com"]["likes"], [1])

        response = self.client.post("/like/1")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.users["student@example.com"]["likes"], [])

    def test_saving_without_login_redirects_to_login(self):
        client = app_module.app.test_client()

        response = client.post("/cart/add/1")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_cart_page_displays_saved_internship(self):
        self.users["student@example.com"]["cart"] = [1]

        response = self.client.get("/cart")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Sample saved internship", html)
        self.assertIn("Remove from my list", html)
        self.assertIn("Email my internship list", html)

    def test_liked_page_displays_unlike_action(self):
        self.users["student@example.com"]["likes"] = [1]

        response = self.client.get("/liked")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Sample saved internship", html)
        self.assertIn("Unlike", html)

    def test_empty_cart_shows_empty_message(self):
        response = self.client.get("/cart")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your cart is empty.", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
