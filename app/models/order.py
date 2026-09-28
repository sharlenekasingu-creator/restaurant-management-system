from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from app.models.customer import Customer
from app.models.menu import MenuItem


@dataclass
class OrderItem:
    """Represents one menu item within an order."""

    menu_item: MenuItem
    quantity: int
    order_item_id: Optional[int] = None

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Order item quantity must be greater than zero.")

    @property
    def subtotal(self) -> Decimal:
        """Calculate the subtotal for this order item."""
        return self.menu_item.price * self.quantity


@dataclass
class Order:
    """Represents a customer order."""

    customer: Customer
    order_id: Optional[int] = None
    status: str = "Pending"
    items: List[OrderItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.status = self.status.strip()

        if not self.status:
            raise ValueError("Order status cannot be empty.")

    def add_item(self, order_item: OrderItem) -> None:
        """Add an item to the order."""
        self.items.append(order_item)

    def remove_item(self, order_item: OrderItem) -> None:
        """Remove an item from the order."""
        self.items.remove(order_item)

    def calculate_total(self) -> Decimal:
        """Calculate the total value of the order."""
        return sum(
            (item.subtotal for item in self.items),
            Decimal("0.00")
        )

    def update_status(self, status: str) -> None:
        """Update the order status."""
        status = status.strip()

        if not status:
            raise ValueError("Order status cannot be empty.")

        self.status = status