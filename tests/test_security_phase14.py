from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from app.business.authentication_service import (
    AuthenticationError,
    AuthenticationServiceImplementation,
    PasswordHasher,
    RegistrationError,
)
from app.business.authorization_service import AuthorizationError
from app.business.customer_service import CustomerService
from app.business.inventory_service import InventoryService
from app.business.menu_service import MenuService
from app.business.reporting_service import BasicReportingService
from app.business.payment_service import PaymentService
from app.config.inventory_config import InventorySettings
from app.data_access.database import DatabaseManager
from app.data_access.reporting_repository import ReportingRepository
from app.data_access.repositories import (
    CustomerRepository,
    InventoryRepository,
    MenuCategoryRepository,
    MenuItemRepository,
    PaymentRepository,
    RoleRepository,
    SupplierRepository,
    UserRepository,
)
from app.models.user import Role, User, UserSession


class TestPhase14Security(unittest.TestCase):
    """Security and authorization verification for Phase 14."""

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = DatabaseManager(
            str(Path(self.temp_directory.name) / "security.db")
        )
        self.database.initialize_database(seed=False)

        self.role_repository = RoleRepository(self.database)
        self.user_repository = UserRepository(self.database)

        self.admin_session = self._create_session(
            "admin", "Administrator"
        )
        self.manager_session = self._create_session(
            "manager", "Manager"
        )
        self.staff_session = self._create_session(
            "staff", "Staff/Cashier"
        )

        self.auth_service = AuthenticationServiceImplementation(
            self.user_repository,
            self.role_repository,
        )

        self.customer_service = CustomerService(
            CustomerRepository(self.database)
        )
        self.menu_service = MenuService(
            MenuCategoryRepository(self.database),
            MenuItemRepository(self.database),
        )
        self.inventory_service = InventoryService(
            InventoryRepository(self.database),
            SupplierRepository(self.database),
            InventorySettings(low_stock_threshold=10),
        )
        self.reporting_service = BasicReportingService(
            ReportingRepository(self.database)
        )
        self.payment_service = PaymentService(
            PaymentRepository(self.database)
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _create_session(self, username: str, role_name: str) -> UserSession:
        role = self.role_repository.create(
            Role(name=role_name, description=f"{role_name} role")
        )
        user = self.user_repository.create(
            User(
                username=username,
                password_hash="test_hash",
                role=role,
                full_name=username.title(),
            )
        )
        return UserSession(user=user)

    def test_password_is_hashed_and_verified(self) -> None:
        password = "StrongPassword123"
        stored = PasswordHasher.hash_password(password)

        self.assertNotEqual(stored, password)
        self.assertTrue(PasswordHasher.verify_password(password, stored))
        self.assertFalse(PasswordHasher.verify_password("wrong", stored))
        self.assertTrue(stored.startswith("pbkdf2_sha256$"))

    def test_password_hash_uses_unique_salts(self) -> None:
        first = PasswordHasher.hash_password("StrongPassword123")
        second = PasswordHasher.hash_password("StrongPassword123")

        self.assertNotEqual(first, second)
        self.assertTrue(PasswordHasher.verify_password("StrongPassword123", first))
        self.assertTrue(PasswordHasher.verify_password("StrongPassword123", second))

    def test_sql_injection_cannot_bypass_authentication(self) -> None:
        with self.assertRaises(RegistrationError):
            self.auth_service.register_user(
                "' OR '1'='1",
                "StrongPassword123",
                "Administrator",
            )

        with self.assertRaises(AuthenticationError):
            self.auth_service.authenticate(
                "' OR '1'='1",
                "anything",
            )

    def test_sql_injection_is_treated_as_search_text(self) -> None:
        customer = self.customer_service.create_customer(
            self.admin_session,
            "Normal Customer",
            "70000000",
            "normal@example.com",
        )

        results = self.customer_service.search_customers(
            self.admin_session,
            "' OR 1=1 --",
        )

        self.assertEqual(results, [])
        self.assertIsNotNone(customer.customer_id)

    def test_manager_cannot_modify_inventory(self) -> None:
        with self.assertRaises(AuthorizationError):
            self.inventory_service.create_inventory_item(
                self.manager_session,
                "Rice",
                10,
                "kg",
            )

    def test_manager_can_only_monitor_inventory(self) -> None:
        item = self.inventory_service.create_inventory_item(
            self.admin_session,
            "Rice",
            10,
            "kg",
        )

        visible = self.inventory_service.get_inventory(
            self.manager_session,
            item.inventory_id,
        )

        self.assertEqual(visible.quantity, 10)

        with self.assertRaises(AuthorizationError):
            self.inventory_service.add_stock(
                self.manager_session,
                item.inventory_id,
                5,
            )

    def test_staff_cannot_manage_menu(self) -> None:
        with self.assertRaises(AuthorizationError):
            self.menu_service.create_category(
                self.staff_session,
                "Unauthorized",
            )

    def test_staff_cannot_manage_customers(self) -> None:
        with self.assertRaises(AuthorizationError):
            self.customer_service.create_customer(
                self.staff_session,
                "Unauthorized",
            )

    def test_staff_cannot_view_reports(self) -> None:
        with self.assertRaises(AuthorizationError):
            self.reporting_service.get_sales_report(
                self.staff_session
            )

    def test_manager_cannot_process_payment_directly(self) -> None:
        with self.assertRaises(AuthorizationError):
            self.payment_service.create_payment(
                self.manager_session,
                Decimal("10.00"),
                "Cash",
                1,
            )

    def test_unauthenticated_payment_is_rejected(self) -> None:
        with self.assertRaises(AuthorizationError):
            self.payment_service.create_payment(
                None,
                Decimal("10.00"),
                "Cash",
                1,
            )

    def test_invalid_password_is_rejected(self) -> None:
        self.auth_service.register_user(
            "secureuser",
            "StrongPassword123",
            "Administrator",
        )

        with self.assertRaises(AuthenticationError):
            self.auth_service.authenticate(
                "secureuser",
                "WrongPassword123",
            )

    def test_inactive_user_cannot_authenticate(self) -> None:
        user = self.auth_service.register_user(
            "inactiveuser",
            "StrongPassword123",
            "Administrator",
        )
        user.deactivate()
        self.user_repository.update(user)

        with self.assertRaises(AuthenticationError):
            self.auth_service.authenticate(
                "inactiveuser",
                "StrongPassword123",
            )


if __name__ == "__main__":
    unittest.main()
