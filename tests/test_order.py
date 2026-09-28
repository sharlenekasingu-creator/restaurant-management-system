import unittest
from decimal import Decimal

from app.models.customer import Customer
from app.models.menu import MenuCategory, MenuItem
from app.models.order import Order, OrderItem


class TestOrderDomainModel(unittest.TestCase):

    def setUp(self):
        self.customer = Customer(name="John Smith")

        self.category = MenuCategory(name="Meals")

        self.item = MenuItem(
            name="Burger",
            price=Decimal("10.00"),
            category=self.category
        )

        self.order = Order(customer=self.customer)

    def test_order_creation(self):
        self.assertEqual(self.order.customer.name, "John Smith")
        self.assertEqual(self.order.status, "Pending")

    def test_order_item_subtotal(self):
        order_item = OrderItem(
            menu_item=self.item,
            quantity=3
        )

        self.assertEqual(
            order_item.subtotal,
            Decimal("30.00")
        )

    def test_order_total(self):
        first_item = OrderItem(
            menu_item=self.item,
            quantity=2
        )

        second_item = OrderItem(
            menu_item=self.item,
            quantity=1
        )

        self.order.add_item(first_item)
        self.order.add_item(second_item)

        self.assertEqual(
            self.order.calculate_total(),
            Decimal("30.00")
        )

    def test_invalid_quantity_is_rejected(self):
        with self.assertRaises(ValueError):
            OrderItem(
                menu_item=self.item,
                quantity=0
            )

    def test_order_status_can_be_updated(self):
        self.order.update_status("Completed")

        self.assertEqual(self.order.status, "Completed")


if __name__ == "__main__":
    unittest.main()