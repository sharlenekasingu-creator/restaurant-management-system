from __future__ import annotations

import sqlite3
import unittest
from uuid import uuid4

from app.business.authentication_service import (
    AuthenticationError,
    AuthenticationServiceImplementation,
    PasswordHasher,
    RegistrationError,
)

from app.business.authorization_service import (
    AuthorizationError,
    AuthorizationService,
    Permission,
)

from app.data_access.repositories import (
    RoleRepository,
    UserRepository,
)


class TestDatabase:
    """Small SQLite database wrapper for authentication tests."""

    def __init__(self) -> None:
        self.database_uri = (
            f"file:auth_test_{uuid4().hex}?mode=memory&cache=shared"
        )

        # Keep one connection open so the shared in-memory
        # database remains alive.
        self._keeper_connection = sqlite3.connect(
            self.database_uri,
            uri=True,
        )

        self._keeper_connection.row_factory = sqlite3.Row

        self._create_schema()
        self._seed_roles()

    def connect(self) -> sqlite3.Connection:
        """Return a new connection to the shared test database."""

        connection = sqlite3.connect(
            self.database_uri,
            uri=True,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    def _create_schema(self) -> None:
        self._keeper_connection.executescript(
            """
            PRAGMA foreign_keys = ON;

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

            CREATE TABLE menu_categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE menu_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price NUMERIC NOT NULL,
                category_id INTEGER NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                is_available INTEGER NOT NULL DEFAULT 1,

                FOREIGN KEY (category_id)
                    REFERENCES menu_categories(category_id)
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
            );

            CREATE TABLE order_items (
                order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,

                FOREIGN KEY (order_id)
                    REFERENCES orders(order_id),

                FOREIGN KEY (item_id)
                    REFERENCES menu_items(item_id)
            );

            CREATE TABLE payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                amount NUMERIC NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',

                FOREIGN KEY (order_id)
                    REFERENCES orders(order_id)
            );

            CREATE TABLE suppliers (
                supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE inventory (
                inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL,
                supplier_id INTEGER,

                FOREIGN KEY (supplier_id)
                    REFERENCES suppliers(supplier_id)
            );
            """
        )

    def _seed_roles(self) -> None:
        self._keeper_connection.executemany(
            """
            INSERT INTO roles (name, description)
            VALUES (?, ?)
            """,
            [
                (
                    "Administrator",
                    "Full system access",
                ),
                (
                    "Manager",
                    "Management and operational access",
                ),
                (
                    "Staff/Cashier",
                    "Order and payment access",
                ),
            ],
        )

        self._keeper_connection.commit()

    def close(self) -> None:
        """Close the keeper connection."""

        self._keeper_connection.close()


class AuthenticationTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.database = TestDatabase()

        self.user_repository = UserRepository(
            self.database
        )

        self.role_repository = RoleRepository(
            self.database
        )

        self.auth_service = AuthenticationServiceImplementation(
            self.user_repository,
            self.role_repository,
        )

    def tearDown(self) -> None:
        self.database.close()

    def test_password_hash_is_not_plaintext(self):
        password = "Password123"

        password_hash = PasswordHasher.hash_password(
            password
        )

        self.assertNotEqual(
            password_hash,
            password,
        )

        self.assertTrue(
            PasswordHasher.verify_password(
                password,
                password_hash,
            )
        )

        self.assertFalse(
            PasswordHasher.verify_password(
                "WrongPassword",
                password_hash,
            )
        )

    def test_successful_login(self):
        self.auth_service.register_user(
            username="admin",
            password="Admin123",
            role_name="Administrator",
            full_name="System Administrator",
        )

        session = self.auth_service.authenticate(
            "admin",
            "Admin123",
        )

        self.assertTrue(
            session.authenticated
        )

        self.assertEqual(
            session.user.username,
            "admin",
        )

        self.assertEqual(
            session.user.role.name,
            "Administrator",
        )

    def test_failed_login(self):
        self.auth_service.register_user(
            username="admin",
            password="Admin123",
            role_name="Administrator",
        )

        with self.assertRaises(AuthenticationError):
            self.auth_service.authenticate(
                "admin",
                "WrongPassword",
            )

    def test_logout(self):
        self.auth_service.register_user(
            username="admin",
            password="Admin123",
            role_name="Administrator",
        )

        session = self.auth_service.authenticate(
            "admin",
            "Admin123",
        )

        self.assertIsNotNone(
            self.auth_service.get_current_session()
        )

        self.auth_service.logout()

        self.assertFalse(
            session.authenticated
        )

        self.assertIsNone(
            self.auth_service.get_current_session()
        )

    def test_administrator_authorization(self):
        self.auth_service.register_user(
            username="admin",
            password="Admin123",
            role_name="Administrator",
        )

        session = self.auth_service.authenticate(
            "admin",
            "Admin123",
        )

        self.assertTrue(
            AuthorizationService.has_permission(
                session.user,
                Permission.MANAGE_USERS,
            )
        )

        self.assertTrue(
            AuthorizationService.has_permission(
                session.user,
                Permission.MANAGE_SYSTEM_SETTINGS,
            )
        )

        self.assertTrue(
            AuthorizationService.has_permission(
                session.user,
                Permission.VIEW_REPORTS,
            )
        )

    def test_manager_authorization(self):
        self.auth_service.register_user(
            username="manager",
            password="Manager123",
            role_name="Manager",
        )

        session = self.auth_service.authenticate(
            "manager",
            "Manager123",
        )

        self.assertTrue(
            AuthorizationService.has_permission(
                session.user,
                Permission.MANAGE_MENU,
            )
        )

        self.assertTrue(
            AuthorizationService.has_permission(
                session.user,
                Permission.MANAGE_ORDERS,
            )
        )

        self.assertFalse(
            AuthorizationService.has_permission(
                session.user,
                Permission.MANAGE_USERS,
            )
        )

    def test_staff_cashier_authorization(self):
        self.auth_service.register_user(
            username="cashier",
            password="Cashier123",
            role_name="Staff/Cashier",
        )

        session = self.auth_service.authenticate(
            "cashier",
            "Cashier123",
        )

        self.assertTrue(
            AuthorizationService.has_permission(
                session.user,
                Permission.MANAGE_ORDERS,
            )
        )

        self.assertTrue(
            AuthorizationService.has_permission(
                session.user,
                Permission.PROCESS_PAYMENTS,
            )
        )

        self.assertTrue(
            AuthorizationService.has_permission(
                session.user,
                Permission.VIEW_MENU,
            )
        )

        self.assertFalse(
            AuthorizationService.has_permission(
                session.user,
                Permission.MANAGE_USERS,
            )
        )

    def test_unauthorized_access(self):
        self.auth_service.register_user(
            username="manager",
            password="Manager123",
            role_name="Manager",
        )

        session = self.auth_service.authenticate(
            "manager",
            "Manager123",
        )

        with self.assertRaises(AuthorizationError):
            AuthorizationService.require_permission_for_session(
                session,
                Permission.MANAGE_USERS,
            )

    def test_unauthenticated_access(self):
        with self.assertRaises(AuthorizationError):
            AuthorizationService.require_permission_for_session(
                None,
                Permission.VIEW_MENU,
            )

    def test_sql_injection_attempt(self):
        malicious_username = "' OR '1'='1"

        with self.assertRaises(RegistrationError):
            self.auth_service.register_user(
                username=malicious_username,
                password="Password123",
                role_name="Administrator",
            )

        with self.assertRaises(AuthenticationError):
            self.auth_service.authenticate(
                malicious_username,
                "anything",
            )

        users = self.user_repository.get_all()

        self.assertEqual(
            len(users),
            0,
        )

    def test_duplicate_username(self):
        self.auth_service.register_user(
            username="admin",
            password="Admin123",
            role_name="Administrator",
        )

        with self.assertRaises(RegistrationError):
            self.auth_service.register_user(
                username="admin",
                password="Another123",
                role_name="Administrator",
            )

    def test_invalid_role(self):
        with self.assertRaises(RegistrationError):
            self.auth_service.register_user(
                username="testuser",
                password="Password123",
                role_name="SuperUser",
            )


if __name__ == "__main__":
    unittest.main()