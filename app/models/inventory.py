from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.supplier import Supplier


@dataclass
class Inventory:
    """Represents an inventory item."""

    name: str
    quantity: float
    unit: str
    inventory_id: Optional[int] = None
    supplier: Optional[Supplier] = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.unit = self.unit.strip()

        if not self.name:
            raise ValueError("Inventory item name cannot be empty.")

        if self.quantity < 0:
            raise ValueError("Inventory quantity cannot be negative.")

        if not self.unit:
            raise ValueError("Inventory unit cannot be empty.")

    def add_stock(self, quantity: float) -> None:
        """Increase inventory quantity."""
        if quantity <= 0:
            raise ValueError("Quantity to add must be greater than zero.")

        self.quantity += quantity

    def remove_stock(self, quantity: float) -> None:
        """Decrease inventory quantity."""
        if quantity <= 0:
            raise ValueError("Quantity to remove must be greater than zero.")

        if quantity > self.quantity:
            raise ValueError("Insufficient inventory.")

        self.quantity -= quantity