from __future__ import annotations

import sqlite3
import unittest
from decimal import Decimal

from app.business.authentication_service import (
    AuthenticationServiceImplementation,
)
from app.business.authorization_service import (
    AuthorizationError,
)
from app.business.menu_service import MenuService
from app.data_access.repositories import (
    MenuCategoryRepository,
    MenuItemRepository,
    RoleRepository,
    UserRepository,
)
from app.exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
    ValidationError,
)


class TestDatabase:
    """Temporary SQLite database wrapper for menu management tests."""

    def __init__(self) -> None:
        import tempfile
        from pathlib import Path

        # Create a temporary directory for the test database.
        self._temp_dir = tempfile.TemporaryDirectory()

        self.database_path = (
            Path(self._temp_dir.name) / "test.db"
        )

        # Create the database and schema.
        connection = sqlite3.connect(
            str(self.database_path)
        )

        connection.row_factory = sqlite3.Row

        try:
            self._create_schema(connection)
            self._seed_roles(connection)
        finally:
            connection.close()

    def connect(self):
        """
        Return a NEW connection to the temporary database.

        This is important because the repositories close their
        connections after each operation.
        """

        connection = sqlite3.connect(
            str(self.database_path)
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    def _create_schema(
        self,
        connection,
    ) -> None:
        connection.executescript(
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
                    ON DELETE RESTRICT,

                CHECK (price >= 0),

                CHECK (is_available IN (0, 1)),

                UNIQUE (name, category_id)
            );
            """
        )

        connection.commit()

    def _seed_roles(
        self,
        connection,
    ) -> None:
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

    def close(self) -> None:
        """
        Clean up the temporary database.

        The repositories create and close their own connections,
        so there is no shared database connection to close here.
        """

        self._temp_dir.cleanup()

class MenuManagementTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.database = TestDatabase()

        self.category_repository = MenuCategoryRepository(
            self.database
        )

        self.item_repository = MenuItemRepository(
            self.database
        )

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

        self.menu_service = MenuService(
            self.category_repository,
            self.item_repository,
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
    # CATEGORY TESTS
    # ========================================================

    def test_create_category(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
            "Main restaurant meals",
        )

        self.assertIsNotNone(
            category.category_id
        )

        self.assertEqual(
            category.name,
            "Main Meals",
        )

    def test_read_category(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Drinks",
            "Cold and hot drinks",
        )

        result = self.menu_service.get_category(
            self.cashier_session,
            category.category_id,
        )

        self.assertEqual(
            result.name,
            "Drinks",
        )

    def test_update_category(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Meals",
        )

        updated = self.menu_service.update_category(
            self.manager_session,
            category.category_id,
            "Main Meals",
            "Updated description",
        )

        self.assertEqual(
            updated.name,
            "Main Meals",
        )

        self.assertEqual(
            updated.description,
            "Updated description",
        )

    def test_delete_category(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Desserts",
        )

        result = self.menu_service.delete_category(
            self.admin_session,
            category.category_id,
        )

        self.assertTrue(result)

        with self.assertRaises(ResourceNotFoundError):
            self.menu_service.get_category(
                self.admin_session,
                category.category_id,
            )

    def test_category_with_items_cannot_be_deleted(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        self.menu_service.create_item(
            self.admin_session,
            "Chicken Rice",
            Decimal("15.00"),
            category.category_id,
        )

        with self.assertRaises(BusinessRuleError):
            self.menu_service.delete_category(
                self.admin_session,
                category.category_id,
            )

    # ========================================================
    # MENU ITEM TESTS
    # ========================================================

    def test_create_menu_item(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        item = self.menu_service.create_item(
            self.admin_session,
            "Chicken Rice",
            Decimal("15.00"),
            category.category_id,
            "Chicken served with rice",
        )

        self.assertIsNotNone(
            item.item_id
        )

        self.assertEqual(
            item.name,
            "Chicken Rice",
        )

        self.assertEqual(
            item.price,
            Decimal("15.00"),
        )

    def test_read_menu_item(self):
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

        result = self.menu_service.get_item(
            self.cashier_session,
            item.item_id,
        )

        self.assertEqual(
            result.name,
            "Soft Drink",
        )

    def test_update_menu_item(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        item = self.menu_service.create_item(
            self.admin_session,
            "Chicken Rice",
            Decimal("15.00"),
            category.category_id,
        )

        updated = self.menu_service.update_item(
            self.manager_session,
            item.item_id,
            "Chicken Rice Large",
            Decimal("18.00"),
            category.category_id,
            "Large chicken rice meal",
        )

        self.assertEqual(
            updated.name,
            "Chicken Rice Large",
        )

        self.assertEqual(
            updated.price,
            Decimal("18.00"),
        )

    def test_delete_menu_item(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        item = self.menu_service.create_item(
            self.admin_session,
            "Beef Burger",
            Decimal("12.00"),
            category.category_id,
        )

        result = self.menu_service.delete_item(
            self.admin_session,
            item.item_id,
        )

        self.assertTrue(result)

        with self.assertRaises(ResourceNotFoundError):
            self.menu_service.get_item(
                self.admin_session,
                item.item_id,
            )

    # ========================================================
    # MENU VIEWING
    # ========================================================

    def test_staff_can_view_menu(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        self.menu_service.create_item(
            self.admin_session,
            "Chicken Rice",
            Decimal("15.00"),
            category.category_id,
        )

        menu = self.menu_service.view_menu(
            self.cashier_session
        )

        self.assertEqual(
            len(menu),
            1,
        )

        self.assertEqual(
            menu[0].name,
            "Chicken Rice",
        )

    def test_unavailable_item_is_not_shown_in_menu(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        item = self.menu_service.create_item(
            self.admin_session,
            "Chicken Rice",
            Decimal("15.00"),
            category.category_id,
        )

        self.menu_service.make_unavailable(
            self.admin_session,
            item.item_id,
        )

        menu = self.menu_service.view_menu(
            self.cashier_session
        )

        self.assertEqual(
            len(menu),
            0,
        )

    # ========================================================
    # ROLE RESTRICTIONS
    # ========================================================

    def test_administrator_can_manage_menu(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        self.assertIsNotNone(
            category.category_id
        )

    def test_manager_can_manage_menu(self):
        category = self.menu_service.create_category(
            self.manager_session,
            "Drinks",
        )

        self.assertIsNotNone(
            category.category_id
        )

    def test_staff_cannot_create_category(self):
        with self.assertRaises(AuthorizationError):
            self.menu_service.create_category(
                self.cashier_session,
                "Restricted",
            )

    def test_staff_cannot_update_category(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        with self.assertRaises(AuthorizationError):
            self.menu_service.update_category(
                self.cashier_session,
                category.category_id,
                "Changed",
            )

    def test_staff_cannot_delete_category(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        with self.assertRaises(AuthorizationError):
            self.menu_service.delete_category(
                self.cashier_session,
                category.category_id,
            )

    def test_staff_cannot_create_menu_item(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        with self.assertRaises(AuthorizationError):
            self.menu_service.create_item(
                self.cashier_session,
                "Chicken Rice",
                Decimal("15.00"),
                category.category_id,
            )

    def test_staff_can_view_categories(self):
        self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        categories = self.menu_service.get_all_categories(
            self.cashier_session
        )

        self.assertEqual(
            len(categories),
            1,
        )

    # ========================================================
    # INVALID INPUT
    # ========================================================

    def test_empty_category_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.menu_service.create_category(
                self.admin_session,
                "",
            )

    def test_negative_menu_price_is_rejected(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        with self.assertRaises(ValidationError):
            self.menu_service.create_item(
                self.admin_session,
                "Invalid Item",
                Decimal("-5.00"),
                category.category_id,
            )

    def test_invalid_category_id_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.menu_service.create_item(
                self.admin_session,
                "Chicken Rice",
                Decimal("15.00"),
                0,
            )

    def test_non_existing_category_is_rejected(self):
        with self.assertRaises(ResourceNotFoundError):
            self.menu_service.create_item(
                self.admin_session,
                "Chicken Rice",
                Decimal("15.00"),
                999,
            )

    # ========================================================
    # DUPLICATE DATA
    # ========================================================

    def test_duplicate_category_is_rejected(self):
        self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        with self.assertRaises(BusinessRuleError):
            self.menu_service.create_category(
                self.admin_session,
                "Main Meals",
            )

    def test_duplicate_item_in_same_category_is_rejected(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        self.menu_service.create_item(
            self.admin_session,
            "Chicken Rice",
            Decimal("15.00"),
            category.category_id,
        )

        with self.assertRaises(BusinessRuleError):
            self.menu_service.create_item(
                self.admin_session,
                "Chicken Rice",
                Decimal("16.00"),
                category.category_id,
            )

    # ========================================================
    # DATABASE PERSISTENCE
    # ========================================================

    def test_category_persistence(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Persistent Category",
        )

        new_repository = MenuCategoryRepository(
            self.database
        )

        stored = new_repository.get_by_id(
            category.category_id
        )

        self.assertIsNotNone(stored)

        self.assertEqual(
            stored.name,
            "Persistent Category",
        )

    def test_menu_item_persistence(self):
        category = self.menu_service.create_category(
            self.admin_session,
            "Main Meals",
        )

        item = self.menu_service.create_item(
            self.admin_session,
            "Persistent Item",
            Decimal("20.00"),
            category.category_id,
        )

        new_repository = MenuItemRepository(
            self.database
        )

        stored = new_repository.get_by_id(
            item.item_id
        )

        self.assertIsNotNone(stored)

        self.assertEqual(
            stored.name,
            "Persistent Item",
        )

        self.assertEqual(
            stored.price,
            Decimal("20"),
        )


if __name__ == "__main__":
    unittest.main()