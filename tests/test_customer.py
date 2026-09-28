import unittest

from app.models.customer import Customer


class TestCustomerDomainModel(unittest.TestCase):

    def test_customer_creation(self):
        customer = Customer(
            name="John Smith",
            phone="12345678",
            email="john@example.com"
        )

        self.assertEqual(customer.name, "John Smith")
        self.assertEqual(customer.phone, "12345678")

    def test_empty_customer_name_is_rejected(self):
        with self.assertRaises(ValueError):
            Customer(name="")


if __name__ == "__main__":
    unittest.main()