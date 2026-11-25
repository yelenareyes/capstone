import unittest
from unittest.mock import patch

from werkzeug.security import check_password_hash, generate_password_hash

import app as app_module


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_registration_page_displays_account_form(self):
        response = self.client.get("/register")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('name="email"', html)
        self.assertIn('name="password"', html)

    def test_register_saves_password_as_hash(self):
        users = {}

        with patch.object(app_module, "get_users", return_value=users):
            with patch.object(
                app_module,
                "generate_password_hash",
                # This system Python lacks scrypt, so the test uses its supported PBKDF2 hash.
                side_effect=lambda password: generate_password_hash(
                    password,
                    method="pbkdf2:sha256",
                ),
            ):
                with patch.object(app_module, "save_users") as save_users:
                    response = self.client.post(
                        "/register",
                        data={"email": "Student@Example.com", "password": "classroom123"},
                    )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")
        saved_users = save_users.call_args.args[0]
        self.assertIn("student@example.com", saved_users)
        self.assertTrue(
            check_password_hash(
                saved_users["student@example.com"]["password_hash"],
                "classroom123",
            )
        )
        self.assertNotEqual(
            saved_users["student@example.com"]["password_hash"],
            "classroom123",
        )

    def test_login_accepts_correct_password(self):
        users = {
            "student@example.com": {
                "password_hash": generate_password_hash(
                    "classroom123",
                    method="pbkdf2:sha256",
                ),
                "cart": [],
                "likes": [],
            }
        }

        with patch.object(app_module, "get_users", return_value=users):
            response = self.client.post(
                "/login",
                data={"email": "student@example.com", "password": "classroom123"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")
        with self.client.session_transaction() as session:
            self.assertEqual(session["email"], "student@example.com")

    def test_login_rejects_incorrect_password(self):
        users = {
            "student@example.com": {
                "password_hash": generate_password_hash(
                    "classroom123",
                    method="pbkdf2:sha256",
                ),
                "cart": [],
                "likes": [],
            }
        }

        with patch.object(app_module, "get_users", return_value=users):
            response = self.client.post(
                "/login",
                data={"email": "student@example.com", "password": "wrong-password"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Email or password is incorrect.", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
