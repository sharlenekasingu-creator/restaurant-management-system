from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.business.authorization_service import AuthorizationError
from app.business.inventory_service import InventoryService
from app.models.inventory import Inventory
from app.data_access.database import DatabaseManager
from app.data_access.repositories import (
    InventoryRepository,
    RoleRepository,
    SupplierRepository,
    UserRepository,
)
from app.exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
    ValidationError,
)
from app.models.user import Role, User, UserSession
from app.models.inventory import Inventory
from app.config.inventory_config import InventorySettings


class TestInventoryManagement(unittest.TestCase):
    """Integration tests for Phase 11 inventory management."""

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "inventory_test.db"

        self.database = DatabaseManager(str(database_path))
        self.database.initialize_database(seed=False)

        self.inventory_repository = InventoryRepository(self.database)
        self.supplier_repository = SupplierRepository(self.database)
        self.role_repository = RoleRepository(self.database)
        self.user_repository = UserRepository(self.database)

        self.admin_session = self._create_session("Administrator", "admin")
        self.manager_session = self._create_session("Manager", "manager")
        self.staff_session = self._create_session("Staff/Cashier", "staff")

        self.service = InventoryService(
            inventory_repository=self.inventory_repository,
            supplier_repository=self.supplier_repository,
            settings=InventorySettings(low_stock_threshold=10),
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def _create_session(
        self,
        role_name: str,
        username: str,
    ) -> UserSession:
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

    # ------------------------------------------------------------
    # SUPPLIER OPERATIONS
    # ------------------------------------------------------------

    def test_supplier_create_update_read_delete(self) -> None:
        supplier = self.service.create_supplier(
            self.admin_session,
            "Fresh Foods Supplier",
            "12345678",
            "supplier@example.com",
            "Port Moresby",
        )

        self.assertIsNotNone(supplier.supplier_id)
        self.assertEqual(supplier.name, "Fresh Foods Supplier")

        found = self.service.get_supplier(
            self.admin_session,
            supplier.supplier_id,
        )
        self.assertEqual(found.email, "supplier@example.com")

        self.assertTrue(
            self.service.update_supplier(
                self.admin_session,
                supplier.supplier_id,
                "Updated Supplier",
                "87654321",
                "updated@example.com",
                "Lae",
            )
        )

        updated = self.service.get_supplier(
            self.admin_session,
            supplier.supplier_id,
        )
        self.assertEqual(updated.name, "Updated Supplier")
        self.assertEqual(updated.address, "Lae")

        self.assertTrue(
            self.service.delete_supplier(
                self.admin_session,
                supplier.supplier_id,
            )
        )

        with self.assertRaises(ResourceNotFoundError):
            self.service.get_supplier(
                self.admin_session,
                supplier.supplier_id,
            )

    # ------------------------------------------------------------
    # INVENTORY OPERATIONS
    # ------------------------------------------------------------

    def test_inventory_create_and_persistence(self) -> None:
        supplier = self.service.create_supplier(
            self.admin_session,
            "Fresh Foods",
        )

        inventory = self.service.create_inventory_item(
            self.admin_session,
            "Rice",
            50,
            "kg",
            supplier.supplier_id,
        )

        self.assertIsNotNone(inventory.inventory_id)
        self.assertEqual(inventory.quantity, 50)
        self.assertEqual(inventory.supplier.supplier_id, supplier.supplier_id)

        reloaded = self.service.get_inventory(
            self.manager_session,
            inventory.inventory_id,
        )

        self.assertEqual(reloaded.name, "Rice")
        self.assertEqual(reloaded.quantity, 50)
        self.assertEqual(reloaded.supplier.supplier_id, supplier.supplier_id)

    def test_inventory_update(self) -> None:
        inventory = self.service.create_inventory_item(
            self.admin_session,
            "Beef",
            25,
            "kg",
        )

        self.assertTrue(
            self.service.update_inventory(
                self.admin_session,
                inventory.inventory_id,
                "Beef",
                30,
                "kg",
            )
        )

        updated = self.service.get_inventory(
            self.manager_session,
            inventory.inventory_id,
        )
        self.assertEqual(updated.quantity, 30)

    def test_quantity_updates_persist(self) -> None:
        inventory = self.service.create_inventory_item(
            self.admin_session,
            "Rice",
            50,
            "kg",
        )

        added = self.service.add_stock(
            self.admin_session,
            inventory.inventory_id,
            10,
        )
        self.assertEqual(added.quantity, 60)

        removed = self.service.remove_stock(
            self.admin_session,
            inventory.inventory_id,
            15,
        )
        self.assertEqual(removed.quantity, 45)

        persisted = self.inventory_repository.get_by_id(
            inventory.inventory_id
        )
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted.quantity, 45)

    # ------------------------------------------------------------
    # LOW STOCK
    # ------------------------------------------------------------

    def test_low_stock_identification_uses_explicit_threshold(self) -> None:
        low = self.service.create_inventory_item(
            self.admin_session,
            "Rice",
            5,
            "kg",
        )
        normal = self.service.create_inventory_item(
            self.admin_session,
            "Beef",
            20,
            "kg",
        )

        low_stock = self.service.get_low_stock_items(
            self.manager_session
        )

        low_ids = {item.inventory_id for item in low_stock}

        self.assertIn(low.inventory_id, low_ids)
        self.assertNotIn(normal.inventory_id, low_ids)

    def test_low_stock_uses_default_threshold(self) -> None:
        service = InventoryService(
            inventory_repository=self.inventory_repository,
            supplier_repository=self.supplier_repository,
        )

        low = self.inventory_repository.create(
            Inventory(
                name="Rice",
                quantity=10,
                unit="kg",
            )
        )

        normal = self.inventory_repository.create(
            Inventory(
                name="Beef",
                quantity=11,
                unit="kg",
            )
        )

        low_stock = service.get_low_stock_items(
            self.manager_session
        )

        low_ids = {item.inventory_id for item in low_stock}

        self.assertIn(low.inventory_id, low_ids)
        self.assertNotIn(normal.inventory_id, low_ids)
    # ------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------

    def test_invalid_supplier_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_supplier(
                self.admin_session,
                "",
            )

    def test_negative_inventory_quantity_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.create_inventory_item(
                self.admin_session,
                "Rice",
                -1,
                "kg",
            )

    def test_invalid_stock_removal_is_rejected(self) -> None:
        inventory = self.service.create_inventory_item(
            self.admin_session,
            "Rice",
            5,
            "kg",
        )

        with self.assertRaises(BusinessRuleError):
            self.service.remove_stock(
                self.admin_session,
                inventory.inventory_id,
                10,
            )

    # ------------------------------------------------------------
    # AUTHORIZATION
    # ------------------------------------------------------------

    def test_manager_can_monitor_inventory(self) -> None:
        inventory = self.service.create_inventory_item(
            self.admin_session,
            "Rice",
            50,
            "kg",
        )

        visible = self.service.get_inventory(
            self.manager_session,
            inventory.inventory_id,
        )

        self.assertEqual(visible.name, "Rice")

    def test_staff_cannot_manage_inventory(self) -> None:
        with self.assertRaises(AuthorizationError):
            self.service.create_inventory_item(
                self.staff_session,
                "Rice",
                50,
                "kg",
            )

    def test_staff_cannot_monitor_inventory(self) -> None:
        with self.assertRaises(AuthorizationError):
            self.service.get_all_inventory(self.staff_session)


if __name__ == "__main__":
    unittest.main()
