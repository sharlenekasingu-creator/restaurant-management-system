import unittest
from decimal import Decimal

from app.models.payment import Payment


class TestPaymentDomainModel(unittest.TestCase):

    def test_payment_creation(self):
        payment = Payment(
            amount=Decimal("25.00"),
            payment_method="Cash",
            order_id=1
        )

        self.assertEqual(payment.amount, Decimal("25.00"))
        self.assertEqual(payment.status, "Pending")

    def test_payment_can_be_completed(self):
        payment = Payment(
            amount=Decimal("25.00"),
            payment_method="Cash"
        )

        payment.mark_completed()

        self.assertEqual(payment.status, "Completed")

    def test_payment_can_fail(self):
        payment = Payment(
            amount=Decimal("25.00"),
            payment_method="Cash"
        )

        payment.mark_failed()

        self.assertEqual(payment.status, "Failed")

    def test_invalid_payment_amount_is_rejected(self):
        with self.assertRaises(ValueError):
            Payment(
                amount=Decimal("0"),
                payment_method="Cash"
            )


if __name__ == "__main__":
    unittest.main()