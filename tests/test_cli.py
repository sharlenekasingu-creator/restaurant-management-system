import unittest
from unittest.mock import patch

from app.business.authorization_service import Permission
from app.models.user import Role, User, UserSession
from app.presentation.cli import RestaurantManagementSystem


def make_session(role_name: str) -> UserSession:
    return UserSession(
        user=User(
            username=f"{role_name.lower()}_user",
            password_hash="test-hash",
            role=Role(name=role_name),
            full_name=role_name,
        )
    )


class TestRestaurantManagementSystem(unittest.TestCase):
    """Tests for the integrated command-line application."""

    def test_administrator_main_menu_contains_all_functions(self):
        application = RestaurantManagementSystem(
            session=make_session("Administrator")
        )

        with patch("builtins.print") as mocked_print:
            application.display_menu()

        output = "\n".join(
            str(call.args[0])
            for call in mocked_print.call_args_list
            if call.args
        )

        self.assertIn("Menu Management / View Menu", output)
        self.assertIn("Customer Management", output)
        self.assertIn("Customer Order Management", output)
        self.assertIn("Payment Processing", output)
        self.assertIn("Inventory Management", output)
        self.assertIn("Reporting", output)
        self.assertIn("Logout", output)
        self.assertIn("Exit", output)

    def test_manager_main_menu_hides_payment_and_inventory_changes(self):
        application = RestaurantManagementSystem(
            session=make_session("Manager")
        )

        with patch("builtins.print") as mocked_print:
            application.display_menu()

        output = "\n".join(
            str(call.args[0])
            for call in mocked_print.call_args_list
            if call.args
        )

        self.assertIn("Menu Management / View Menu", output)
        self.assertIn("Customer Management", output)
        self.assertIn("Customer Order Management", output)
        self.assertIn("Inventory Management", output)
        self.assertIn("Reporting", output)
        self.assertNotIn("Payment Processing", output)
        self.assertIn("Logout", output)
        self.assertIn("Exit", output)

    def test_staff_main_menu_only_contains_authorized_functions(self):
        application = RestaurantManagementSystem(
            session=make_session("Staff/Cashier")
        )

        with patch("builtins.print") as mocked_print:
            application.display_menu()

        output = "\n".join(
            str(call.args[0])
            for call in mocked_print.call_args_list
            if call.args
        )

        self.assertIn("Menu Management / View Menu", output)
        self.assertIn("Customer Order Management", output)
        self.assertIn("Payment Processing", output)
        self.assertNotIn("Customer Management", output)
        self.assertNotIn("Inventory Management", output)
        self.assertNotIn("Reporting", output)

    def test_exit_option_shuts_down_application(self):
        application = RestaurantManagementSystem(
            session=make_session("Administrator")
        )

        # Administrator menu order: menu, customers, orders, payments,
        # inventory, reports, logout, exit.
        with patch("builtins.print"):
            application.handle_choice("8")

        self.assertFalse(application._running)
        self.assertTrue(application._session.authenticated)

    def test_logout_invalidates_session_and_stops_cli(self):
        session = make_session("Administrator")
        application = RestaurantManagementSystem(session=session)

        with patch("builtins.print"):
            application.handle_choice("7")

        self.assertFalse(application._running)
        self.assertFalse(session.authenticated)

    def test_invalid_choice_is_rejected(self):
        application = RestaurantManagementSystem(
            session=make_session("Administrator")
        )

        with patch(
            "builtins.input",
            side_effect=["invalid", "8"],
        ):
            with patch("builtins.print"):
                choice = application.get_menu_choice()

        self.assertEqual(choice, "8")

    def test_menu_option_dispatches_to_menu_cli(self):
        application = RestaurantManagementSystem(
            session=make_session("Administrator")
        )

        with patch.object(application, "menu_management_cli") as method:
            application.handle_choice("1")

        method.assert_called_once()

    def test_customer_option_dispatches_to_customer_cli(self):
        application = RestaurantManagementSystem(
            session=make_session("Administrator")
        )

        with patch.object(application, "customer_management_cli") as method:
            application.handle_choice("2")

        method.assert_called_once()

    def test_order_option_dispatches_to_order_cli(self):
        application = RestaurantManagementSystem(
            session=make_session("Administrator")
        )

        with patch.object(application, "order_management_cli") as method:
            application.handle_choice("3")

        method.assert_called_once()

    def test_payment_option_dispatches_to_payment_cli(self):
        application = RestaurantManagementSystem(
            session=make_session("Administrator")
        )

        with patch.object(application, "payment_processing_cli") as method:
            application.handle_choice("4")

        method.assert_called_once()

    def test_inventory_option_dispatches_to_inventory_cli(self):
        application = RestaurantManagementSystem(
            session=make_session("Administrator")
        )

        with patch.object(application, "inventory_management_cli") as method:
            application.handle_choice("5")

        method.assert_called_once()

    def test_reporting_option_dispatches_to_reporting_cli(self):
        application = RestaurantManagementSystem(
            session=make_session("Administrator")
        )

        with patch.object(application, "reporting_cli") as method:
            application.handle_choice("6")

        method.assert_called_once()


if __name__ == "__main__":
    unittest.main()
