import unittest
from decimal import Decimal

from app.models.menu import Menu, MenuCategory, MenuItem


class TestMenuDomainModel(unittest.TestCase):

    def setUp(self):
        self.category = MenuCategory(
            name="Main Meals",
            description="Main restaurant meals"
        )

        self.item = MenuItem(
            name="Chicken Rice",
            price=Decimal("15.00"),
            category=self.category
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Main Meals")

    def test_menu_item_creation(self):
        self.assertEqual(self.item.name, "Chicken Rice")
        self.assertEqual(self.item.price, Decimal("15.00"))

    def test_negative_price_is_rejected(self):
        with self.assertRaises(ValueError):
            MenuItem(
                name="Invalid Item",
                price=Decimal("-5.00"),
                category=self.category
            )

    def test_item_can_be_marked_unavailable(self):
        self.item.mark_unavailable()

        self.assertFalse(self.item.is_available)

    def test_item_can_be_marked_available(self):
        self.item.mark_unavailable()
        self.item.mark_available()

        self.assertTrue(self.item.is_available)

    def test_menu_composition(self):
        menu = Menu()

        menu.add_category(self.category)
        menu.add_item(self.item)

        self.assertEqual(len(menu.categories), 1)
        self.assertEqual(len(menu.items), 1)
        self.assertEqual(len(menu.get_available_items()), 1)


if __name__ == "__main__":
    unittest.main()