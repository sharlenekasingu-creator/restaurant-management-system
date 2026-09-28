from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from app.business.authorization_service import (
    AuthorizationError,
    Permission,
)

from app.business.reporting_service import (
    BasicReportingService,
    ReportingServiceError,
)

from app.data_access.database import DatabaseManager

from app.data_access.reporting_repository import (
    ReportingRepository,
    ReportingRepositoryError,
)

from app.data_access.repositories import (
    RoleRepository,
    UserRepository,
)

from app.models.user import (
    Role,
    User,
    UserSession,
)


class TestReporting(unittest.TestCase):
    """Tests for Phase 12 operational reporting."""

    def setUp(self) -> None:
        """Create an isolated SQLite database for each test."""

        self.temp_dir = tempfile.TemporaryDirectory()

        self.database_path = (
            Path(self.temp_dir.name)
            / "reporting_test.db"
        )

        self.database = DatabaseManager(
            self.database_path
        )

        self.database.initialize_database(
            seed=False
        )

        self.role_repository = RoleRepository(
            self.database
        )

        self.user_repository = UserRepository(
            self.database
        )

        self.repository = ReportingRepository(
            self.database
        )

        self.service = BasicReportingService(
            self.repository
        )

        self.admin_session = self._create_session(
            "Administrator",
            "admin",
        )

        self.manager_session = self._create_session(
            "Manager",
            "manager",
        )

        self.staff_session = self._create_session(
            "Staff/Cashier",
            "staff",
        )

    def _create_session(
        self,
        role_name: str,
        username: str,
    ) -> UserSession:
        """Create a test user session for a specific role."""

        role = self.role_repository.create(
            Role(
                name=role_name,
                description=f"{role_name} role",
            )
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

    def tearDown(self) -> None:
        """Remove the temporary database."""

        self.temp_dir.cleanup()

    # ============================================================
    # DATABASE SETUP
    # ============================================================
    def _insert_test_data(self) -> None:
        """Insert representative reporting data."""

        connection = self.database.connect()

        try:
            connection.execute("PRAGMA foreign_keys = ON")

            connection.executescript(
                """
                INSERT INTO menu_categories
                    (category_id, name)
                VALUES
                    (1, 'Main Meals'),
                    (2, 'Drinks');

                INSERT INTO menu_items
                    (
                        item_id,
                        category_id,
                        name,
                        price,
                        description
                    ) 
                VALUES
                    (
                        1,
                        1,
                        'Chicken Rice',
                        15.00,
                        'Rice with chicken'
                    ),
                    (
                        2,
                        1,
                        'Beef Burger',
                        20.00,
                        'Beef burger'
                    ),
                    (
                        3,
                        2,
                        'Soft Drink',
                        5.00,
                        'Cold drink'
                    );

                INSERT INTO customers
                    (
                        customer_id,
                        name,
                        phone,
                        email
                    )
                VALUES
                    (
                        1,
                        'Test Customer One',
                        '70000001',
                        'customer1@example.com'
                    ),
                    (
                        2,
                        'Test Customer Two',
                        '70000002',
                        'customer2@example.com'
                    ),
                    (
                        3,
                        'Test Customer Three',
                        '70000003',
                        'customer3@example.com'
                    );

                INSERT INTO orders
                    (
                        order_id,
                        customer_id,
                        status
                    )
                VALUES
                    (
                        1,
                        1,
                        'Completed'
                    ),
                    (
                        2,
                        2,
                        'Pending'
                    ),
                    (
                        3,
                        3,
                        'Cancelled'
                    );

                INSERT INTO order_items
                    (
                        order_item_id,
                        order_id,
                        item_id,
                        quantity
                    )
                VALUES
                    (
                        1,
                        1,
                        1,
                        3
                    ),
                    (
                        2,
                        1,
                        2,
                        2
                    ),
                    (
                        3,
                        2,
                        1,
                        1
                    );

                INSERT INTO payments
                    (
                        payment_id,
                        order_id,
                        amount,
                        payment_method,
                        status
                    )
                VALUES
                    (
                        1,
                        1,
                        85.00,
                        'Cash',
                        'Completed'
                    ),
                    (
                        2,
                        2,
                        15.00,
                        'Cash',
                        'Pending'
                    ),
                    (
                        3,
                        3,
                        20.00,
                        'Card',
                        'Failed'
                    );

                INSERT INTO suppliers
                    (
                        supplier_id,
                        name,
                        phone,
                        email,
                        address
                    )
                VALUES
                    (
                        1,
                        'Fresh Foods Supplier',
                        '12345678',
                        'supplier@example.com',
                        'Port Moresby'
                    );

                INSERT INTO inventory
                    (
                        inventory_id,
                        name,
                        quantity,
                        unit,
                        supplier_id
                    )
                VALUES
                    (
                        1,
                        'Rice',
                        50,
                        'kg',
                        1
                    ),
                    (
                        2,
                        'Beef',
                        10,
                        'kg',
                        1
                    ),
                    (
                        3,
                        'Cooking Oil',
                        5,
                        'litres',
                        1
                    ),
                    (
                        4,
                        'Sugar',
                        11,
                        'kg',
                        1
                    );
                """
            )

            connection.commit()

        finally:
            connection.close()
    
    # ============================================================
    # SALES REPORT
    # ============================================================

    def test_sales_report(self) -> None:
        """Completed payments should appear in the sales report."""

        self._insert_test_data()

        report = self.service.get_sales_report(
            self.admin_session
        )

        self.assertEqual(
            len(report["records"]),
            1,
        )

        self.assertEqual(
            report["records"][0]["payment_id"],
            1,
        )

        self.assertEqual(
            report["records"][0]["order_id"],
            1,
        )

        self.assertEqual(
            report["records"][0]["status"],
            "Completed",
        )

        self.assertEqual(
            report["total_sales"],
            85,
        )

    # ============================================================
    # ORDER REPORT
    # ============================================================

    def test_order_report(self) -> None:
        """Orders should be grouped by status."""

        self._insert_test_data()

        report = self.service.get_order_report(
            self.admin_session
        )

        self.assertEqual(
            report["total_orders"],
            3,
        )

        status_counts = {
            record["status"]: record["order_count"]
            for record in report["records"]
        }

        self.assertEqual(
            status_counts["Completed"],
            1,
        )

        self.assertEqual(
            status_counts["Pending"],
            1,
        )

        self.assertEqual(
            status_counts["Cancelled"],
            1,
        )

    # ============================================================
    # MENU PERFORMANCE REPORT
    # ============================================================

    def test_menu_performance_report(self) -> None:
        """Menu sales should calculate quantity and revenue."""

        self._insert_test_data()

        report = (
            self.service.get_menu_performance_report(
                self.admin_session
            )
        )

        records = {
            record["item_name"]: record
            for record in report["records"]
        }

        self.assertIn(
            "Chicken Rice",
            records,
        )

        self.assertEqual(
            records["Chicken Rice"]["quantity_sold"],
            3,
        )

        self.assertEqual(
            records["Chicken Rice"]["revenue"],
            45,
        )

        self.assertEqual(
            records["Beef Burger"]["quantity_sold"],
            2,
        )

        self.assertEqual(
            records["Beef Burger"]["revenue"],
            40,
        )

    # ============================================================
    # INVENTORY REPORT
    # ============================================================

    def test_inventory_report(self) -> None:
        """Inventory report should identify low-stock items."""

        self._insert_test_data()

        report = self.service.get_inventory_report(
            self.admin_session
        )

        records = {
            record["item_name"]: record
            for record in report["records"]
        }

        self.assertEqual(
            report["low_stock_threshold"],
            10,
        )

        self.assertFalse(
            records["Rice"]["is_low_stock"]
        )

        self.assertTrue(
            records["Beef"]["is_low_stock"]
        )

        self.assertTrue(
            records["Cooking Oil"]["is_low_stock"]
        )

        self.assertFalse(
            records["Sugar"]["is_low_stock"]
        )

    def test_inventory_report_threshold_boundary(
        self,
    ) -> None:
        """Quantity 10 is low stock while 11 is not."""

        self._insert_test_data()

        report = self.service.get_inventory_report(
            self.admin_session
        )

        records = {
            record["item_name"]: record
            for record in report["records"]
        }

        self.assertTrue(
            records["Beef"]["is_low_stock"]
        )

        self.assertFalse(
            records["Sugar"]["is_low_stock"]
        )

    # ============================================================
    # EMPTY DATASETS
    # ============================================================

    def test_sales_report_empty_dataset(self) -> None:
        """Sales report should work when no payments exist."""

        report = self.service.get_sales_report(
            self.admin_session
        )

        self.assertEqual(
            report["records"],
            [],
        )

        self.assertEqual(
            report["total_sales"],
            0,
        )

    def test_order_report_empty_dataset(self) -> None:
        """Order report should work when no orders exist."""

        report = self.service.get_order_report(
            self.admin_session
        )

        self.assertEqual(
            report["records"],
            [],
        )

        self.assertEqual(
            report["total_orders"],
            0,
        )

    def test_menu_performance_report_empty_dataset(
        self,
    ) -> None:
        """Menu report should work when no menu items exist."""

        report = (
            self.service.get_menu_performance_report(
                self.admin_session
            )
        )

        self.assertEqual(
            report["records"],
            [],
        )

    def test_inventory_report_empty_dataset(self) -> None:
        """Inventory report should work when inventory is empty."""

        report = self.service.get_inventory_report(
            self.admin_session
        )

        self.assertEqual(
            report["records"],
            [],
        )

        self.assertEqual(
            report["low_stock_threshold"],
            10,
        )

    # ============================================================
    # AUTHORIZATION
    # ============================================================

    def test_administrator_can_view_reports(self) -> None:
        """Administrator should have full report access."""

        self._insert_test_data()

        report = self.service.get_sales_report(
            self.admin_session
        )

        self.assertEqual(
            report["total_sales"],
            85,
        )

    def test_manager_can_view_reports(self) -> None:
        """Manager should be able to view operational reports."""

        self._insert_test_data()

        report = self.service.get_sales_report(
            self.manager_session
        )

        self.assertEqual(
            report["total_sales"],
            85,
        )

    def test_staff_cannot_view_reports(self) -> None:
        """Staff without VIEW_REPORTS must be rejected."""

        with self.assertRaises(AuthorizationError):
            self.service.get_sales_report(
                self.staff_session
            )

    def test_unauthenticated_user_cannot_view_reports(
        self,
    ) -> None:
        """A missing session must not access reports."""

        with self.assertRaises(AuthorizationError):
            self.service.get_sales_report(None)

    # ============================================================
    # DATABASE ERRORS
    # ============================================================

    def test_sales_report_database_error(self) -> None:
        """Database errors should become ReportingServiceError."""

        repository = Mock(
            spec=ReportingRepository
        )

        repository.get_sales_report.side_effect = (
            ReportingRepositoryError(
                "Database unavailable"
            )
        )

        service = BasicReportingService(
            repository
        )

        with self.assertRaises(
            ReportingServiceError
        ):
            service.get_sales_report(
                self.admin_session
            )

    def test_order_report_database_error(self) -> None:
        """Order database errors should be handled."""

        repository = Mock(
            spec=ReportingRepository
        )

        repository.get_order_report.side_effect = (
            ReportingRepositoryError(
                "Database unavailable"
            )
        )

        service = BasicReportingService(
            repository
        )

        with self.assertRaises(
            ReportingServiceError
        ):
            service.get_order_report(
                self.admin_session
            )

    def test_menu_performance_database_error(
        self,
    ) -> None:
        """Menu-report database errors should be handled."""

        repository = Mock(
            spec=ReportingRepository
        )

        repository.get_menu_performance_report.side_effect = (
            ReportingRepositoryError(
                "Database unavailable"
            )
        )

        service = BasicReportingService(
            repository
        )

        with self.assertRaises(
            ReportingServiceError
        ):
            service.get_menu_performance_report(
                self.admin_session
            )

    def test_inventory_report_database_error(
        self,
    ) -> None:
        """Inventory database errors should be handled."""

        repository = Mock(
            spec=ReportingRepository
        )

        repository.get_inventory_report.side_effect = (
            ReportingRepositoryError(
                "Database unavailable"
            )
        )

        service = BasicReportingService(
            repository
        )

        with self.assertRaises(
            ReportingServiceError
        ):
            service.get_inventory_report(
                self.admin_session
            )


if __name__ == "__main__":
    unittest.main()