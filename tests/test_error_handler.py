import unittest

from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
)
from app.presentation import CLIErrorHandler


class TestCLIErrorHandler(unittest.TestCase):

    def test_validation_error_message(self):
        error = ValidationError(
            "Name cannot be empty."
        )

        message = CLIErrorHandler.handle(error)

        self.assertEqual(
            message,
            "Validation error: Name cannot be empty."
        )

    def test_authentication_error_message(self):
        error = AuthenticationError(
            "Invalid username or password."
        )

        message = CLIErrorHandler.handle(error)

        self.assertEqual(
            message,
            "Authentication error: "
            "Invalid username or password."
        )

    def test_authorization_error_message(self):
        error = AuthorizationError(
            "Access denied."
        )

        message = CLIErrorHandler.handle(error)

        self.assertEqual(
            message,
            "Authorization error: Access denied."
        )

    def test_resource_not_found_message(self):
        error = ResourceNotFoundError(
            "Customer was not found."
        )

        message = CLIErrorHandler.handle(error)

        self.assertEqual(
            message,
            "Not found: Customer was not found."
        )

    def test_business_rule_error_message(self):
        error = BusinessRuleError(
            "The operation is not allowed."
        )

        message = CLIErrorHandler.handle(error)

        self.assertEqual(
            message,
            "Business rule error: "
            "The operation is not allowed."
        )

    def test_database_error_hides_technical_details(self):
        error = DatabaseError(
            "SQLite internal technical information."
        )

        message = CLIErrorHandler.handle(error)

        self.assertEqual(
            message,
            "Database error: "
            "The requested database operation could not be completed."
        )

        self.assertNotIn(
            "SQLite internal",
            message
        )

    def test_unknown_error_is_safe(self):
        error = RuntimeError(
            "Sensitive internal information."
        )

        message = CLIErrorHandler.handle(error)

        self.assertEqual(
            message,
            "An unexpected error occurred."
        )

        self.assertNotIn(
            "Sensitive internal",
            message
        )


if __name__ == "__main__":
    unittest.main()