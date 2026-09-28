import unittest

from app.models.supplier import Supplier


class TestSupplierDomainModel(unittest.TestCase):

    def test_supplier_creation(self):
        supplier = Supplier(
            name="Fresh Foods Supplier",
            phone="12345678",
            email="supplier@example.com",
            address="Port Moresby"
        )

        self.assertEqual(
            supplier.name,
            "Fresh Foods Supplier"
        )

        self.assertEqual(
            supplier.address,
            "Port Moresby"
        )

    def test_empty_supplier_name_is_rejected(self):
        with self.assertRaises(ValueError):
            Supplier(name="")


if __name__ == "__main__":
    unittest.main()