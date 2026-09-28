from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.business.authorization_service import (
    AuthorizationService,
    Permission,
)
from app.data_access.repositories import (
    MenuCategoryRepository,
    MenuItemRepository,
    RepositoryError,
)
from app.exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
    ValidationError,
)
from app.models.menu import MenuCategory, MenuItem
from app.models.user import UserSession
from app.validation.validators import Validator


class MenuService:
    """Business service for menu category and menu item management."""

    def __init__(
        self,
        category_repository: MenuCategoryRepository,
        item_repository: MenuItemRepository,
    ) -> None:
        self._category_repository = category_repository
        self._item_repository = item_repository

    # ========================================================
    # AUTHORIZATION HELPERS
    # ========================================================

    @staticmethod
    def _require_menu_management(
        session: UserSession | None,
    ):
        """Require Administrator or Manager menu permissions."""

        return AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_MENU,
        )

    @staticmethod
    def _require_menu_view(
        session: UserSession | None,
    ):
        """Require an authenticated user who can view the menu."""

        return AuthorizationService.require_permission_for_session(
            session,
            Permission.VIEW_MENU,
        )

    # ========================================================
    # CATEGORY MANAGEMENT
    # ========================================================

    def create_category(
        self,
        session: UserSession | None,
        name: str,
        description: str = "",
    ) -> MenuCategory:
        """Create a new menu category."""

        self._require_menu_management(session)

        name = Validator.required(
            name,
            "Category name",
        )

        description = Validator.optional_string(
            description,
            "Category description",
        )

        existing = self._category_repository.get_by_name(name)

        if existing is not None:
            raise BusinessRuleError(
                f"Menu category '{name}' already exists."
            )

        category = MenuCategory(
            name=name,
            description=description,
        )

        try:
            return self._category_repository.create(category)

        except RepositoryError:
            raise

    def get_category(
        self,
        session: UserSession | None,
        category_id: int,
    ) -> MenuCategory:
        """Retrieve one menu category."""

        self._require_menu_view(session)

        category_id = Validator.positive_integer(
            category_id,
            "Category ID",
        )

        category = self._category_repository.get_by_id(
            category_id
        )

        if category is None:
            raise ResourceNotFoundError(
                f"Menu category with ID {category_id} was not found."
            )

        return category

    def get_all_categories(
        self,
        session: UserSession | None,
    ) -> list[MenuCategory]:
        """Retrieve all menu categories."""

        self._require_menu_view(session)

        return self._category_repository.get_all()

    def update_category(
        self,
        session: UserSession | None,
        category_id: int,
        name: str,
        description: str = "",
    ) -> MenuCategory:
        """Update an existing menu category."""

        self._require_menu_management(session)

        category_id = Validator.positive_integer(
            category_id,
            "Category ID",
        )

        name = Validator.required(
            name,
            "Category name",
        )

        description = Validator.optional_string(
            description,
            "Category description",
        )

        category = self._category_repository.get_by_id(
            category_id
        )

        if category is None:
            raise ResourceNotFoundError(
                f"Menu category with ID {category_id} was not found."
            )

        existing = self._category_repository.get_by_name(name)

        if (
            existing is not None
            and existing.category_id != category_id
        ):
            raise BusinessRuleError(
                f"Menu category '{name}' already exists."
            )

        updated_category = MenuCategory(
            name=name,
            category_id=category_id,
            description=description,
        )

        success = self._category_repository.update(
            updated_category
        )

        if not success:
            raise ResourceNotFoundError(
                f"Menu category with ID {category_id} was not found."
            )

        return updated_category

    def delete_category(
        self,
        session: UserSession | None,
        category_id: int,
    ) -> bool:
        """Delete a menu category."""

        self._require_menu_management(session)

        category_id = Validator.positive_integer(
            category_id,
            "Category ID",
        )

        category = self._category_repository.get_by_id(
            category_id
        )

        if category is None:
            raise ResourceNotFoundError(
                f"Menu category with ID {category_id} was not found."
            )

        items = self._item_repository.get_by_category(
            category_id
        )

        if items:
            raise BusinessRuleError(
                "Cannot delete a category that contains menu items."
            )

        return self._category_repository.delete(
            category_id
        )

    # ========================================================
    # MENU ITEM MANAGEMENT
    # ========================================================

    def create_item(
        self,
        session: UserSession | None,
        name: str,
        price: Decimal,
        category_id: int,
        description: str = "",
        is_available: bool = True,
    ) -> MenuItem:
        """Create a new menu item."""

        self._require_menu_management(session)

        name = Validator.required(
            name,
            "Menu item name",
        )

        description = Validator.optional_string(
            description,
            "Menu item description",
        )

        category_id = Validator.positive_integer(
            category_id,
            "Category ID",
        )

        is_available = Validator.boolean(
            is_available,
            "Availability",
        )

        validated_price = self._validate_price(price)

        category = self._category_repository.get_by_id(
            category_id
        )

        if category is None:
            raise ResourceNotFoundError(
                f"Menu category with ID {category_id} was not found."
            )

        existing_items = self._item_repository.get_by_category(
            category_id
        )

        for existing_item in existing_items:
            if existing_item.name.lower() == name.lower():
                raise BusinessRuleError(
                    f"Menu item '{name}' already exists in "
                    f"category '{category.name}'."
                )

        item = MenuItem(
            name=name,
            price=validated_price,
            category=category,
            description=description,
            is_available=is_available,
        )

        return self._item_repository.create(item)

    def get_item(
        self,
        session: UserSession | None,
        item_id: int,
    ) -> MenuItem:
        """Retrieve one menu item."""

        self._require_menu_view(session)

        item_id = Validator.positive_integer(
            item_id,
            "Menu item ID",
        )

        item = self._item_repository.get_by_id(
            item_id
        )

        if item is None:
            raise ResourceNotFoundError(
                f"Menu item with ID {item_id} was not found."
            )

        return item

    def get_all_items(
        self,
        session: UserSession | None,
    ) -> list[MenuItem]:
        """Retrieve all menu items."""

        self._require_menu_view(session)

        return self._item_repository.get_all()

    def view_menu(
        self,
        session: UserSession | None,
    ) -> list[MenuItem]:
        """
        Return available menu items for authenticated users
        who have permission to view the menu.
        """

        self._require_menu_view(session)

        items = self._item_repository.get_all()

        return [
            item
            for item in items
            if item.is_available
        ]

    def update_item(
        self,
        session: UserSession | None,
        item_id: int,
        name: str,
        price: Decimal,
        category_id: int,
        description: str = "",
        is_available: bool = True,
    ) -> MenuItem:
        """Update an existing menu item."""

        self._require_menu_management(session)

        item_id = Validator.positive_integer(
            item_id,
            "Menu item ID",
        )

        name = Validator.required(
            name,
            "Menu item name",
        )

        description = Validator.optional_string(
            description,
            "Menu item description",
        )

        category_id = Validator.positive_integer(
            category_id,
            "Category ID",
        )

        is_available = Validator.boolean(
            is_available,
            "Availability",
        )

        validated_price = self._validate_price(price)

        existing_item = self._item_repository.get_by_id(
            item_id
        )

        if existing_item is None:
            raise ResourceNotFoundError(
                f"Menu item with ID {item_id} was not found."
            )

        category = self._category_repository.get_by_id(
            category_id
        )

        if category is None:
            raise ResourceNotFoundError(
                f"Menu category with ID {category_id} was not found."
            )

        category_items = self._item_repository.get_by_category(
            category_id
        )

        for item in category_items:
            if (
                item.item_id != item_id
                and item.name.lower() == name.lower()
            ):
                raise BusinessRuleError(
                    f"Menu item '{name}' already exists in "
                    f"category '{category.name}'."
                )

        updated_item = MenuItem(
            name=name,
            price=validated_price,
            category=category,
            item_id=item_id,
            description=description,
            is_available=is_available,
        )

        success = self._item_repository.update(
            updated_item
        )

        if not success:
            raise ResourceNotFoundError(
                f"Menu item with ID {item_id} was not found."
            )

        return updated_item

    def delete_item(
        self,
        session: UserSession | None,
        item_id: int,
    ) -> bool:
        """Delete a menu item."""

        self._require_menu_management(session)

        item_id = Validator.positive_integer(
            item_id,
            "Menu item ID",
        )

        item = self._item_repository.get_by_id(
            item_id
        )

        if item is None:
            raise ResourceNotFoundError(
                f"Menu item with ID {item_id} was not found."
            )

        return self._item_repository.delete(
            item_id
        )

    # ========================================================
    # AVAILABILITY
    # ========================================================

    def make_available(
        self,
        session: UserSession | None,
        item_id: int,
    ) -> MenuItem:
        """Mark a menu item as available."""

        self._require_menu_management(session)

        item = self.get_item(
            session,
            item_id,
        )

        item.mark_available()

        self._item_repository.update(item)

        return item

    def make_unavailable(
        self,
        session: UserSession | None,
        item_id: int,
    ) -> MenuItem:
        """Mark a menu item as unavailable."""

        self._require_menu_management(session)

        item = self.get_item(
            session,
            item_id,
        )

        item.mark_unavailable()

        self._item_repository.update(item)

        return item

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_price(value: Decimal) -> Decimal:
        """Validate and normalize a menu item price."""

        try:
            price = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValidationError(
                "Menu item price must be a valid number."
            ) from exc

        if not price.is_finite():
            raise ValidationError(
                "Menu item price must be a finite number."
            )

        if price < Decimal("0"):
            raise ValidationError(
                "Menu item price cannot be negative."
            )

        return price.quantize(Decimal("0.01"))