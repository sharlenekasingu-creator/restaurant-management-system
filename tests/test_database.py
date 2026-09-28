import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.data_access.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Tests for SQLite database initialization."""

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()

        self.database_path = (
            Path(self.temp_directory.name)
            / "test_restaurant.db"
        )

        self.database = DatabaseManager(
            str(self.database_path)
        )

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_database_is_created(self):
        """Database initialization should create the database file."""
        self.database.initialize_database()

        self.assertTrue(
            self.database.database_exists()
        )

    def test_required_tables_are_created(self):
        """All required RMS tables should be created."""
        self.database.initialize_database()

        required_tables = {
            "roles",
            "users",
            "menu_categories",
            "menu_items",
            "customers",
            "orders",
            "order_items",
            "payments",
            "inventory",
            "suppliers",
        }

        connection = self.database.connect()

        try:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = ?
                """,
                ("table",)
            ).fetchall()

        finally:
            connection.close()

        existing_tables = {
            row["name"] for row in rows
        }

        self.assertTrue(
            required_tables.issubset(existing_tables)
        )

    def test_foreign_keys_are_enabled(self):
        """SQLite foreign-key enforcement should be enabled."""
        self.database.initialize_database()

        connection = self.database.connect()

        try:
            result = connection.execute(
                "PRAGMA foreign_keys"
            ).fetchone()

        finally:
            connection.close()

        self.assertEqual(result[0], 1)

    def test_foreign_key_relationship_is_enforced(self):
        """Invalid foreign-key references should be rejected."""
        self.database.initialize_database()

        connection = self.database.connect()

        try:
            with self.assertRaises(
                sqlite3.IntegrityError
            ):
                connection.execute(
                    """
                    INSERT INTO menu_items
                        (name, price, category_id)
                    VALUES (?, ?, ?)
                    """,
                    (
                        "Invalid Item",
                        10.00,
                        999999
                    )
                )

        finally:
            connection.close()

    def test_seed_data_is_created(self):
        """Seed initialization should create sample data."""
        self.database.initialize_database(
            seed=True
        )

        connection = self.database.connect()

        try:
            role_count = connection.execute(
                "SELECT COUNT(*) FROM roles"
            ).fetchone()[0]

            category_count = connection.execute(
                "SELECT COUNT(*) FROM menu_categories"
            ).fetchone()[0]

            item_count = connection.execute(
                "SELECT COUNT(*) FROM menu_items"
            ).fetchone()[0]

            supplier_count = connection.execute(
                "SELECT COUNT(*) FROM suppliers"
            ).fetchone()[0]

            inventory_count = connection.execute(
                "SELECT COUNT(*) FROM inventory"
            ).fetchone()[0]

            customer_count = connection.execute(
                "SELECT COUNT(*) FROM customers"
            ).fetchone()[0]

        finally:
            connection.close()

        self.assertGreaterEqual(
            role_count,
            2
        )

        self.assertGreaterEqual(
            category_count,
            2
        )

        self.assertGreaterEqual(
            item_count,
            3
        )

        self.assertGreaterEqual(
            supplier_count,
            1
        )

        self.assertGreaterEqual(
            inventory_count,
            2
        )

        self.assertGreaterEqual(
            customer_count,
            1
        )

    def test_database_persists_data(self):
        """Data should remain available after closing the connection."""
        self.database.initialize_database(
            seed=True
        )

        connection = self.database.connect()

        try:
            connection.execute(
                """
                INSERT INTO customers
                    (name, phone, email)
                VALUES (?, ?, ?)
                """,
                (
                    "Persistence Test Customer",
                    "11111111",
                    "persist@example.com"
                )
            )

            connection.commit()

        finally:
            connection.close()

        connection = self.database.connect()

        try:
            customer = connection.execute(
                """
                SELECT name
                FROM customers
                WHERE email = ?
                """,
                ("persist@example.com",)
            ).fetchone()

        finally:
            connection.close()

        self.assertIsNotNone(customer)

        self.assertEqual(
            customer["name"],
            "Persistence Test Customer"
        )

    def test_schema_constraints(self):
        """Basic database constraints should be enforced."""
        self.database.initialize_database()

        connection = self.database.connect()

        try:
            with self.assertRaises(
                sqlite3.IntegrityError
            ):
                connection.execute(
                    """
                    INSERT INTO menu_categories (name)
                    VALUES (?)
                    """,
                    ("Main Meals",)
                )

        finally:
            connection.close()

    def test_initialization_without_seed(self):
        """Database can be initialized without sample data."""
        self.database.initialize_database(
            seed=False
        )

        connection = self.database.connect()

        try:
            role_count = connection.execute(
                "SELECT COUNT(*) FROM roles"
            ).fetchone()[0]

            table_count = connection.execute(
                """
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type = ?
                """,
                ("table",)
            ).fetchone()[0]

        finally:
            connection.close()

        self.assertEqual(
            role_count,
            0
        )

        # SQLite creates sqlite_sequence automatically
        # because the schema uses AUTOINCREMENT.
        self.assertGreaterEqual(
            table_count,
            10
        )


if __name__ == "__main__":
    unittest.main()