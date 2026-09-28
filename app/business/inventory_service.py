from __future__ import annotations

from typing import Optional

from app.business.authorization_service import (
    AuthorizationService,
    Permission,
)
from app.data_access.repositories import (
    InventoryRepository,
    RepositoryError,
    SupplierRepository,
)

from app.exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
    ValidationError,
)
from app.models.inventory import Inventory
from app.models.supplier import Supplier
from app.models.user import UserSession
from app.validation.validators import Validator
from app.config.inventory_config import InventorySettings

LOW_STOCK_THRESHOLD = 10


class InventoryServiceError(Exception):
    """Raised when an inventory business operation fails."""


class InventoryService:
    """Business service for supplier and inventory management."""

    def __init__(
        self,
        inventory_repository: InventoryRepository,
        supplier_repository: SupplierRepository,
        settings: Optional[InventorySettings] = None,
    ) -> None:
        self._inventory_repository = inventory_repository
        self._supplier_repository = supplier_repository
        self._settings = settings or InventorySettings()

    # ============================================================
    # SUPPLIER OPERATIONS
    # ============================================================

    def create_supplier(
        self,
        session: UserSession | None,
        name: str,
        phone: str = "",
        email: str = "",
        address: str = "",
    ) -> Supplier:
        self._require_manage(session)

        supplier = Supplier(
            name=Validator.required(name, "Supplier name"),
            phone=Validator.phone(phone, "Phone"),
            email=Validator.email(email, "Email"),
            address=Validator.optional_string(address, "Address"),
        )

        try:
            return self._supplier_repository.create(supplier)
        except RepositoryError:
            raise
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def get_supplier(
        self,
        session: UserSession | None,
        supplier_id: int,
    ) -> Supplier:
        self._require_view(session)
        validated_id = Validator.positive_integer(
            supplier_id,
            "Supplier ID",
        )

        supplier = self._supplier_repository.get_by_id(validated_id)

        if supplier is None:
            raise ResourceNotFoundError(
                f"Supplier with ID {validated_id} was not found."
            )

        return supplier

    def get_all_suppliers(
        self,
        session: UserSession | None,
    ) -> list[Supplier]:
        self._require_view(session)
        return self._supplier_repository.get_all()

    def update_supplier(
        self,
        session: UserSession | None,
        supplier_id: int,
        name: str,
        phone: str = "",
        email: str = "",
        address: str = "",
    ) -> bool:
        self._require_manage(session)

        validated_id = Validator.positive_integer(
            supplier_id,
            "Supplier ID",
        )

        supplier = Supplier(
            name=Validator.required(name, "Supplier name"),
            supplier_id=validated_id,
            phone=Validator.phone(phone, "Phone"),
            email=Validator.email(email, "Email"),
            address=Validator.optional_string(address, "Address"),
        )

        if self._supplier_repository.get_by_id(validated_id) is None:
            raise ResourceNotFoundError(
                f"Supplier with ID {validated_id} was not found."
            )

        return self._supplier_repository.update(supplier)

    def delete_supplier(
        self,
        session: UserSession | None,
        supplier_id: int,
    ) -> bool:
        self._require_manage(session)
        validated_id = Validator.positive_integer(
            supplier_id,
            "Supplier ID",
        )

        if self._supplier_repository.get_by_id(validated_id) is None:
            raise ResourceNotFoundError(
                f"Supplier with ID {validated_id} was not found."
            )

        return self._supplier_repository.delete(validated_id)

    # ============================================================
    # INVENTORY OPERATIONS
    # ============================================================

    def create_inventory_item(
        self,
        session: UserSession | None,
        name: str,
        quantity: float,
        unit: str,
        supplier_id: int | None = None,
    ) -> Inventory:
        self._require_manage(session)

        validated_name = Validator.required(
            name,
            "Inventory item name",
        )
        validated_quantity = Validator.non_negative_number(
            quantity,
            "Inventory quantity",
        )
        validated_unit = Validator.required(
            unit,
            "Inventory unit",
        )

        supplier = self._get_optional_supplier(supplier_id)

        inventory = Inventory(
            name=validated_name,
            quantity=validated_quantity,
            unit=validated_unit,
            supplier=supplier,
        )

        return self._inventory_repository.create(inventory)

    def get_inventory(
        self,
        session: UserSession | None,
        inventory_id: int,
    ) -> Inventory:
        self._require_view(session)
        validated_id = Validator.positive_integer(
            inventory_id,
            "Inventory ID",
        )

        inventory = self._inventory_repository.get_by_id(validated_id)

        if inventory is None:
            raise ResourceNotFoundError(
                f"Inventory item with ID {validated_id} was not found."
            )

        return inventory

    def get_all_inventory(
        self,
        session: UserSession | None,
    ) -> list[Inventory]:
        self._require_view(session)
        return self._inventory_repository.get_all()

    def get_inventory_by_supplier(
        self,
        session: UserSession | None,
        supplier_id: int,
    ) -> list[Inventory]:
        self._require_view(session)
        validated_id = Validator.positive_integer(
            supplier_id,
            "Supplier ID",
        )

        if self._supplier_repository.get_by_id(validated_id) is None:
            raise ResourceNotFoundError(
                f"Supplier with ID {validated_id} was not found."
            )

        return self._inventory_repository.get_by_supplier(validated_id)

    def update_inventory(
        self,
        session: UserSession | None,
        inventory_id: int,
        name: str,
        quantity: float,
        unit: str,
        supplier_id: int | None = None,
    ) -> bool:
        self._require_manage(session)

        validated_id = Validator.positive_integer(
            inventory_id,
            "Inventory ID",
        )
        validated_name = Validator.required(
            name,
            "Inventory item name",
        )
        validated_quantity = Validator.non_negative_number(
            quantity,
            "Inventory quantity",
        )
        validated_unit = Validator.required(
            unit,
            "Inventory unit",
        )

        if self._inventory_repository.get_by_id(validated_id) is None:
            raise ResourceNotFoundError(
                f"Inventory item with ID {validated_id} was not found."
            )

        supplier = self._get_optional_supplier(supplier_id)

        inventory = Inventory(
            name=validated_name,
            quantity=validated_quantity,
            unit=validated_unit,
            inventory_id=validated_id,
            supplier=supplier,
        )

        return self._inventory_repository.update(inventory)

    def add_stock(
        self,
        session: UserSession | None,
        inventory_id: int,
        quantity: float,
    ) -> Inventory:
        self._require_manage(session)

        inventory = self.get_inventory(session, inventory_id)
        validated_quantity = Validator.positive_number(
            quantity,
            "Quantity to add",
        )

        inventory.add_stock(validated_quantity)
        self._inventory_repository.update(inventory)
        return inventory

    def remove_stock(
        self,
        session: UserSession | None,
        inventory_id: int,
        quantity: float,
    ) -> Inventory:
        self._require_manage(session)

        inventory = self.get_inventory(session, inventory_id)
        validated_quantity = Validator.positive_number(
            quantity,
            "Quantity to remove",
        )

        try:
            inventory.remove_stock(validated_quantity)
        except ValueError as exc:
            raise BusinessRuleError(str(exc)) from exc

        self._inventory_repository.update(inventory)
        return inventory

    def get_low_stock_items(
        self,
        session: UserSession | None,
        threshold: float | None = None,
    ) -> list[Inventory]:
        self._require_view(session)

        effective_threshold = (
            threshold
            if threshold is not None
            else (
                self._settings.low_stock_threshold
                if self._settings.low_stock_threshold is not None
                else LOW_STOCK_THRESHOLD
            )
        )

        if effective_threshold is None:
            raise BusinessRuleError(
                "Low-stock threshold is not configured. "
                "Set it explicitly in InventorySettings or "
                "app/config/inventory_config.py."
            )

        validated_threshold = Validator.non_negative_number(
            effective_threshold,
            "Low-stock threshold",
        )

        return [
            item
            for item in self._inventory_repository.get_all()
            if item.quantity <= validated_threshold
        ]

    # ============================================================
    # VALIDATION / AUTHORIZATION HELPERS
    # ============================================================

    @staticmethod
    def _require_manage(session: UserSession | None) -> None:
        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_INVENTORY,
        )

    @staticmethod
    def _require_view(session: UserSession | None) -> None:
        AuthorizationService.require_permission_for_session(
            session,
            Permission.VIEW_INVENTORY,
        )

    def _get_optional_supplier(
        self,
        supplier_id: int | None,
    ) -> Supplier | None:
        if supplier_id is None:
            return None

        validated_id = Validator.positive_integer(
            supplier_id,
            "Supplier ID",
        )

        supplier = self._supplier_repository.get_by_id(validated_id)

        if supplier is None:
            raise ResourceNotFoundError(
                f"Supplier with ID {validated_id} was not found."
            )

        return supplier


# Backwards-compatible aliases for the two domain-level operations
# used by earlier phases. New application code should use the
# session-aware add_stock() and remove_stock() methods above.