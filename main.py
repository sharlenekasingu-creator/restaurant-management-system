import argparse
import getpass
import tkinter as tk

from app.data_access.database import DatabaseError, DatabaseManager
from app.data_access.repositories import (
    CustomerRepository,
    InventoryRepository,
    MenuCategoryRepository,
    MenuItemRepository,
    OrderItemRepository,
    OrderRepository,
    OrderTransaction,
    PaymentRepository,
    RoleRepository,
    SupplierRepository,
    UserRepository,
)

from app.data_access.reporting_repository import (
    ReportingRepository,
)

# PHASE 12: Use the concrete reporting service implementation
from app.business.reporting_service import (
    BasicReportingService,
)

from app.business.authentication_service import (
    AuthenticationError,
    AuthenticationServiceImplementation,
)

from app.business.inventory_service import InventoryService
from app.business.menu_service import MenuService
from app.business.customer_service import CustomerService
from app.business.order_service import OrderService
from app.business.payment_service import PaymentService

from app.config.inventory_config import InventorySettings

from app.presentation.cli import RestaurantManagementSystem
from app.presentation.gui import RestaurantManagementGUI


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Restaurant Management System"
    )

    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize the SQLite database and sample data."
    )

    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Initialize the database without sample data."
    )

    # ------------------------------------------------------------
    # GUI INSERTION
    # ------------------------------------------------------------
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Start the graphical user interface."
    )

    return parser.parse_args()


def initialize_database(seed: bool = True) -> bool:
    """Initialize the SQLite development database."""

    database = DatabaseManager()

    try:
        database.initialize_database(seed=seed)

        print("Database initialization completed.")
        print(
            f"Database: {database.database_path}"
        )

        if seed:
            print("Sample data has been loaded.")
        else:
            print(
                "Database created without sample data."
            )

        return True

    except DatabaseError as exc:
        print(
            f"Database initialization failed: {exc}"
        )
        return False


def create_order_service(
    database: DatabaseManager,
) -> OrderService:
    """Create the order service and its data-access dependencies."""

    order_repository = OrderRepository(database)
    order_item_repository = OrderItemRepository(database)
    customer_repository = CustomerRepository(database)
    menu_item_repository = MenuItemRepository(database)
    order_transaction = OrderTransaction(database)

    return OrderService(
        order_repository=order_repository,
        order_item_repository=order_item_repository,
        customer_repository=customer_repository,
        menu_item_repository=menu_item_repository,
        order_transaction=order_transaction,
    )


def create_payment_service(
    database: DatabaseManager,
) -> PaymentService:
    """Create the existing payment service and repository."""

    payment_repository = PaymentRepository(database)

    return PaymentService(
        payment_repository
    )


def create_inventory_service(
    database: DatabaseManager,
) -> InventoryService:
    """Create the Phase 11 inventory service and repositories."""

    inventory_repository = InventoryRepository(
        database
    )

    supplier_repository = SupplierRepository(
        database
    )

    return InventoryService(
        inventory_repository=inventory_repository,
        supplier_repository=supplier_repository,
        settings=InventorySettings(),
    )


def create_menu_service(
    database: DatabaseManager,
) -> MenuService:
    """Create the menu service and repositories."""

    category_repository = MenuCategoryRepository(
        database
    )

    item_repository = MenuItemRepository(
        database
    )

    return MenuService(
        category_repository,
        item_repository,
    )


def create_customer_service(
    database: DatabaseManager,
) -> CustomerService:
    """Create the customer service and repository."""

    customer_repository = CustomerRepository(
        database
    )

    return CustomerService(
        customer_repository
    )


def create_authentication_service(
    database: DatabaseManager,
) -> AuthenticationServiceImplementation:
    """Create the authentication service and its repositories."""

    user_repository = UserRepository(
        database
    )

    role_repository = RoleRepository(
        database
    )

    return AuthenticationServiceImplementation(
        user_repository=user_repository,
        role_repository=role_repository,
    )


def authenticate_user(
    authentication_service: AuthenticationServiceImplementation,
):
    """Prompt for credentials and authenticate the user."""

    print("\n" + "=" * 60)
    print("Restaurant Management System")
    print("Authentication")
    print("=" * 60)

    while True:

        username = input(
            "Username: "
        ).strip()

        password = getpass.getpass(
            "Password: "
        )

        try:

            session = (
                authentication_service.authenticate(
                    username,
                    password,
                )
            )

            print(
                "\nAuthentication successful."
            )

            if session.user.full_name:

                print(
                    f"Welcome, "
                    f"{session.user.full_name}!"
                )

            else:

                print(
                    f"Welcome, "
                    f"{session.user.username}!"
                )

            print(
                f"Role: "
                f"{session.user.role.name}"
            )

            print()

            return session

        except AuthenticationError as exc:

            print(
                f"\nAuthentication failed: {exc}"
            )

            retry = input(
                "Try again? (y/n): "
            ).strip().lower()

            if retry != "y":
                return None


def main() -> None:
    """Start the Restaurant Management System."""

    arguments = parse_arguments()

    # ------------------------------------------------------------
    # EXISTING DATABASE OPTIONS
    # ------------------------------------------------------------

    if (
        arguments.no_seed
        and not arguments.init_db
    ):
        print(
            "--no-seed can only be used "
            "with --init-db."
        )
        return

    if arguments.init_db:

        initialize_database(
            seed=not arguments.no_seed
        )

        return

    # ------------------------------------------------------------
    # GUI INSERTION
    #
    # IMPORTANT:
    # This is BEFORE terminal authentication.
    #
    # Therefore:
    #
    # python main.py --gui
    #
    # will NOT ask for:
    #
    # Username:
    # Password:
    #
    # in the terminal.
    # ------------------------------------------------------------

    if arguments.gui:

        database = DatabaseManager()

        if not database.database_exists():

            message = (
                "Database does not exist.\n\n"
                "Run:\n"
                "python main.py --init-db"
            )

            print(message)

            return

        authentication_service = (
            create_authentication_service(
                database
            )
        )

        order_service = (
            create_order_service(
                database
            )
        )

        reporting_repository = (
            ReportingRepository(
                database
            )
        )

        reporting_service = (
            BasicReportingService(
                reporting_repository
            )
        )

        payment_service = (
            create_payment_service(
                database
            )
        )

        inventory_service = (
            create_inventory_service(
                database
            )
        )

        menu_service = (
            create_menu_service(
                database
            )
        )

        customer_service = (
            create_customer_service(
                database
            )
        )

        root = tk.Tk()

        application = (
            RestaurantManagementGUI(
                root=root,
                database=database,
                authentication_service=authentication_service,
                order_service=order_service,
                payment_service=payment_service,
                inventory_service=inventory_service,
                reporting_service=reporting_service,
                menu_service=menu_service,
                customer_service=customer_service,
            )
        )

        root.mainloop()

        return

    # ------------------------------------------------------------
    # EXISTING CLI APPLICATION
    # ------------------------------------------------------------

    database = DatabaseManager()

    if not database.database_exists():

        print(
            "Database does not exist. "
            "Run the application with "
            "--init-db first."
        )

        return

    authentication_service = (
        create_authentication_service(
            database
        )
    )

    # Keep the application alive across a logout.
    #
    # Existing CLI functionality is preserved.

    while True:

        session = authenticate_user(
            authentication_service
        )

        if session is None:

            print(
                "\nApplication closed."
            )

            return

        order_service = (
            create_order_service(
                database
            )
        )

        reporting_repository = (
            ReportingRepository(
                database
            )
        )

        reporting_service = (
            BasicReportingService(
                reporting_repository
            )
        )

        payment_service = (
            create_payment_service(
                database
            )
        )

        inventory_service = (
            create_inventory_service(
                database
            )
        )

        menu_service = (
            create_menu_service(
                database
            )
        )

        customer_service = (
            create_customer_service(
                database
            )
        )

        application = RestaurantManagementSystem(
            order_service=order_service,
            session=session,
            payment_service=payment_service,
            inventory_service=inventory_service,
            reporting_service=reporting_service,
            menu_service=menu_service,
            customer_service=customer_service,
        )

        application.run()

        if not session.authenticated:

            print(
                "\nReturning to login..."
            )

            continue

        return


if __name__ == "__main__":
    main()