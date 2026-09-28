from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional


@dataclass
class MenuCategory:
    """Represents a category of menu items."""

    name: str
    category_id: Optional[int] = None
    description: str = ""

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.description = self.description.strip()

        if not self.name:
            raise ValueError("Menu category name cannot be empty.")


@dataclass
class MenuItem:
    """Represents an item available on the restaurant menu."""

    name: str
    price: Decimal
    category: MenuCategory
    item_id: Optional[int] = None
    description: str = ""
    is_available: bool = True

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.description = self.description.strip()

        if not self.name:
            raise ValueError("Menu item name cannot be empty.")

        if self.price < Decimal("0"):
            raise ValueError("Menu item price cannot be negative.")

    def mark_unavailable(self) -> None:
        """Mark the menu item as unavailable."""
        self.is_available = False

    def mark_available(self) -> None:
        """Mark the menu item as available."""
        self.is_available = True


@dataclass
class Menu:
    """Composition of menu categories and menu items."""

    categories: List[MenuCategory] = field(default_factory=list)
    items: List[MenuItem] = field(default_factory=list)

    def add_category(self, category: MenuCategory) -> None:
        self.categories.append(category)

    def add_item(self, item: MenuItem) -> None:
        self.items.append(item)

    def get_available_items(self) -> List[MenuItem]:
        return [item for item in self.items if item.is_available]