import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from app.data_access.database import DatabaseManager
from app.data_access.repositories import (
    RepositoryError,
    RoleRepository,
    UserRepository,
    MenuCategoryRepository,
    MenuItemRepository,
    CustomerRepository,
    OrderRepository,
    OrderItemRepository,
    PaymentRepository,
    InventoryRepository,
    SupplierRepository,
    OrderTransaction,
)
from app.models import (
    Customer,
    Inventory,
    MenuCategory,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    Role,
    Supplier,
    User,
)


class TestRepositories(unittest.TestCase):
    """Tests for the Phase 4 data access layer."""

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()

        database_path = (
            Path(self.temp_directory.name)
            / "test_restaurant.db"
        )

        self.database = DatabaseManager(
            str(database_path)
        )

        self.database.initialize_database(
            seed=False
        )

        self.roles = RoleRepository(
            self.database
        )

        self.users = UserRepository(
            self.database
        )

        self.categories = MenuCategoryRepository(
            self.database
        )

        self.menu_items = MenuItemRepository(
            self.database
        )

        self.customers = CustomerRepository(
            self.database
        )

        self.orders = OrderRepository(
            self.database
        )

        self.order_items = OrderItemRepository(
            self.database
        )

        self.payments = PaymentRepository(
            self.database
        )

        self.inventory = InventoryRepository(
            self.database
        )

        self.suppliers = SupplierRepository(
            self.database
        )

    def tearDown(self):
        self.temp_directory.cleanup()

    # --------------------------------------------------------
    # ROLE TESTS
    # --------------------------------------------------------

    def test_role_create_read_update_delete(self):
        role = Role(
            name="Manager",
            description="Restaurant manager",
        )

        created = self.roles.create(role)

        self.assertIsNotNone(created.role_id)

        found = self.roles.get_by_id(
            created.role_id
        )

        self.assertIsNotNone(found)
        self.assertEqual(
            found.name,
            "Manager",
        )

        found.description = "Updated manager"

        self.assertTrue(
            self.roles.update(found)
        )

        updated = self.roles.get_by_id(
            found.role_id
        )

        self.assertEqual(
            updated.description,
            "Updated manager",
        )

        self.assertTrue(
            self.roles.delete(found.role_id)
        )

        self.assertIsNone(
            self.roles.get_by_id(found.role_id)
        )

    # --------------------------------------------------------
    # USER TESTS
    # --------------------------------------------------------

    def test_user_create_and_read(self):
        role = self.roles.create(
            Role(name="Staff")
        )

        user = User(
            username="testuser",
            password_hash="hashed_password",
            role=role,
            full_name="Test User",
            email="test@example.com",
        )

        created = self.users.create(user)

        found = self.users.get_by_id(
            created.user_id
        )

        self.assertIsNotNone(found)
        self.assertEqual(
            found.username,
            "testuser",
        )

        self.assertEqual(
            found.role.name,
            "Staff",
        )

        self.assertEqual(
            found.password_hash,
            "hashed_password",
        )

    # --------------------------------------------------------
    # CATEGORY TESTS
    # --------------------------------------------------------

    def test_category_create_read_update_delete(self):
        category = self.categories.create(
            MenuCategory(
                name="Desserts",
                description="Dessert items",
            )
        )

        self.assertIsNotNone(
            category.category_id
        )

        found = self.categories.get_by_id(
            category.category_id
        )

        self.assertEqual(
            found.name,
            "Desserts",
        )

        found.description = "Updated desserts"

        self.assertTrue(
            self.categories.update(found)
        )

        self.assertEqual(
            self.categories.get_by_id(
                found.category_id
            ).description,
            "Updated desserts",
        )

        self.assertTrue(
            self.categories.delete(
                found.category_id
            )
        )

    # --------------------------------------------------------
    # MENU ITEM TESTS
    # --------------------------------------------------------

    def test_menu_item_relationship(self):
        category = self.categories.create(
            MenuCategory(
                name="Main Meals"
            )
        )

        item = self.menu_items.create(
            MenuItem(
                name="Chicken Rice",
                price=Decimal("15.00"),
                category=category,
                description="Chicken with rice",
            )
        )

        found = self.menu_items.get_by_id(
            item.item_id
        )

        self.assertIsNotNone(found)

        self.assertEqual(
            found.name,
            "Chicken Rice",
        )

        self.assertEqual(
            found.category.name,
            "Main Meals",
        )

        self.assertEqual(
            found.price,
            Decimal("15.0"),
        )

    def test_menu_item_update_delete(self):
        category = self.categories.create(
            MenuCategory(name="Drinks")
        )

        item = self.menu_items.create(
            MenuItem(
                name="Juice",
                price=Decimal("5.00"),
                category=category,
            )
        )

        item.price = Decimal("6.00")

        self.assertTrue(
            self.menu_items.update(item)
        )

        updated = self.menu_items.get_by_id(
            item.item_id
        )

        self.assertEqual(
            updated.price,
            Decimal("6.0"),
        )

        self.assertTrue(
            self.menu_items.delete(item.item_id)
        )

        self.assertIsNone(
            self.menu_items.get_by_id(
                item.item_id
            )
        )

    # --------------------------------------------------------
    # CUSTOMER TESTS
    # --------------------------------------------------------

    def test_customer_crud(self):
        customer = self.customers.create(
            Customer(
                name="John Customer",
                phone="70000000",
                email="john@example.com",
            )
        )

        found = self.customers.get_by_id(
            customer.customer_id
        )

        self.assertEqual(
            found.name,
            "John Customer",
        )

        found.phone = "71111111"

        self.assertTrue(
            self.customers.update(found)
        )

        updated = self.customers.get_by_id(
            found.customer_id
        )

        self.assertEqual(
            updated.phone,
            "71111111",
        )

        self.assertTrue(
            self.customers.delete(
                customer.customer_id
            )
        )

    # --------------------------------------------------------
    # SUPPLIER TESTS
    # --------------------------------------------------------

    def test_supplier_and_inventory_relationship(self):
        supplier = self.suppliers.create(
            Supplier(
                name="Fresh Foods",
                phone="12345678",
                email="fresh@example.com",
                address="Port Moresby",
            )
        )

        inventory = self.inventory.create(
            Inventory(
                name="Rice",
                quantity=50,
                unit="kg",
                supplier=supplier,
            )
        )

        found = self.inventory.get_by_id(
            inventory.inventory_id
        )

        self.assertIsNotNone(found)

        self.assertEqual(
            found.name,
            "Rice",
        )

        self.assertIsNotNone(
            found.supplier
        )

        self.assertEqual(
            found.supplier.name,
            "Fresh Foods",
        )

    # --------------------------------------------------------
    # ORDER TESTS
    # --------------------------------------------------------

    def test_order_relationship(self):
        customer = self.customers.create(
            Customer(
                name="Order Customer"
            )
        )

        order = self.orders.create(
            Order(
                customer=customer,
                status="Pending",
            )
        )

        found = self.orders.get_by_id(
            order.order_id
        )

        self.assertIsNotNone(found)

        self.assertEqual(
            found.customer.name,
            "Order Customer",
        )

        self.assertEqual(
            found.status,
            "Pending",
        )

    # --------------------------------------------------------
    # ORDER ITEM TESTS
    # --------------------------------------------------------

    def test_order_item_relationship(self):
        customer = self.customers.create(
            Customer(
                name="Order Item Customer"
            )
        )

        category = self.categories.create(
            MenuCategory(
                name="Meals"
            )
        )

        menu_item = self.menu_items.create(
            MenuItem(
                name="Burger",
                price=Decimal("12.00"),
                category=category,
            )
        )

        order = self.orders.create(
            Order(
                customer=customer
            )
        )

        order_item = self.order_items.create(
            order.order_id,
            OrderItem(
                menu_item=menu_item,
                quantity=2,
            ),
        )

        found = self.order_items.get_by_id(
            order_item.order_item_id
        )

        self.assertIsNotNone(found)

        self.assertEqual(
            found.menu_item.name,
            "Burger",
        )

        self.assertEqual(
            found.quantity,
            2,
        )

        self.assertEqual(
            found.subtotal,
            Decimal("24.00"),
        )

    # --------------------------------------------------------
    # PAYMENT TESTS
    # --------------------------------------------------------

    def test_payment_create_read_update_delete(self):
        customer = self.customers.create(
            Customer(
                name="Payment Customer"
            )
        )

        order = self.orders.create(
            Order(customer=customer)
        )

        payment = self.payments.create(
            Payment(
                amount=Decimal("25.00"),
                payment_method="Cash",
                order_id=order.order_id,
            )
        )

        found = self.payments.get_by_id(
            payment.payment_id
        )

        self.assertIsNotNone(found)

        self.assertEqual(
            found.amount,
            Decimal("25.0"),
        )

        found.mark_completed()

        self.assertTrue(
            self.payments.update(found)
        )

        updated = self.payments.get_by_id(
            found.payment_id
        )

        self.assertEqual(
            updated.status,
            "Completed",
        )

        self.assertTrue(
            self.payments.delete(
                found.payment_id
            )
        )

    # --------------------------------------------------------
    # INVALID FOREIGN KEY TESTS
    # --------------------------------------------------------

    def test_invalid_role_reference(self):
        user = User(
            username="invaliduser",
            password_hash="hashed_password",
            role=Role(
                role_id=999999,
                name="Invalid Role",
            ),
        )

        with self.assertRaises(RepositoryError):
            self.users.create(user)

    def test_invalid_category_reference(self):
        item = MenuItem(
            name="Invalid Item",
            price=Decimal("10.00"),
            category=MenuCategory(
                category_id=999999,
                name="Invalid Category",
            ),
        )

        with self.assertRaises(RepositoryError):
            self.menu_items.create(item)

    def test_invalid_customer_reference(self):
        order = Order(
            customer=Customer(
                customer_id=999999,
                name="Invalid Customer",
            )
        )

        with self.assertRaises(RepositoryError):
            self.orders.create(order)

    # --------------------------------------------------------
    # DATABASE ERROR TEST
    # --------------------------------------------------------

    def test_database_error_is_converted_to_repository_error(self):
        database_path = self.database.database_path

        database_path.unlink()

        repository = CustomerRepository(
            self.database
        )

        with self.assertRaises(RepositoryError):
            repository.get_all()

    # --------------------------------------------------------
    # TRANSACTION TEST
    # --------------------------------------------------------

    def test_order_transaction_commits(self):
        customer = self.customers.create(
            Customer(
                name="Transaction Customer"
            )
        )

        category = self.categories.create(
            MenuCategory(
                name="Transaction Meals"
            )
        )

        item = self.menu_items.create(
            MenuItem(
                name="Transaction Burger",
                price=Decimal("20.00"),
                category=category,
            )
        )

        order = Order(
            customer=customer
        )

        order_item = OrderItem(
            menu_item=item,
            quantity=2,
        )

        transaction = OrderTransaction(
            self.database
        )

        created_order = (
            transaction.create_order_with_items(
                order,
                [order_item],
            )
        )

        self.assertIsNotNone(
            created_order.order_id
        )

        stored_items = (
            self.order_items.get_by_order(
                created_order.order_id
            )
        )

        self.assertEqual(
            len(stored_items),
            1,
        )

        self.assertEqual(
            stored_items[0].quantity,
            2,
        )

    def test_order_transaction_rolls_back(self):
        customer = self.customers.create(
            Customer(
                name="Rollback Customer"
            )
        )

        category = self.categories.create(
            MenuCategory(
                name="Rollback Meals"
            )
        )

        valid_item = self.menu_items.create(
            MenuItem(
                name="Valid Meal",
                price=Decimal("10.00"),
                category=category,
            )
        )

        invalid_item = MenuItem(
            name="Invalid Meal",
            price=Decimal("5.00"),
            category=category,
            item_id=999999,
        )

        order = Order(
            customer=customer
        )

        transaction = OrderTransaction(
            self.database
        )

        with self.assertRaises(RepositoryError):
            transaction.create_order_with_items(
                order,
                [
                    OrderItem(
                        menu_item=valid_item,
                        quantity=1,
                    ),
                    OrderItem(
                        menu_item=invalid_item,
                        quantity=1,
                    ),
                ],
            )

        stored_orders = (
            self.orders.get_by_customer(
                customer.customer_id
            )
        )

        self.assertEqual(
            len(stored_orders),
            0,
        )


if __name__ == "__main__":
    unittest.main()