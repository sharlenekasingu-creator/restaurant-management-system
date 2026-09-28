from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from app.business.authorization_service import (
    AuthorizationService,
    Permission,
)
from app.data_access.repositories import (
    CustomerRepository,
    MenuItemRepository,
    OrderItemRepository,
    OrderRepository,
)
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.user import UserSession


class OrderTransaction(Protocol):
    """
    Transaction interface required by the order service.

    The existing data-access layer implements this through
    OrderTransaction.create_order_with_items().
    """

    def create_order_with_items(
        self,
        order: Order,
        items: list[OrderItem],
    ) -> Order:
        ...


class OrderServiceError(Exception):
    """Raised when an order business operation fails."""


class OrderService:
    """
    Business logic for customer order management.

    The service coordinates:
    - customers
    - menu items
    - orders
    - order items
    - authorization
    - order totals
    """

    def __init__(
        self,
        order_repository: OrderRepository,
        order_item_repository: OrderItemRepository,
        customer_repository: CustomerRepository,
        menu_item_repository: MenuItemRepository,
        order_transaction: OrderTransaction,
    ) -> None:
        self._order_repository = order_repository
        self._order_item_repository = order_item_repository
        self._customer_repository = customer_repository
        self._menu_item_repository = menu_item_repository
        self._order_transaction = order_transaction

    # ============================================================
    # CUSTOMER OPERATIONS FOR ORDERING
    # ============================================================

    def get_customer(
        self,
        session: UserSession | None,
        customer_id: int,
    ) -> Customer:
        """Retrieve a customer for an order."""

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        if not isinstance(customer_id, int) or isinstance(
            customer_id,
            bool,
        ):
            raise OrderServiceError(
                "Customer ID must be a valid integer."
            )

        if customer_id <= 0:
            raise OrderServiceError(
                "Customer ID must be greater than zero."
            )

        customer = self._customer_repository.get_by_id(
            customer_id
        )

        if customer is None:
            raise OrderServiceError(
                f"Customer with ID {customer_id} was not found."
            )

        return customer

    def create_customer(
        self,
        session: UserSession | None,
        name: str,
        phone: str = "",
        email: str = "",
    ) -> Customer:
        """Create a customer during the order workflow."""

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        if not isinstance(name, str) or not name.strip():
            raise OrderServiceError(
                "Customer name cannot be empty."
            )

        if not isinstance(phone, str):
            raise OrderServiceError(
                "Customer phone must be text."
            )

        if not isinstance(email, str):
            raise OrderServiceError(
                "Customer email must be text."
            )

        customer = Customer(
            name=name.strip(),
            phone=phone.strip(),
            email=email.strip(),
        )

        try:
            return self._customer_repository.create(customer)

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to create customer: {exc}"
            ) from exc

    def get_all_customers(
        self,
        session: UserSession | None,
    ) -> list[Customer]:
        """Return all customers available for order creation."""

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        try:
            return self._customer_repository.get_all()

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to retrieve customers: {exc}"
            ) from exc

    # ============================================================
    # MENU OPERATIONS
    # ============================================================

    def get_available_menu_items(
        self,
        session: UserSession | None,
    ):
        """Return only menu items currently available."""

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        try:
            items = self._menu_item_repository.get_all()

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to retrieve menu items: {exc}"
            ) from exc

        return [
            item
            for item in items
            if item.is_available
        ]

    def get_menu_item(
        self,
        session: UserSession | None,
        item_id: int,
    ):
        """Retrieve and validate an available menu item."""

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        if not isinstance(item_id, int) or isinstance(
            item_id,
            bool,
        ):
            raise OrderServiceError(
                "Menu item ID must be a valid integer."
            )

        if item_id <= 0:
            raise OrderServiceError(
                "Menu item ID must be greater than zero."
            )

        try:
            item = self._menu_item_repository.get_by_id(
                item_id
            )

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to retrieve menu item: {exc}"
            ) from exc

        if item is None:
            raise OrderServiceError(
                f"Menu item with ID {item_id} was not found."
            )

        if not item.is_available:
            raise OrderServiceError(
                f"Menu item '{item.name}' is currently unavailable."
            )

        return item

    # ============================================================
    # ORDER CREATION
    # ============================================================

    def create_order(
        self,
        session: UserSession | None,
        customer_id: int,
    ) -> Order:
        """
        Create a new order in memory for a customer.

        The order is not written to the database until save_order()
        is called. This prevents empty orders from being persisted.
        """

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        if not isinstance(customer_id, int) or isinstance(
            customer_id,
            bool,
        ):
            raise OrderServiceError(
                "Customer ID must be a valid integer."
            )

        if customer_id <= 0:
            raise OrderServiceError(
                "Customer ID must be greater than zero."
            )

        try:
            customer = self._customer_repository.get_by_id(
                customer_id
            )

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to retrieve customer: {exc}"
            ) from exc

        if customer is None:
            raise OrderServiceError(
                f"Customer with ID {customer_id} was not found."
            )

        try:
            return Order(
                customer=customer,
                items=[],
                status="Pending",
            )

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to create order: {exc}"
            ) from exc

    # ============================================================
    # ORDER ITEMS
    # ============================================================

    def add_item(
        self,
        session: UserSession | None,
        order: Order,
        menu_item_id: int,
        quantity: int,
    ) -> OrderItem:
        """
        Add a menu item to an unsaved order.

        The item is added to the order in memory. It is persisted
        together with the order when save_order() is called.
        """

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        if not isinstance(order, Order):
            raise OrderServiceError(
                "A valid Order object is required."
            )

        if order.order_id is not None:
            raise OrderServiceError(
                "This order has already been saved."
            )

        if not isinstance(menu_item_id, int) or isinstance(
            menu_item_id,
            bool,
        ):
            raise OrderServiceError(
                "Menu item ID must be a valid integer."
            )

        if menu_item_id <= 0:
            raise OrderServiceError(
                "Menu item ID must be greater than zero."
            )

        if not isinstance(quantity, int) or isinstance(
            quantity,
            bool,
        ):
            raise OrderServiceError(
                "Quantity must be a whole number."
            )

        if quantity <= 0:
            raise OrderServiceError(
                "Quantity must be greater than zero."
            )

        try:
            menu_item = self._menu_item_repository.get_by_id(
                menu_item_id
            )

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to retrieve menu item: {exc}"
            ) from exc

        if menu_item is None:
            raise OrderServiceError(
                f"Menu item with ID {menu_item_id} was not found."
            )

        if not menu_item.is_available:
            raise OrderServiceError(
                f"Menu item '{menu_item.name}' is currently unavailable."
            )

        try:
            order_item = OrderItem(
                menu_item=menu_item,
                quantity=quantity,
            )

            order.items.append(order_item)

            return order_item

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to add item to order: {exc}"
            ) from exc

    # ============================================================
    # TOTAL CALCULATION
    # ============================================================

    def calculate_item_subtotal(
        self,
        session: UserSession | None,
        order_item: OrderItem,
    ) -> Decimal:
        """Calculate the subtotal for one order item."""

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        if not isinstance(order_item, OrderItem):
            raise OrderServiceError(
                "A valid OrderItem object is required."
            )

        try:
            return order_item.subtotal

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to calculate item subtotal: {exc}"
            ) from exc

    def calculate_total(
        self,
        session: UserSession | None,
        order: Order,
    ) -> Decimal:
        """Calculate the complete order total."""

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        if not isinstance(order, Order):
            raise OrderServiceError(
                "A valid Order object is required."
            )

        try:
            return order.calculate_total()

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to calculate order total: {exc}"
            ) from exc

    # ============================================================
    # ORDER PERSISTENCE
    # ============================================================

    def save_order(
        self,
        session: UserSession | None,
        order: Order,
    ) -> Order:
        """
        Persist the order and all of its items atomically.

        The existing OrderTransaction creates the order and all
        order items inside one database transaction.
        """

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        if not isinstance(order, Order):
            raise OrderServiceError(
                "A valid Order object is required."
            )

        if order.order_id is not None:
            raise OrderServiceError(
                "This order has already been saved."
            )

        if order.customer is None:
            raise OrderServiceError(
                "Order must have a customer."
            )

        if order.customer.customer_id is None:
            raise OrderServiceError(
                "Order must have a valid customer."
            )

        if not order.items:
            raise OrderServiceError(
                "An order must contain at least one item."
            )

        for item in order.items:
            if not isinstance(item, OrderItem):
                raise OrderServiceError(
                    "Order contains an invalid order item."
                )

            if item.menu_item is None:
                raise OrderServiceError(
                    "Every order item must have a menu item."
                )

            if item.menu_item.item_id is None:
                raise OrderServiceError(
                    "Every menu item must have a valid ID."
                )

            if not isinstance(item.quantity, int) or isinstance(
                item.quantity,
                bool,
            ):
                raise OrderServiceError(
                    "Every order item quantity must be a whole number."
                )

            if item.quantity <= 0:
                raise OrderServiceError(
                    "Every order item quantity must be greater than zero."
                )

        try:
            saved_order = (
                self._order_transaction.create_order_with_items(
                    order,
                    order.items,
                )
            )

            return saved_order

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to save order: {exc}"
            ) from exc

    # ============================================================
    # RETRIEVE COMPLETED ORDER
    # ============================================================

    def get_order(
        self,
        session: UserSession | None,
        order_id: int,
    ) -> Order:
        """Retrieve an order and its persisted items."""

        AuthorizationService.require_permission_for_session(
            session,
            Permission.MANAGE_ORDERS,
        )

        if not isinstance(order_id, int) or isinstance(
            order_id,
            bool,
        ):
            raise OrderServiceError(
                "Order ID must be a valid integer."
            )

        if order_id <= 0:
            raise OrderServiceError(
                "Order ID must be greater than zero."
            )

        try:
            order = self._order_repository.get_by_id(
                order_id
            )

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to retrieve order: {exc}"
            ) from exc

        if order is None:
            raise OrderServiceError(
                f"Order with ID {order_id} was not found."
            )

        try:
            items = self._order_item_repository.get_by_order(
                order_id
            )

            order.items = items

            return order

        except Exception as exc:
            raise OrderServiceError(
                f"Unable to retrieve order items: {exc}"
            ) from exc