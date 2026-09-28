from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from app.business.authentication_service import AuthenticationServiceImplementation
from app.business.customer_service import CustomerService
from app.business.inventory_service import InventoryService
from app.business.menu_service import MenuService
from app.business.order_service import OrderService, OrderTransaction
from app.business.payment_service import PaymentService
from app.business.reporting_service import BasicReportingService
from app.config.inventory_config import InventorySettings
from app.data_access.database import DatabaseManager
from app.data_access.reporting_repository import ReportingRepository
from app.data_access.repositories import (
    CustomerRepository,
    InventoryRepository,
    MenuCategoryRepository,
    MenuItemRepository,
    OrderItemRepository,
    OrderRepository,
    OrderTransaction as RepositoryOrderTransaction,
    PaymentRepository,
    RoleRepository,
    SupplierRepository,
    UserRepository,
)
from app.models.user import Role, User, UserSession


class TestPhase14DatabaseIntegration(unittest.TestCase):
    """Cross-layer smoke tests using the real SQLite repositories."""

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database = DatabaseManager(
            str(Path(self.temp_directory.name) / "integration.db")
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

        self.menu_service = MenuService(
            MenuCategoryRepository(self.database),
            MenuItemRepository(self.database),
        )
        self.customer_service = CustomerService(
            CustomerRepository(self.database)
        )
        self.inventory_service = InventoryService(
            InventoryRepository(self.database),
            SupplierRepository(self.database),
            InventorySettings(low_stock_threshold=10),
        )
        self.order_service = OrderService(
            OrderRepository(self.database),
            OrderItemRepository(self.database),
            CustomerRepository(self.database),
            MenuItemRepository(self.database),
            RepositoryOrderTransaction(self.database),
        )
        self.payment_service = PaymentService(
            PaymentRepository(self.database)
        )
        self.reporting_service = BasicReportingService(
            ReportingRepository(self.database)
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

    def test_menu_customer_order_payment_inventory_reporting_workflow(self) -> None:
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
            "Main meals",
        )
        item = self.menu_service.create_item(
            self.admin_session,
            "Chicken Rice",
            Decimal("15.00"),
            category.category_id,
        )

        customer = self.customer_service.create_customer(
            self.admin_session,
            "Integration Customer",
            "70000001",
            "integration@example.com",
        )

        order = self.order_service.create_order(
            self.admin_session,
            customer.customer_id,
        )
        self.order_service.add_item(
            self.admin_session,
            order,
            item.item_id,
            2,
        )
        total = self.order_service.calculate_total(
            self.admin_session,
            order,
        )
        self.assertEqual(total, Decimal("30.00"))

        saved_order = self.order_service.save_order(
            self.admin_session,
            order,
        )
        self.assertIsNotNone(saved_order.order_id)

        # Reports treat completed orders as sales. Persist the completed
        # order state before validating menu-performance reporting.
        saved_order.status = "Completed"
        OrderRepository(self.database).update(saved_order)

        payment = self.payment_service.create_payment(
            self.admin_session,
            total,
            "Cash",
            saved_order.order_id,
        )
        self.payment_service.complete_payment(
            self.admin_session,
            payment,
        )

        inventory = self.inventory_service.create_inventory_item(
            self.admin_session,
            "Rice",
            10,
            "kg",
        )
        self.assertEqual(inventory.quantity, 10)

        sales = self.reporting_service.get_sales_report(
            self.manager_session
        )
        orders = self.reporting_service.get_order_report(
            self.manager_session
        )
        menu = self.reporting_service.get_menu_performance_report(
            self.manager_session
        )
        inventory_report = self.reporting_service.get_inventory_report(
            self.manager_session
        )

        self.assertEqual(sales["total_sales"], Decimal("30.00"))
        self.assertEqual(orders["total_orders"], 1)
        self.assertEqual(menu["records"][0]["quantity_sold"], 2)
        self.assertEqual(menu["records"][0]["revenue"], Decimal("30.00"))
        self.assertEqual(inventory_report["low_stock_threshold"], 10)
        self.assertEqual(sum(1 for row in inventory_report["records"] if row["is_low_stock"]), 1)

    def test_database_state_persists_after_service_reloads(self) -> None:
        category = self.menu_service.create_category(
            self.admin_session,
            "Drinks",
        )
        item = self.menu_service.create_item(
            self.admin_session,
            "Soft Drink",
            Decimal("4.00"),
            category.category_id,
        )
        customer = self.customer_service.create_customer(
            self.admin_session,
            "Persistent Customer",
        )

        fresh_menu_repository = MenuItemRepository(self.database)
        fresh_customer_repository = CustomerRepository(self.database)

        persisted_item = fresh_menu_repository.get_by_id(item.item_id)
        persisted_customer = fresh_customer_repository.get_by_id(
            customer.customer_id
        )

        self.assertIsNotNone(persisted_item)
        self.assertEqual(persisted_item.name, "Soft Drink")
        self.assertIsNotNone(persisted_customer)
        self.assertEqual(persisted_customer.name, "Persistent Customer")


if __name__ == "__main__":
    unittest.main()
