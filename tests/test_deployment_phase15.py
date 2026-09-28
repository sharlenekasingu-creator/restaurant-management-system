from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.business.authentication_service import AuthenticationServiceImplementation
from app.config.inventory_config import InventorySettings
from app.data_access.database import DatabaseManager
from app.data_access.repositories import RoleRepository, UserRepository
from scripts.backup_database import backup_database
from scripts.restore_database import restore_database, validate_database


class TestPhase15Deployment(unittest.TestCase):
    """Deployment, backup, recovery, and configuration verification."""

    def test_clean_database_initialization_creates_required_tables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "restaurant_management.db"
            database = DatabaseManager(database_path)
            database.initialize_database(seed=True)

            required_tables = {
                "roles",
                "users",
                "menu_categories",
                "menu_items",
                "customers",
                "orders",
                "order_items",
                "payments",
                "suppliers",
                "inventory",
            }

            connection = database.connect()
            try:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = ?",
                        ("table",),
                    )
                }
            finally:
                connection.close()

            self.assertTrue(required_tables.issubset(tables))

    def test_seeded_database_contains_operational_sample_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = DatabaseManager(
                Path(directory) / "restaurant_management.db"
            )
            database.initialize_database(seed=True)

            connection = database.connect()
            try:
                menu_count = connection.execute(
                    "SELECT COUNT(*) FROM menu_items"
                ).fetchone()[0]
                customer_count = connection.execute(
                    "SELECT COUNT(*) FROM customers"
                ).fetchone()[0]
                inventory_count = connection.execute(
                    "SELECT COUNT(*) FROM inventory"
                ).fetchone()[0]
            finally:
                connection.close()

            self.assertGreaterEqual(menu_count, 1)
            self.assertGreaterEqual(customer_count, 1)
            self.assertGreaterEqual(inventory_count, 1)

    def test_password_is_hashed_during_clean_user_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = DatabaseManager(
                Path(directory) / "restaurant_management.db"
            )
            database.initialize_database(seed=True)

            service = AuthenticationServiceImplementation(
                UserRepository(database),
                RoleRepository(database),
            )
            user = service.register_user(
                "deploy_admin",
                "DeployPassword123",
                "Administrator",
            )

            self.assertNotEqual(
                user.password_hash,
                "DeployPassword123",
            )
            session = service.authenticate(
                "deploy_admin",
                "DeployPassword123",
            )
            self.assertTrue(session.authenticated)

    def test_low_stock_default_is_ten(self) -> None:
        self.assertEqual(InventorySettings().low_stock_threshold, 10)

    def test_database_backup_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "restaurant_management.db"
            backup = root / "backup.db"
            restored = root / "restored.db"

            database = DatabaseManager(source)
            database.initialize_database(seed=True)

            backup_database(source, backup)
            validate_database(backup)
            restore_database(backup, restored)
            validate_database(restored)

            connection = sqlite3.connect(str(restored))
            try:
                result = connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]
            finally:
                connection.close()

            self.assertEqual(result, "ok")


if __name__ == "__main__":
    unittest.main()
