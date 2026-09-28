import unittest

from app.models.user import Role, User, UserSession


class TestUserDomainModel(unittest.TestCase):

    def setUp(self):
        self.role = Role(
            name="Manager",
            description="Restaurant manager"
        )

    def test_role_creation(self):
        self.assertEqual(self.role.name, "Manager")

    def test_user_creation(self):
        user = User(
            username="manager",
            password_hash="hashed_password",
            role=self.role,
            full_name="Restaurant Manager"
        )

        self.assertEqual(user.username, "manager")
        self.assertTrue(user.is_active)

    def test_user_role(self):
        user = User(
            username="manager",
            password_hash="hashed_password",
            role=self.role
        )

        self.assertTrue(user.has_role("manager"))

    def test_user_can_be_deactivated(self):
        user = User(
            username="manager",
            password_hash="hashed_password",
            role=self.role
        )

        user.deactivate()

        self.assertFalse(user.is_active)

    def test_user_can_be_activated(self):
        user = User(
            username="manager",
            password_hash="hashed_password",
            role=self.role,
            is_active=False
        )

        user.activate()

        self.assertTrue(user.is_active)

    def test_session_logout(self):
        user = User(
            username="manager",
            password_hash="hashed_password",
            role=self.role
        )

        session = UserSession(user)

        session.logout()

        self.assertFalse(session.authenticated)

    def test_empty_username_is_rejected(self):
        with self.assertRaises(ValueError):
            User(
                username="",
                password_hash="hashed_password",
                role=self.role
            )


if __name__ == "__main__":
    unittest.main()