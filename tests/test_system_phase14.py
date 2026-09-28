from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.business.authorization_service import Permission
from app.models.user import Role, User, UserSession
from app.presentation.cli import RestaurantManagementSystem


class TestPhase14SystemCLI(unittest.TestCase):
    """System-level verification of the role-aware CLI."""

    def _session(self, role_name: str) -> UserSession:
        role = Role(name=role_name, description="test role")
        user = User(
            username=role_name.lower(),
            password_hash="test_hash",
            role=role,
            full_name=role_name,
        )
        return UserSession(user=user)

    def test_administrator_sees_all_major_functions(self) -> None:
        app = RestaurantManagementSystem(session=self._session("Administrator"))
        actions = app._main_menu_actions()

        self.assertEqual(
            actions,
            [
                "menu",
                "customers",
                "orders",
                "payments",
                "inventory",
                "reports",
                "logout",
                "exit",
            ],
        )

    def test_manager_cannot_access_payment_or_inventory_changes(self) -> None:
        app = RestaurantManagementSystem(session=self._session("Manager"))
        actions = app._main_menu_actions()

        self.assertIn("reports", actions)
        self.assertIn("inventory", actions)
        self.assertNotIn("payments", actions)

    def test_staff_has_payment_but_not_management_reports(self) -> None:
        app = RestaurantManagementSystem(session=self._session("Staff/Cashier"))
        actions = app._main_menu_actions()

        self.assertIn("menu", actions)
        self.assertIn("orders", actions)
        self.assertIn("payments", actions)
        self.assertNotIn("customers", actions)
        self.assertNotIn("inventory", actions)
        self.assertNotIn("reports", actions)

    def test_unauthenticated_user_has_only_logout_and_exit(self) -> None:
        app = RestaurantManagementSystem()
        self.assertEqual(app._main_menu_actions(), ["logout", "exit"])

    def test_logout_invalidates_session(self) -> None:
        session = self._session("Administrator")
        app = RestaurantManagementSystem(session=session)

        with patch("builtins.print"):
            app.handle_choice(str(len(app._main_menu_actions()) - 1))

        self.assertFalse(app._running)
        self.assertFalse(session.authenticated)

    def test_exit_stops_application(self) -> None:
        app = RestaurantManagementSystem(session=self._session("Administrator"))

        with patch("builtins.print"):
            app.handle_choice(str(len(app._main_menu_actions())))

        self.assertFalse(app._running)

    def test_invalid_main_menu_choice_does_not_dispatch(self) -> None:
        app = RestaurantManagementSystem(session=self._session("Administrator"))
        app.menu_management_cli = MagicMock()
        app.reporting_cli = MagicMock()

        with patch("builtins.print"):
            app.handle_choice("999")

        app.menu_management_cli.assert_not_called()
        app.reporting_cli.assert_not_called()
        self.assertTrue(app._running)

    def test_keyboard_interrupt_shuts_down_cleanly(self) -> None:
        app = RestaurantManagementSystem(session=self._session("Administrator"))

        with patch.object(app, "get_menu_choice", side_effect=KeyboardInterrupt):
            with patch("builtins.print"):
                app.run()

        self.assertFalse(app._running)


if __name__ == "__main__":
    unittest.main()
