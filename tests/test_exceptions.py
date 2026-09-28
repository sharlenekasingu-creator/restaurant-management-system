import unittest

from app.exceptions import (
    RMSException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ResourceNotFoundError,
    BusinessRuleError,
)


class TestExceptions(unittest.TestCase):

    def test_validation_error(self):
        error = ValidationError(
            "Invalid input."
        )

        self.assertIsInstance(
            error,
            RMSException
        )

        self.assertEqual(
            error.message,
            "Invalid input."
        )

    def test_authentication_error(self):
        error = AuthenticationError(
            "Login failed."
        )

        self.assertIsInstance(
            error,
            RMSException
        )

    def test_authorization_error(self):
        error = AuthorizationError(
            "Access denied."
        )

        self.assertIsInstance(
            error,
            RMSException
        )

    def test_database_error(self):
        error = DatabaseError(
            "Database failure."
        )

        self.assertIsInstance(
            error,
            RMSException
        )

    def test_resource_not_found_error(self):
        error = ResourceNotFoundError(
            "Customer was not found."
        )

        self.assertIsInstance(
            error,
            RMSException
        )

    def test_business_rule_error(self):
        error = BusinessRuleError(
            "Business condition failed."
        )

        self.assertIsInstance(
            error,
            RMSException
        )


if __name__ == "__main__":
    unittest.main()