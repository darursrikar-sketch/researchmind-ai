"""
Unit and integration tests for authentication system.
"""
import unittest
import json
from werkzeug.security import generate_password_hash, check_password_hash

from researchmind.storage import storage
from researchmind.web.app import app


class TestAuthentication(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.test_username = "testresearcher"
        self.test_email = "test@researchmind.ai"
        self.test_password = "SecurePassword123!"

        # Clean up if existing
        with storage._get_conn() as conn:
            conn.execute("DELETE FROM users WHERE email = ? OR username = ?", (self.test_email, self.test_username))

    def tearDown(self):
        with storage._get_conn() as conn:
            conn.execute("DELETE FROM users WHERE email = ? OR username = ?", (self.test_email, self.test_username))

    def test_storage_user_creation_and_retrieval(self):
        pwd_hash = generate_password_hash(self.test_password)
        user = storage.create_user(self.test_username, self.test_email, pwd_hash)
        self.assertIsNotNone(user["id"])
        self.assertEqual(user["username"], self.test_username)
        self.assertEqual(user["email"], self.test_email)

        # Retrieve by ID
        by_id = storage.get_user_by_id(user["id"])
        self.assertIsNotNone(by_id)
        self.assertTrue(check_password_hash(by_id["password_hash"], self.test_password))

        # Retrieve by username
        by_user = storage.get_user_by_identifier(self.test_username)
        self.assertIsNotNone(by_user)
        self.assertEqual(by_user["id"], user["id"])

        # Retrieve by email
        by_email = storage.get_user_by_identifier(self.test_email)
        self.assertIsNotNone(by_email)
        self.assertEqual(by_email["id"], user["id"])

    def test_auth_api_flow(self):
        # 1. Sign Up
        res = self.client.post(
            "/api/auth/signup",
            json={"username": self.test_username, "email": self.test_email, "password": self.test_password},
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user"]["username"], self.test_username)

        # 2. Duplicate rejection
        dup_res = self.client.post(
            "/api/auth/signup",
            json={"username": self.test_username, "email": self.test_email, "password": self.test_password},
        )
        self.assertEqual(dup_res.status_code, 409)

        # 3. Check Current User (Session active)
        me_res = self.client.get("/api/auth/me")
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.get_json()["user"]["email"], self.test_email)

        # 4. Sign Out
        out_res = self.client.post("/api/auth/signout")
        self.assertEqual(out_res.status_code, 200)

        # 5. Check Current User (Session cleared)
        me_after = self.client.get("/api/auth/me")
        self.assertIsNone(me_after.get_json()["user"])

        # 6. Sign In with wrong password
        bad_signin = self.client.post(
            "/api/auth/signin",
            json={"identifier": self.test_email, "password": "WrongPassword!"},
        )
        self.assertEqual(bad_signin.status_code, 401)

        # 7. Sign In with correct credentials
        good_signin = self.client.post(
            "/api/auth/signin",
            json={"identifier": self.test_email, "password": self.test_password},
        )
        self.assertEqual(good_signin.status_code, 200)
        self.assertEqual(good_signin.get_json()["user"]["username"], self.test_username)


if __name__ == "__main__":
    unittest.main()
