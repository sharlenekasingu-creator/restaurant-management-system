import sqlite3
import unittest
from decimal import Decimal

from app.data_access.repositories import (
    PaymentRepository,
    RepositoryError,
)
from app.models.payment import Payment


class BrokenDatabase:
    def connect(self):
        raise sqlite3.OperationalError(
            "Simulated database connection failure"
        )


class TestPaymentDatabaseFailure(unittest.TestCase):

    def test_payment_creation_handles_database_failure(self):
        repository = PaymentRepository(BrokenDatabase())

        payment = Payment(
            amount=Decimal("30.00"),
            payment_method="Cash",
            order_id=1,
        )

        with self.assertRaises(RepositoryError) as context:
            repository.create(payment)

        self.assertIn(
            "Database",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()