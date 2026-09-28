from __future__ import annotations

import sqlite3
import unittest
import tempfile
from pathlib import Path

from app.business.authentication_service import (
    AuthenticationServiceImplementation,
)
from app.business.authorization_service import (
    AuthorizationError,
)
from app.business.customer_service import (
    CustomerService,
)
from app.data_access.repositories import (
    CustomerRepository,
    RoleRepository,
    UserRepository,
)
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)


class TestDatabase:
    """Temporary SQLite database for customer management tests."""

    def __init__(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()

        self.database_path = (
            Path(self._temp_dir.name) / "test.db"
        )

        connection = sqlite3.connect(
            str(self.database_path)
        )

        try:
            connection.execute(
                "PRAGMA foreign_keys = ON"
            )

            connection.executescript(
                """
                CREATE TABLE roles (
                    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    full_name TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 1,

                    FOREIGN KEY (role_id)
                        REFERENCES roles(role_id)
                );

                CREATE TABLE customers (
                    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',

                    FOREIGN KEY (customer_id)
                        REFERENCES customers(customer_id)
                        ON DELETE RESTRICT
                );
                """
            )

            connection.executemany(
                """
                INSERT INTO roles (
                    name,
                    description
                )
                VALUES (?, ?)
                """,
                [
                    (
                        "Administrator",
                        "Full system access",
                    ),
                    (
                        "Manager",
                        "Management access",
                    ),
                    (
                        "Staff/Cashier",
                        "Order and payment access",
                    ),
                ],
            )

            connection.commit()

        finally:
            connection.close()

    def connect(self):
        connection = sqlite3.connect(
            str(self.database_path)
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    def close(self) -> None:
        self._temp_dir.cleanup()


class CustomerManagementTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.database = TestDatabase()

        self.customer_repository = CustomerRepository(
            self.database
        )

        self.user_repository = UserRepository(
            self.database
        )

        self.role_repository = RoleRepository(
            self.database
        )

        self.auth_service = (
            AuthenticationServiceImplementation(
                self.user_repository,
                self.role_repository,
            )
        )

        self.customer_service = CustomerService(
            self.customer_repository
        )

        self.admin_session = self._create_user(
            "admin",
            "Admin123",
            "Administrator",
        )

        self.manager_session = self._create_user(
            "manager",
            "Manager123",
            "Manager",
        )

        self.cashier_session = self._create_user(
            "cashier",
            "Cashier123",
            "Staff/Cashier",
        )

    def tearDown(self) -> None:
        self.database.close()

    # ========================================================
    # HELPER
    # ========================================================

    def _create_user(
        self,
        username: str,
        password: str,
        role: str,
    ):
        self.auth_service.register_user(
            username=username,
            password=password,
            role_name=role,
        )

        return self.auth_service.authenticate(
            username,
            password,
        )

    # ========================================================
    # CREATE
    # ========================================================

    def test_create_customer(self):
        customer = self.customer_service.create_customer(
            self.admin_session,
            "John Smith",
            "70000000",
            "john@example.com",
        )

        self.assertIsNotNone(
            customer.customer_id
        )

        self.assertEqual(
            customer.name,
            "John Smith",
        )

        self.assertEqual(
            customer.phone,
            "70000000",
        )

        self.assertEqual(
            customer.email,
            "john@example.com",
        )

    # ========================================================
    # READ
    # ========================================================

    def test_read_customer(self):
        created = self.customer_service.create_customer(
            self.admin_session,
            "Mary Jones",
            "71111111",
            "mary@example.com",
        )

        customer = self.customer_service.get_customer(
            self.admin_session,
            created.customer_id,
        )

        self.assertEqual(
            customer.name,
            "Mary Jones",
        )

        self.assertEqual(
            customer.phone,
            "71111111",
        )

    def test_get_all_customers(self):
        self.customer_service.create_customer(
            self.admin_session,
            "Customer One",
        )

        self.customer_service.create_customer(
            self.admin_session,
            "Customer Two",
        )

        customers = self.customer_service.get_all_customers(
            self.admin_session
        )

        self.assertEqual(
            len(customers),
            2,
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def test_search_customer(self):
        self.customer_service.create_customer(
            self.admin_session,
            "Peter Jackson",
            "72222222",
            "peter@example.com",
        )

        results = self.customer_service.search_customers(
            self.admin_session,
            "Peter",
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0].name,
            "Peter Jackson",
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def test_update_customer(self):
        customer = self.customer_service.create_customer(
            self.admin_session,
            "Old Name",
            "73333333",
            "old@example.com",
        )

        updated = self.customer_service.update_customer(
            self.admin_session,
            customer.customer_id,
            "New Name",
            "74444444",
            "new@example.com",
        )

        self.assertEqual(
            updated.name,
            "New Name",
        )

        stored = self.customer_service.get_customer(
            self.admin_session,
            customer.customer_id,
        )

        self.assertEqual(
            stored.name,
            "New Name",
        )

        self.assertEqual(
            stored.phone,
            "74444444",
        )

    # ========================================================
    # DELETE
    # ========================================================

    def test_delete_customer(self):
        customer = self.customer_service.create_customer(
            self.admin_session,
            "Delete Me",
        )

        result = self.customer_service.delete_customer(
            self.admin_session,
            customer.customer_id,
        )

        self.assertTrue(result)

        with self.assertRaises(ResourceNotFoundError):
            self.customer_service.get_customer(
                self.admin_session,
                customer.customer_id,
            )

    # ========================================================
    # VALIDATION
    # ========================================================

    def test_empty_customer_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.customer_service.create_customer(
                self.admin_session,
                "",
            )

    def test_invalid_customer_phone_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.customer_service.create_customer(
                self.admin_session,
                "Invalid Phone",
                "ABC123",
            )

    def test_invalid_customer_email_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.customer_service.create_customer(
                self.admin_session,
                "Invalid Email",
                "",
                "invalid-email",
            )

    def test_invalid_customer_id_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.customer_service.get_customer(
                self.admin_session,
                0,
            )

    # ========================================================
    # ROLE AUTHORIZATION
    # ========================================================

    def test_administrator_can_manage_customers(self):
        customer = self.customer_service.create_customer(
            self.admin_session,
            "Administrator Customer",
        )

        self.assertIsNotNone(
            customer.customer_id
        )

    def test_manager_can_manage_customers(self):
        customer = self.customer_service.create_customer(
            self.manager_session,
            "Manager Customer",
        )

        self.assertIsNotNone(
            customer.customer_id
        )

    def test_staff_cannot_create_customer(self):
        with self.assertRaises(AuthorizationError):
            self.customer_service.create_customer(
                self.cashier_session,
                "Staff Customer",
            )

    def test_staff_cannot_view_customers(self):
        with self.assertRaises(AuthorizationError):
            self.customer_service.get_all_customers(
                self.cashier_session
            )

    def test_staff_cannot_search_customers(self):
        with self.assertRaises(AuthorizationError):
            self.customer_service.search_customers(
                self.cashier_session,
                "John",
            )

    def test_unauthenticated_user_cannot_access_customers(self):
        with self.assertRaises(AuthorizationError):
            self.customer_service.get_all_customers(
                None
            )

    # ========================================================
    # PERSISTENCE
    # ========================================================

    def test_customer_persistence(self):
        customer = self.customer_service.create_customer(
            self.admin_session,
            "Persistent Customer",
            "75555555",
            "persistent@example.com",
        )

        new_repository = CustomerRepository(
            self.database
        )

        stored = new_repository.get_by_id(
            customer.customer_id
        )

        self.assertIsNotNone(stored)

        self.assertEqual(
            stored.name,
            "Persistent Customer",
        )

        self.assertEqual(
            stored.phone,
            "75555555",
        )

    # ========================================================
    # DATABASE RELATIONSHIP
    # ========================================================

    def test_customer_with_order_cannot_be_deleted(self):
        customer = self.customer_service.create_customer(
            self.admin_session,
            "Customer With Order",
        )

        connection = self.database.connect()

        try:
            connection.execute(
                """
                INSERT INTO orders (
                    customer_id,
                    status
                )
                VALUES (?, ?)
                """,
                (
                    customer.customer_id,
                    "Pending",
                ),
            )

            connection.commit()

        finally:
            connection.close()

        with self.assertRaises(Exception):
            self.customer_service.delete_customer(
                self.admin_session,
                customer.customer_id,
            )


if __name__ == "__main__":
    unittest.main()