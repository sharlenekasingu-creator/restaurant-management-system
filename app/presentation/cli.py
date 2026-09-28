from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.business.authorization_service import (
    AuthorizationError,
    AuthorizationService,
    Permission,
)
from app.business.order_service import OrderService, OrderServiceError
from app.business.payment_service import PaymentService
from app.business.inventory_service import InventoryService
from app.business.menu_service import MenuService
from app.business.customer_service import CustomerService
from app.business.reporting_service import (
    BasicReportingService,
    ReportingServiceError,
)
from app.models.order import Order, OrderItem
from app.models.user import UserSession
from app.exceptions import RMSException
from app.data_access.repositories import RepositoryError


class RestaurantManagementSystem:
    """
    Main command-line interface for the Restaurant Management System.

    The CLI is responsible only for:
    - displaying information
    - collecting user input
    - calling business services
    - displaying results and errors

    Business rules and database operations remain in the service
    and data-access layers.
    """

    SYSTEM_NAME = "Restaurant Management System"

    def __init__(
        self,
        order_service: Optional[OrderService] = None,
        session: Optional[UserSession] = None,
        payment_service: Optional[PaymentService] = None,
        inventory_service: Optional[InventoryService] = None,
        reporting_service: Optional[BasicReportingService] = None,
        menu_service: Optional[MenuService] = None,
        customer_service: Optional[CustomerService] = None,
    ) -> None:
        self._running = True

        # OrderService is injected so the CLI does not contain
        # database or business-layer construction logic.
        self._order_service = order_service

        # The authenticated session is supplied by the application
        # authentication layer.
        self._session = session

        # Existing PaymentService is injected so the CLI does not
        # contain payment persistence or business-layer construction logic.
        self._payment_service = payment_service
        self._inventory_service = inventory_service
        self._reporting_service = reporting_service
        self._menu_service = menu_service
        self._customer_service = customer_service

    # ============================================================
    # APPLICATION / MAIN MENU
    # ============================================================

    def display_welcome(self) -> None:
        """Display the system name."""
        print("=" * 60)
        print(self.SYSTEM_NAME)
        print("=" * 60)

    def _has_permission(self, permission: Permission) -> bool:
        """Return whether the current authenticated user has a permission."""
        if self._session is None:
            return False

        try:
            AuthorizationService.require_permission_for_session(
                self._session,
                permission,
            )
            return True
        except AuthorizationError:
            return False

    def display_menu(self) -> None:
        """Display only the main-menu functions allowed for the current role."""
        print("\nMain Menu")
        option = 1

        if self._has_permission(Permission.MANAGE_MENU) or self._has_permission(Permission.VIEW_MENU):
            print(f"{option}. Menu Management / View Menu")
            option += 1

        if self._has_permission(Permission.VIEW_CUSTOMERS):
            print(f"{option}. Customer Management")
            option += 1

        if self._has_permission(Permission.MANAGE_ORDERS):
            print(f"{option}. Customer Order Management")
            option += 1

        if self._has_permission(Permission.PROCESS_PAYMENTS):
            print(f"{option}. Payment Processing")
            option += 1

        if self._has_permission(Permission.VIEW_INVENTORY):
            print(f"{option}. Inventory Management")
            option += 1

        if self._has_permission(Permission.VIEW_REPORTS):
            print(f"{option}. Reporting")
            option += 1

        print(f"{option}. Logout")
        option += 1
        print(f"{option}. Exit")

    def _main_menu_actions(self) -> list[str]:
        """Build the authorized main-menu action list in display order."""
        actions: list[str] = []

        if self._has_permission(Permission.MANAGE_MENU) or self._has_permission(Permission.VIEW_MENU):
            actions.append("menu")
        if self._has_permission(Permission.VIEW_CUSTOMERS):
            actions.append("customers")
        if self._has_permission(Permission.MANAGE_ORDERS):
            actions.append("orders")
        if self._has_permission(Permission.PROCESS_PAYMENTS):
            actions.append("payments")
        if self._has_permission(Permission.VIEW_INVENTORY):
            actions.append("inventory")
        if self._has_permission(Permission.VIEW_REPORTS):
            actions.append("reports")

        actions.extend(("logout", "exit"))
        return actions

    def get_menu_choice(self) -> str:
        """Get and validate the current role-specific main-menu choice."""
        actions = self._main_menu_actions()
        while True:
            choice = input("Enter your choice: ").strip()

            if choice.isdigit():
                index = int(choice)
                if 1 <= index <= len(actions):
                    return choice

            print(
                "Invalid choice. Please select one of the displayed options."
            )

    def handle_choice(self, choice: str) -> None:
        """Process a role-specific main-menu option."""
        actions = self._main_menu_actions()

        try:
            index = int(choice) - 1
        except (TypeError, ValueError):
            print("Invalid choice. Please select one of the displayed options.")
            return

        if index < 0 or index >= len(actions):
            print("Invalid choice. Please select one of the displayed options.")
            return

        action = actions[index]

        if action == "menu":
            self.menu_management_cli()
        elif action == "customers":
            self.customer_management_cli()
        elif action == "orders":
            self.order_management_cli()
        elif action == "payments":
            self.payment_processing_cli()
        elif action == "inventory":
            self.inventory_management_cli()
        elif action == "reports":
            self.reporting_cli()
        elif action == "logout":
            self._logout()
        elif action == "exit":
            self._shutdown()

    def _logout(self) -> None:
        """End the current session and return control to the application."""
        if self._session is not None:
            self._session.logout()
        self._running = False
        print("\nYou have been logged out successfully.")

    def _shutdown(self) -> None:
        """Cleanly shut down the application."""
        self._running = False

        print(
            "\nThank you for using the "
            "Restaurant Management System."
        )
        print("Application closed.")

    def run(self) -> None:
        """Start and run the command-line application."""
        self.display_welcome()

        try:
            while self._running:
                self.display_menu()
                choice = self.get_menu_choice()
                self.handle_choice(choice)

        except KeyboardInterrupt:
            print("\n\nApplication interrupted by user.")
            self._shutdown()

        except EOFError:
            print("\n\nInput stream closed.")
            self._shutdown()

    # ============================================================
    # SESSION / SERVICE CONFIGURATION
    # ============================================================

    def set_order_service(
        self,
        order_service: OrderService,
    ) -> None:
        """Set the OrderService used by the CLI."""
        self._order_service = order_service

    def set_session(
        self,
        session: UserSession,
    ) -> None:
        """Set the authenticated user session."""
        self._session = session

    def set_payment_service(
        self,
        payment_service: PaymentService,
    ) -> None:
        """Set the existing PaymentService used by the CLI."""
        self._payment_service = payment_service

    def _require_payment_service(self) -> PaymentService:
        """Return the configured PaymentService."""
        if self._payment_service is None:
            raise RuntimeError("Payment service is not configured.")

        return self._payment_service

    def set_inventory_service(
        self,
        inventory_service: InventoryService,
    ) -> None:
        """Set the InventoryService used by the CLI."""
        self._inventory_service = inventory_service

    def _require_inventory_service(self) -> InventoryService:
        """Return the configured InventoryService."""
        if self._inventory_service is None:
            raise RuntimeError("Inventory service is not configured.")

        return self._inventory_service

    def set_reporting_service(
        self,
        reporting_service: BasicReportingService,
    ) -> None:
        """Set the ReportingService used by the CLI."""
        self._reporting_service = reporting_service

    def _require_reporting_service(self) -> BasicReportingService:
        """Return the configured ReportingService."""
        if self._reporting_service is None:
            raise RuntimeError("Reporting service is not configured.")

        return self._reporting_service

    def set_menu_service(
        self,
        menu_service: MenuService,
    ) -> None:
        """Set the MenuService used by the CLI."""
        self._menu_service = menu_service

    def _require_menu_service(self) -> MenuService:
        """Return the configured MenuService."""
        if self._menu_service is None:
            raise RuntimeError("Menu service is not configured.")
        return self._menu_service

    def set_customer_service(
        self,
        customer_service: CustomerService,
    ) -> None:
        """Set the CustomerService used by the CLI."""
        self._customer_service = customer_service

    def _require_customer_service(self) -> CustomerService:
        """Return the configured CustomerService."""
        if self._customer_service is None:
            raise RuntimeError("Customer service is not configured.")
        return self._customer_service

    def _require_order_service(self) -> OrderService:
        """
        Return the configured OrderService.

        The CLI cannot perform order operations without the
        business service.
        """
        if self._order_service is None:
            raise OrderServiceError(
                "Order service is not configured."
            )

        return self._order_service

    def _require_session(self) -> UserSession:
        """
        Return the current authenticated session.

        Authorization is ultimately checked by OrderService.
        """
        if self._session is None:
            raise AuthorizationError(
                "Authentication is required to manage orders."
            )

        return self._session

    # ============================================================
    # MENU MANAGEMENT / VIEWING
    # ============================================================

    def menu_management_cli(self) -> None:
        """Run the role-appropriate menu management/viewing menu."""
        try:
            session = self._require_session()
            service = self._require_menu_service()
            AuthorizationService.require_permission_for_session(
                session,
                Permission.VIEW_MENU,
            )
        except (AuthorizationError, RuntimeError) as exc:
            print(f"Error: {exc}")
            return

        can_manage = self._has_permission(Permission.MANAGE_MENU)

        while True:
            print("\nMenu Management / View Menu")
            print("-" * 40)
            print("1. View menu")
            print("2. View categories")
            if can_manage:
                print("3. Create category")
                print("4. Update category")
                print("5. Delete category")
                print("6. Create menu item")
                print("7. Update menu item")
                print("8. Delete menu item")
                print("9. Change item availability")
                print("10. Return")
            else:
                print("3. Return")

            choice = input("Enter your choice: ").strip()

            try:
                if choice == "1":
                    self.view_menu_cli()
                elif choice == "2":
                    self.view_menu_categories_cli()
                elif can_manage and choice == "3":
                    self.create_menu_category_cli()
                elif can_manage and choice == "4":
                    self.update_menu_category_cli()
                elif can_manage and choice == "5":
                    self.delete_menu_category_cli()
                elif can_manage and choice == "6":
                    self.create_menu_item_cli()
                elif can_manage and choice == "7":
                    self.update_menu_item_cli()
                elif can_manage and choice == "8":
                    self.delete_menu_item_cli()
                elif can_manage and choice == "9":
                    self.change_menu_item_availability_cli()
                elif (can_manage and choice == "10") or (not can_manage and choice == "3"):
                    return
                else:
                    print("Invalid choice. Please select a displayed option.")
            except RMSException as exc:
                print(f"Error: {exc}")

    def view_menu_cli(self) -> None:
        """Display available menu items."""
        try:
            session = self._require_session()
            service = self._require_menu_service()
            items = service.view_menu(session)

            print("\nMenu")
            print("=" * 80)
            if not items:
                print("No available menu items found.")
            else:
                print(f"{'ID':<6}{'Item':<25}{'Category':<20}{'Price':>12}")
                print("-" * 80)
                for item in items:
                    print(
                        f"{item.item_id:<6}"
                        f"{item.name:<25}"
                        f"{item.category.name:<20}"
                        f"{self._format_money(item.price):>12}"
                    )
            print("=" * 80)
        except (RMSException, RuntimeError) as exc:
            print(f"Error: {exc}")

    def view_menu_categories_cli(self) -> None:
        """Display menu categories."""
        try:
            session = self._require_session()
            service = self._require_menu_service()
            categories = service.get_all_categories(session)
            print("\nMenu Categories")
            print("=" * 70)
            if not categories:
                print("No menu categories found.")
            else:
                for category in categories:
                    print(
                        f"ID: {category.category_id} | "
                        f"Name: {category.name} | "
                        f"Description: {category.description}"
                    )
            print("=" * 70)
        except (RMSException, RuntimeError) as exc:
            print(f"Error: {exc}")

    def create_menu_category_cli(self) -> None:
        session = self._require_session()
        service = self._require_menu_service()
        name = input("Category name: ").strip()
        description = input("Description: ").strip()
        category = service.create_category(session, name, description)
        print(f"Category created successfully. ID: {category.category_id}")

    def update_menu_category_cli(self) -> None:
        session = self._require_session()
        service = self._require_menu_service()
        category_id = self._read_positive_integer("Category ID: ")
        current = service.get_category(session, category_id)
        print(f"Current name: {current.name}")
        name = input("New name: ").strip()
        print(f"Current description: {current.description}")
        description = input("New description: ").strip()
        service.update_category(session, category_id, name, description)
        print("Category updated successfully.")

    def delete_menu_category_cli(self) -> None:
        session = self._require_session()
        service = self._require_menu_service()
        category_id = self._read_positive_integer("Category ID: ")
        service.delete_category(session, category_id)
        print("Category deleted successfully.")

    def create_menu_item_cli(self) -> None:
        session = self._require_session()
        service = self._require_menu_service()
        name = input("Menu item name: ").strip()
        price = self._read_decimal("Price: ")
        category_id = self._read_positive_integer("Category ID: ")
        description = input("Description: ").strip()
        available = self._read_yes_no("Available? (y/n): ")
        item = service.create_item(
            session, name, price, category_id, description, available
        )
        print(f"Menu item created successfully. ID: {item.item_id}")

    def update_menu_item_cli(self) -> None:
        session = self._require_session()
        service = self._require_menu_service()
        item_id = self._read_positive_integer("Menu item ID: ")
        current = service.get_item(session, item_id)
        print(f"Current name: {current.name}")
        name = input("New name: ").strip()
        print(f"Current price: {self._format_money(current.price)}")
        price = self._read_decimal("New price: ")
        print(f"Current category ID: {current.category.category_id}")
        category_id = self._read_positive_integer("New category ID: ")
        description = input("New description: ").strip()
        available = self._read_yes_no("Available? (y/n): ")
        service.update_item(
            session, item_id, name, price, category_id, description, available
        )
        print("Menu item updated successfully.")

    def delete_menu_item_cli(self) -> None:
        session = self._require_session()
        service = self._require_menu_service()
        item_id = self._read_positive_integer("Menu item ID: ")
        service.delete_item(session, item_id)
        print("Menu item deleted successfully.")

    def change_menu_item_availability_cli(self) -> None:
        session = self._require_session()
        service = self._require_menu_service()
        item_id = self._read_positive_integer("Menu item ID: ")
        item = service.get_item(session, item_id)
        if item.is_available:
            service.make_unavailable(session, item_id)
            print("Menu item is now unavailable.")
        else:
            service.make_available(session, item_id)
            print("Menu item is now available.")

    # ============================================================
    # CUSTOMER MANAGEMENT
    # ============================================================

    def customer_management_cli(self) -> None:
        """Run customer management for Administrator and Manager."""
        try:
            session = self._require_session()
            service = self._require_customer_service()
            AuthorizationService.require_permission_for_session(
                session,
                Permission.VIEW_CUSTOMERS,
            )
        except (AuthorizationError, RuntimeError) as exc:
            print(f"Error: {exc}")
            return

        while True:
            print("\nCustomer Management")
            print("-" * 40)
            print("1. View customers")
            print("2. Search customers")
            print("3. Create customer")
            print("4. Update customer")
            print("5. Delete customer")
            print("6. Return")

            choice = input("Enter your choice: ").strip()
            try:
                if choice == "1":
                    self.view_customers_cli()
                elif choice == "2":
                    self.search_customers_cli()
                elif choice == "3":
                    self.create_customer_cli()
                elif choice == "4":
                    self.update_customer_cli()
                elif choice == "5":
                    self.delete_customer_cli()
                elif choice == "6":
                    return
                else:
                    print("Invalid choice. Please enter 1 to 6.")
            except RMSException as exc:
                print(f"Error: {exc}")

    def view_customers_cli(self) -> None:
        session = self._require_session()
        service = self._require_customer_service()
        customers = service.get_all_customers(session)
        print("\nCustomer Records")
        print("=" * 80)
        if not customers:
            print("No customers found.")
        else:
            for customer in customers:
                print(
                    f"ID: {customer.customer_id} | "
                    f"Name: {customer.name} | "
                    f"Phone: {customer.phone} | "
                    f"Email: {customer.email}"
                )
        print("=" * 80)

    def search_customers_cli(self) -> None:
        session = self._require_session()
        service = self._require_customer_service()
        term = input("Search term: ").strip()
        customers = service.search_customers(session, term)
        if not customers:
            print("No matching customers found.")
            return
        for customer in customers:
            print(
                f"ID: {customer.customer_id} | "
                f"Name: {customer.name} | "
                f"Phone: {customer.phone} | "
                f"Email: {customer.email}"
            )

    def create_customer_cli(self) -> None:
        session = self._require_session()
        service = self._require_customer_service()
        name = input("Customer name: ").strip()
        phone = input("Phone: ").strip()
        email = input("Email: ").strip()
        customer = service.create_customer(session, name, phone, email)
        print(f"Customer created successfully. ID: {customer.customer_id}")

    def update_customer_cli(self) -> None:
        session = self._require_session()
        service = self._require_customer_service()
        customer_id = self._read_positive_integer("Customer ID: ")
        current = service.get_customer(session, customer_id)
        print(f"Current name: {current.name}")
        name = input("New name: ").strip()
        phone = input("New phone: ").strip()
        email = input("New email: ").strip()
        service.update_customer(session, customer_id, name, phone, email)
        print("Customer updated successfully.")

    def delete_customer_cli(self) -> None:
        session = self._require_session()
        service = self._require_customer_service()
        customer_id = self._read_positive_integer("Customer ID: ")
        service.delete_customer(session, customer_id)
        print("Customer deleted successfully.")

    # ============================================================
    # ORDER MANAGEMENT MENU
    # ============================================================

    def display_order_menu(self) -> None:
        """Display customer order management options."""
        print("\nCustomer Order Management")
        print("-" * 40)
        print("1. Create customer order")
        print("2. View order")
        print("3. Return")

    def get_order_menu_choice(self) -> str:
        """Get and validate an order menu choice."""
        while True:
            choice = input("Enter your choice: ").strip()

            if choice in {"1", "2", "3"}:
                return choice

            print("Invalid choice. Please enter 1, 2 or 3.")

    def order_management_cli(self) -> None:
        """Run the customer order management menu."""

        try:
            self._require_session()
            self._require_order_service()

        except (
            AuthorizationError,
            OrderServiceError,
        ) as exc:
            print(f"Error: {exc}")
            return

        while True:
            self.display_order_menu()
            choice = self.get_order_menu_choice()

            if choice == "1":
                self.create_order_cli()

            elif choice == "2":
                self.view_order_cli()

            elif choice == "3":
                return

    # ============================================================
    # CREATE CUSTOMER ORDER
    # ============================================================

    def create_order_cli(self) -> None:
        """
        Run the complete Phase 9 order workflow.

        Workflow:
        1. Select or create customer
        2. Create order in memory
        3. Display available menu items
        4. Select menu item
        5. Enter quantity
        6. Add item
        7. Calculate subtotal
        8. Add additional items
        9. Calculate total
        10. Save order
        11. Display completed order
        """

        try:
            session = self._require_session()
            service = self._require_order_service()

            # ----------------------------------------------------
            # Step 1: Select or create customer
            # ----------------------------------------------------

            customer = self._select_or_create_customer(
                service,
                session,
            )

            if customer is None:
                print("Order creation cancelled.")
                return

            print(
                f"\nCustomer selected: "
                f"{customer.name} "
                f"(ID: {customer.customer_id})"
            )

            # ----------------------------------------------------
            # Step 2: Create order
            # ----------------------------------------------------

            order = service.create_order(
                session,
                customer.customer_id,
            )

            print("\nOrder created.")
            print(f"Customer: {customer.name}")

            # ----------------------------------------------------
            # Step 3: Add order items
            # ----------------------------------------------------

            while True:
                menu_items = service.get_available_menu_items(
                    session
                )

                if not menu_items:
                    print(
                        "\nNo available menu items were found."
                    )
                    return

                self._display_available_menu_items(
                    menu_items
                )

                item_id = self._read_positive_integer(
                    "\nEnter menu item ID: "
                )

                quantity = self._read_positive_integer(
                    "Enter quantity: "
                )

                try:
                    order_item = service.add_item(
                        session,
                        order,
                        item_id,
                        quantity,
                    )

                    subtotal = service.calculate_item_subtotal(
                        session,
                        order_item,
                    )

                    print(
                        "\nItem added successfully."
                    )
                    print(
                        f"Item: "
                        f"{order_item.menu_item.name}"
                    )
                    print(
                        f"Quantity: "
                        f"{order_item.quantity}"
                    )
                    print(
                        f"Subtotal: "
                        f"{self._format_money(subtotal)}"
                    )

                except (
                    OrderServiceError,
                    AuthorizationError,
                ) as exc:
                    print(f"\nError: {exc}")
                    continue

                # ------------------------------------------------
                # Ask whether another item should be added.
                # ------------------------------------------------

                add_more = self._read_yes_no(
                    "\nAdd another item? (y/n): "
                )

                if not add_more:
                    break

            # ----------------------------------------------------
            # Step 4: Validate that the order contains items
            # ----------------------------------------------------

            if not order.items:
                print(
                    "\nAn order must contain at least one item."
                )
                return

            # ----------------------------------------------------
            # Step 5: Calculate total
            # ----------------------------------------------------

            total = service.calculate_total(
                session,
                order,
            )

            print("\n" + "=" * 60)
            print("ORDER SUMMARY")
            print("=" * 60)

            self._display_order_items(order.items)

            print("-" * 60)
            print(
                f"TOTAL: "
                f"{self._format_money(total)}"
            )

            # ----------------------------------------------------
            # Step 6: Confirm and save
            # ----------------------------------------------------

            save_order = self._read_yes_no(
                "\nSave this order? (y/n): "
            )

            if not save_order:
                print("Order was not saved.")
                return

            saved_order = service.save_order(
                session,
                order,
            )

            # ----------------------------------------------------
            # Step 7: Display completed order
            # ----------------------------------------------------

            print(
                "\nOrder saved successfully."
            )

            self._display_completed_order(
                service,
                session,
                saved_order,
            )

        except (
            OrderServiceError,
            AuthorizationError,
            ValueError,
        ) as exc:
            print(f"\nError: {exc}")

    # ============================================================
    # CUSTOMER SELECTION
    # ============================================================

    def _select_or_create_customer(
        self,
        service: OrderService,
        session: UserSession,
    ):
        """
        Allow the staff member to select an existing customer
        or create a new customer.
        """

        while True:
            print("\nCustomer Selection")
            print("-" * 30)
            print("1. Select existing customer")
            print("2. Create new customer")
            print("3. Cancel")

            choice = input(
                "Enter your choice: "
            ).strip()

            if choice == "1":
                customer = self._select_existing_customer(
                    service,
                    session,
                )

                if customer is not None:
                    return customer

            elif choice == "2":
                return self._create_customer_for_order(
                    service,
                    session,
                )

            elif choice == "3":
                return None

            else:
                print(
                    "Invalid choice. Please enter 1, 2 or 3."
                )

    def _select_existing_customer(
        self,
        service: OrderService,
        session: UserSession,
    ):
        """Display customers and allow one to be selected."""

        try:
            customers = service.get_all_customers(
                session
            )

            if not customers:
                print(
                    "\nNo customers are currently registered."
                )
                return None

            print("\nAvailable Customers")
            print("-" * 60)

            for customer in customers:
                print(
                    f"ID: {customer.customer_id} | "
                    f"Name: {customer.name} | "
                    f"Phone: {customer.phone}"
                )

            customer_id = self._read_positive_integer(
                "\nEnter customer ID: "
            )

            return service.get_customer(
                session,
                customer_id,
            )

        except (
            OrderServiceError,
            AuthorizationError,
        ) as exc:
            print(f"Error: {exc}")
            return None

    def _create_customer_for_order(
        self,
        service: OrderService,
        session: UserSession,
    ):
        """Create a new customer for the current order."""

        print("\nCreate New Customer")
        print("-" * 30)

        name = input(
            "Customer name: "
        ).strip()

        phone = input(
            "Phone: "
        ).strip()

        email = input(
            "Email: "
        ).strip()

        try:
            customer = service.create_customer(
                session,
                name,
                phone,
                email,
            )

            print(
                "\nCustomer created successfully."
            )
            print(
                f"Customer ID: "
                f"{customer.customer_id}"
            )

            return customer

        except (
            OrderServiceError,
            AuthorizationError,
        ) as exc:
            print(f"Error: {exc}")
            return None

    # ============================================================
    # MENU ITEM DISPLAY
    # ============================================================

    @staticmethod
    def _display_available_menu_items(
        menu_items,
    ) -> None:
        """Display currently available menu items."""

        print("\nAvailable Menu Items")
        print("=" * 70)

        print(
            f"{'ID':<6}"
            f"{'Item':<25}"
            f"{'Price':>12}"
            f"  Description"
        )

        print("-" * 70)

        for item in menu_items:
            description = (
                item.description
                if item.description
                else ""
            )

            print(
                f"{item.item_id:<6}"
                f"{item.name:<25}"
                f"{RestaurantManagementSystem._format_money(item.price):>12}"
                f"  {description}"
            )

        print("=" * 70)

    # ============================================================
    # ORDER DISPLAY
    # ============================================================

    @staticmethod
    def _display_order_items(
        items: list[OrderItem],
    ) -> None:
        """Display all items currently belonging to an order."""

        print(
            f"{'Item':<25}"
            f"{'Qty':>8}"
            f"{'Unit Price':>15}"
            f"{'Subtotal':>15}"
        )

        print("-" * 65)

        for item in items:
            print(
                f"{item.menu_item.name:<25}"
                f"{item.quantity:>8}"
                f"{RestaurantManagementSystem._format_money(item.menu_item.price):>15}"
                f"{RestaurantManagementSystem._format_money(item.subtotal):>15}"
            )

    def _display_completed_order(
        self,
        service: OrderService,
        session: UserSession,
        order: Order,
    ) -> None:
        """Display the completed saved order."""

        print("\n" + "=" * 60)
        print("COMPLETED ORDER")
        print("=" * 60)

        print(
            f"Order ID: {order.order_id}"
        )

        print(
            f"Customer ID: "
            f"{order.customer.customer_id}"
        )

        print(
            f"Customer: "
            f"{order.customer.name}"
        )

        print(
            f"Status: "
            f"{order.status}"
        )

        print("-" * 60)

        # Reload the persisted items so the CLI displays the
        # database-backed completed order.
        try:
            persisted_order = service.get_order(
                session,
                order.order_id,
            )

            items = persisted_order.items

            if items:
                self._display_order_items(items)

            total = service.calculate_total(
                session,
                persisted_order,
            )

            print("-" * 60)
            print(
                f"TOTAL: "
                f"{self._format_money(total)}"
            )

        except (
            OrderServiceError,
            AuthorizationError,
        ):
            # The order itself has already been saved.
            # Fall back to the in-memory order if reloading
            # is unavailable.
            self._display_order_items(order.items)

            print("-" * 60)
            print(
                f"TOTAL: "
                f"{self._format_money(order.calculate_total())}"
            )

        print("=" * 60)

    # ============================================================
    # VIEW ORDER
    # ============================================================

    def view_order_cli(self) -> None:
        """View a previously saved order by ID."""

        try:
            session = self._require_session()
            service = self._require_order_service()

            order_id = self._read_positive_integer(
                "\nEnter order ID: "
            )

            order = service.get_order(
                session,
                order_id,
            )

            if order is None:
                print(
                    f"Order {order_id} was not found."
                )
                return

            self._display_completed_order(
                service,
                session,
                order,
            )

        except (
            OrderServiceError,
            AuthorizationError,
        ) as exc:
            print(f"Error: {exc}")

    # ============================================================
    # PAYMENT PROCESSING
    # ============================================================

    def payment_processing_cli(self) -> None:
        """Process a payment for an existing saved order."""

        try:
            session = self._require_session()
            order_service = self._require_order_service()
            payment_service = self._require_payment_service()

            AuthorizationService.require_permission_for_session(
                session,
                Permission.PROCESS_PAYMENTS,
            )

            order_id = self._read_positive_integer(
                "\nEnter order ID: "
            )

            order = order_service.get_order(
                session,
                order_id,
            )

            if order is None:
                print(f"Order {order_id} was not found.")
                return

            total = order_service.calculate_total(
                session,
                order,
            )

            print("\n" + "=" * 60)
            print("PAYMENT PROCESSING")
            print("=" * 60)
            print(f"Order ID: {order.order_id}")
            print(f"Customer: {order.customer.name}")
            print(f"Order Total: {self._format_money(total)}")
            print("=" * 60)

            while True:
                payment_amount = self._read_decimal(
                    "Enter payment amount: "
                )

                if payment_amount <= 0:
                    print("Payment amount must be greater than zero.")
                    continue

                if payment_amount < total:
                    print(
                        "Payment amount is insufficient. "
                        f"Amount due: {self._format_money(total)}"
                    )
                    continue

                break

            payment_method = input(
                "Enter payment method: "
            ).strip()

            while not payment_method:
                print("Payment method cannot be empty.")
                payment_method = input(
                    "Enter payment method: "
                ).strip()

            payment = payment_service.create_payment(
                session=session,
                amount=payment_amount,
                payment_method=payment_method,
                order_id=order.order_id,
            )

            payment_service.complete_payment(
                session,
                payment,
            )

            change = payment_amount - total

            self._display_receipt(
                order=order,
                total=total,
                payment=payment,
                change=change,
            )

        except (
            AuthorizationError,
            OrderServiceError,
            RuntimeError,
            ValueError,
        ) as exc:
            print(f"Error: {exc}")

        except Exception as exc:
            print(f"Payment processing failed: {exc}")

    @staticmethod
    def _read_decimal(prompt: str) -> Decimal:
        """Read a valid decimal monetary amount from the CLI."""

        while True:
            value = input(prompt).strip()

            try:
                amount = Decimal(value)
            except Exception:
                print("Invalid amount. Please enter a valid number.")
                continue

            if not amount.is_finite():
                print("Invalid amount. Please enter a finite number.")
                continue

            return amount.quantize(Decimal("0.01"))

    def _display_receipt(
        self,
        order: Order,
        total: Decimal,
        payment,
        change: Decimal,
    ) -> None:
        """Display the payment receipt through the CLI."""

        print("\n" + "=" * 60)
        print("RECEIPT")
        print("=" * 60)
        print(f"Order ID: {order.order_id}")
        print(f"Customer: {order.customer.name}")
        print(f"Order Total: {self._format_money(total)}")
        print(f"Payment Method: {payment.payment_method}")
        print(f"Amount Paid: {self._format_money(payment.amount)}")
        print(f"Change: {self._format_money(change)}")
        print(f"Payment Status: {payment.status}")
        if payment.payment_id is not None:
            print(f"Payment ID: {payment.payment_id}")
        print("=" * 60)
        print("Payment completed successfully.")

    # ============================================================
    # REPORTING
    # ============================================================

    def reporting_cli(self) -> None:
        """Run the operational reporting menu."""
        try:
            self._require_session()
            self._require_reporting_service()
        except (AuthorizationError, RuntimeError) as exc:
            print(f"Error: {exc}")
            return

        while True:
            print("\nReporting")
            print("-" * 40)
            print("1. Sales Report")
            print("2. Order Report")
            print("3. Menu Performance Report")
            print("4. Inventory Report")
            print("5. Return")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.sales_report_cli()
            elif choice == "2":
                self.order_report_cli()
            elif choice == "3":
                self.menu_performance_report_cli()
            elif choice == "4":
                self.inventory_report_cli()
            elif choice == "5":
                return
            else:
                print("Invalid choice. Please enter 1 to 5.")

    def sales_report_cli(self) -> None:
        """Display the operational sales report."""
        try:
            session = self._require_session()
            service = self._require_reporting_service()
            report = service.get_sales_report(session)

            print("\nSales Report")
            print("=" * 80)

            records = report["records"]
            if not records:
                print("No completed sales found.")
                print("=" * 80)
                return

            print(
                f"{'Payment ID':<12}"
                f"{'Order ID':<10}"
                f"{'Amount':>12}"
                f"{'Method':<18}"
                f"{'Status':<12}"
            )
            print("-" * 80)

            for record in records:
                print(
                    f"{record['payment_id']:<12}"
                    f"{record['order_id']:<10}"
                    f"{record['amount']:>12.2f}"
                    f"{record['payment_method']:<18}"
                    f"{record['status']:<12}"
                )

            print("-" * 80)
            print(f"TOTAL SALES: {report['total_sales']:.2f}")
            print("=" * 80)

        except (
            ReportingServiceError,
            AuthorizationError,
            RuntimeError,
        ) as exc:
            print(f"Error: {exc}")

    def order_report_cli(self) -> None:
        """Display the operational order report."""
        try:
            session = self._require_session()
            service = self._require_reporting_service()
            report = service.get_order_report(session)

            print("\nOrder Report")
            print("=" * 60)

            records = report["records"]
            if not records:
                print("No orders found.")
                print("=" * 60)
                return

            print(
                f"{'Status':<25}"
                f"{'Number of Orders':>20}"
            )
            print("-" * 60)

            for record in records:
                print(
                    f"{record['status']:<25}"
                    f"{record['order_count']:>20}"
                )

            print("-" * 60)
            print(
                f"{'TOTAL ORDERS':<25}"
                f"{report['total_orders']:>20}"
            )
            print("=" * 60)

        except (
            ReportingServiceError,
            AuthorizationError,
            RuntimeError,
        ) as exc:
            print(f"Error: {exc}")

    def menu_performance_report_cli(self) -> None:
        """Display the menu-performance report."""
        try:
            session = self._require_session()
            service = self._require_reporting_service()
            report = service.get_menu_performance_report(session)

            print("\nMenu Performance Report")
            print("=" * 90)

            records = report["records"]
            if not records:
                print("No menu-performance data found.")
                print("=" * 90)
                return

            print(
                f"{'Item':<25}"
                f"{'Category':<20}"
                f"{'Qty Sold':>12}"
                f"{'Revenue':>15}"
            )
            print("-" * 90)

            for record in records:
                print(
                    f"{record['item_name']:<25}"
                    f"{record['category_name']:<20}"
                    f"{record['quantity_sold']:>12}"
                    f"{record['revenue']:>15.2f}"
                )

            print("=" * 90)

        except (
            ReportingServiceError,
            AuthorizationError,
            RuntimeError,
        ) as exc:
            print(f"Error: {exc}")

    def inventory_report_cli(self) -> None:
        """Display the operational inventory report."""
        try:
            session = self._require_session()
            service = self._require_reporting_service()
            report = service.get_inventory_report(session)

            print("\nInventory Report")
            print("=" * 100)

            records = report["records"]
            if not records:
                print("No inventory records found.")
                print("=" * 100)
                return

            print(
                f"{'Item':<25}"
                f"{'Quantity':>12}"
                f"{'Unit':<12}"
                f"{'Supplier':<25}"
                f"{'Status':<15}"
            )
            print("-" * 100)

            for record in records:
                status = (
                    "LOW STOCK"
                    if record["is_low_stock"]
                    else "Normal"
                )
                supplier = (
                    record["supplier_name"]
                    or "None"
                )

                print(
                    f"{record['item_name']:<25}"
                    f"{record['quantity']:>12.2f}"
                    f"{record['unit']:<12}"
                    f"{supplier:<25}"
                    f"{status:<15}"
                )

            print("-" * 100)
            print(
                "Low-stock threshold: "
                f"{report['low_stock_threshold']} units"
            )
            print("=" * 100)

        except (
            ReportingServiceError,
            AuthorizationError,
            RuntimeError,
        ) as exc:
            print(f"Error: {exc}")

    # ============================================================
    # INVENTORY MANAGEMENT
    # ============================================================

    def inventory_management_cli(self) -> None:
        """Run supplier and inventory management from the CLI."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()

            AuthorizationService.require_permission_for_session(
                session,
                Permission.VIEW_INVENTORY,
            )

        except (AuthorizationError, RuntimeError) as exc:
            print(f"Error: {exc}")
            return

        can_manage = self._has_permission(Permission.MANAGE_INVENTORY)

        while True:
            print("\nInventory Management")
            print("-" * 40)
            print("1. View inventory")
            print("2. View low-stock items")
            if can_manage:
                print("3. Add inventory item")
                print("4. Update inventory item")
                print("5. Add stock")
                print("6. Remove stock")
                print("7. Supplier management")
                print("8. Return")
            else:
                print("3. Return")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.view_inventory_cli()
            elif choice == "2":
                self.view_low_stock_cli()
            elif can_manage and choice == "3":
                self.create_inventory_cli()
            elif can_manage and choice == "4":
                self.update_inventory_cli()
            elif can_manage and choice == "5":
                self.add_inventory_stock_cli()
            elif can_manage and choice == "6":
                self.remove_inventory_stock_cli()
            elif can_manage and choice == "7":
                self.supplier_management_cli()
            elif (can_manage and choice == "8") or (not can_manage and choice == "3"):
                return
            else:
                print("Invalid choice. Please select a displayed option.")

    def view_inventory_cli(self) -> None:
        """Display all inventory records."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()
            inventory = service.get_all_inventory(session)

            if not inventory:
                print("No inventory records found.")
                return

            print("\nInventory Records")
            print("=" * 85)
            for item in inventory:
                supplier_name = (
                    item.supplier.name
                    if item.supplier is not None
                    else "None"
                )
                print(
                    f"ID: {item.inventory_id} | "
                    f"Name: {item.name} | "
                    f"Quantity: {item.quantity:g} {item.unit} | "
                    f"Supplier: {supplier_name}"
                )
            print("=" * 85)

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    def create_inventory_cli(self) -> None:
        """Create an inventory item."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()

            name = input("Inventory item name: ").strip()
            quantity = self._read_non_negative_number(
                "Starting quantity: "
            )
            unit = input("Unit: ").strip()
            supplier_id = self._read_optional_positive_integer(
                "Supplier ID (leave blank for none): "
            )

            item = service.create_inventory_item(
                session,
                name,
                quantity,
                unit,
                supplier_id,
            )

            print(
                f"Inventory item created successfully. "
                f"ID: {item.inventory_id}"
            )

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    def update_inventory_cli(self) -> None:
        """Update an existing inventory item."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()

            inventory_id = self._read_positive_integer(
                "Inventory ID: "
            )
            current = service.get_inventory(session, inventory_id)

            print(f"Current name: {current.name}")
            name = input("New name: ").strip()
            print(f"Current quantity: {current.quantity:g}")
            quantity = self._read_non_negative_number(
                "New quantity: "
            )
            print(f"Current unit: {current.unit}")
            unit = input("New unit: ").strip()
            supplier_id = self._read_optional_positive_integer(
                "New supplier ID (blank for none): "
            )

            service.update_inventory(
                session,
                inventory_id,
                name,
                quantity,
                unit,
                supplier_id,
            )

            print("Inventory item updated successfully.")

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    def add_inventory_stock_cli(self) -> None:
        """Increase the quantity of an inventory item."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()
            inventory_id = self._read_positive_integer(
                "Inventory ID: "
            )
            quantity = self._read_positive_number(
                "Quantity to add: "
            )

            item = service.add_stock(
                session,
                inventory_id,
                quantity,
            )

            print(
                f"Stock updated. Available quantity: "
                f"{item.quantity:g} {item.unit}"
            )

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    def remove_inventory_stock_cli(self) -> None:
        """Decrease the quantity of an inventory item."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()
            inventory_id = self._read_positive_integer(
                "Inventory ID: "
            )
            quantity = self._read_positive_number(
                "Quantity to remove: "
            )

            item = service.remove_stock(
                session,
                inventory_id,
                quantity,
            )

            print(
                f"Stock updated. Available quantity: "
                f"{item.quantity:g} {item.unit}"
            )

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    def view_low_stock_cli(self) -> None:
        """Display inventory items at or below the configured threshold."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()
            low_stock = service.get_low_stock_items(session)

            if not low_stock:
                print("No low-stock items identified.")
                return

            print("\nLow-Stock Inventory")
            print("=" * 70)
            for item in low_stock:
                print(
                    f"ID: {item.inventory_id} | "
                    f"{item.name} | "
                    f"Available: {item.quantity:g} {item.unit}"
                )
            print("=" * 70)

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    def supplier_management_cli(self) -> None:
        """Run supplier record management."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()
            AuthorizationService.require_permission_for_session(
                session,
                Permission.VIEW_INVENTORY,
            )
        except (AuthorizationError, RuntimeError) as exc:
            print(f"Error: {exc}")
            return

        while True:
            print("\nSupplier Management")
            print("-" * 40)
            print("1. View suppliers")
            print("2. Create supplier")
            print("3. Update supplier")
            print("4. Delete supplier")
            print("5. Return")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.view_suppliers_cli()
            elif choice == "2":
                self.create_supplier_cli()
            elif choice == "3":
                self.update_supplier_cli()
            elif choice == "4":
                self.delete_supplier_cli()
            elif choice == "5":
                return
            else:
                print("Invalid choice. Please enter 1 to 5.")

    def view_suppliers_cli(self) -> None:
        """Display supplier records."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()
            suppliers = service.get_all_suppliers(session)

            if not suppliers:
                print("No suppliers found.")
                return

            print("\nSupplier Records")
            print("=" * 75)
            for supplier in suppliers:
                print(
                    f"ID: {supplier.supplier_id} | "
                    f"Name: {supplier.name} | "
                    f"Phone: {supplier.phone} | "
                    f"Email: {supplier.email} | "
                    f"Address: {supplier.address}"
                )
            print("=" * 75)

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    def create_supplier_cli(self) -> None:
        """Create a supplier record."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()

            name = input("Supplier name: ").strip()
            phone = input("Phone: ").strip()
            email = input("Email: ").strip()
            address = input("Address: ").strip()

            supplier = service.create_supplier(
                session,
                name,
                phone,
                email,
                address,
            )

            print(
                f"Supplier created successfully. "
                f"ID: {supplier.supplier_id}"
            )

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    def update_supplier_cli(self) -> None:
        """Update a supplier record."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()
            supplier_id = self._read_positive_integer(
                "Supplier ID: "
            )
            current = service.get_supplier(session, supplier_id)

            print(f"Current name: {current.name}")
            name = input("New name: ").strip()
            phone = input("New phone: ").strip()
            email = input("New email: ").strip()
            address = input("New address: ").strip()

            service.update_supplier(
                session,
                supplier_id,
                name,
                phone,
                email,
                address,
            )

            print("Supplier updated successfully.")

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    def delete_supplier_cli(self) -> None:
        """Delete a supplier record."""
        try:
            session = self._require_session()
            service = self._require_inventory_service()
            supplier_id = self._read_positive_integer(
                "Supplier ID: "
            )

            service.delete_supplier(session, supplier_id)
            print("Supplier deleted successfully.")

        except (RMSException, RepositoryError) as exc:
            print(f"Error: {exc}")

    # ============================================================
    # INPUT VALIDATION
    # ============================================================

    @staticmethod
    def _read_positive_integer(
        prompt: str,
    ) -> int:
        """
        Read a positive integer from the CLI.

        This validates basic input formatting before the
        business service performs its own validation.
        """

        while True:
            value = input(prompt).strip()

            try:
                number = int(value)

            except ValueError:
                print(
                    "Invalid input. Please enter a whole number."
                )
                continue

            if number <= 0:
                print(
                    "Value must be greater than zero."
                )
                continue

            return number

    @staticmethod
    def _read_positive_number(prompt: str) -> float:
        """Read a strictly positive numeric value."""
        while True:
            value = input(prompt).strip()
            try:
                number = float(value)
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                continue

            if number <= 0:
                print("Value must be greater than zero.")
                continue

            return number

    @staticmethod
    def _read_non_negative_number(prompt: str) -> float:
        """Read a zero-or-positive numeric value."""
        while True:
            value = input(prompt).strip()
            try:
                number = float(value)
            except ValueError:
                print("Invalid input. Please enter a valid number.")
                continue

            if number < 0:
                print("Value cannot be negative.")
                continue

            return number

    @staticmethod
    def _read_optional_positive_integer(prompt: str) -> int | None:
        """Read a positive integer or blank for no association."""
        while True:
            value = input(prompt).strip()

            if not value:
                return None

            try:
                number = int(value)
            except ValueError:
                print("Invalid input. Please enter a whole number or leave blank.")
                continue

            if number <= 0:
                print("Value must be greater than zero.")
                continue

            return number

    @staticmethod
    def _read_yes_no(
        prompt: str,
    ) -> bool:
        """Read a yes/no answer from the CLI."""

        while True:
            answer = input(prompt).strip().lower()

            if answer in {"y", "yes"}:
                return True

            if answer in {"n", "no"}:
                return False

            print(
                "Invalid response. Please enter y or n."
            )

    # ============================================================
    # FORMATTING
    # ============================================================

    @staticmethod
    def _format_money(
        amount: Decimal,
    ) -> str:
        """Format a Decimal monetary value."""

        return f"K{Decimal(amount):,.2f}"


if __name__ == "__main__":
    application = RestaurantManagementSystem()
    application.run()