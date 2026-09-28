import unittest

from app.exceptions import ValidationError
from app.validation import Validator


class TestValidator(unittest.TestCase):

    def test_required_value_is_valid(self):
        result = Validator.required(
            "  Chicken Rice  ",
            "Menu item"
        )

        self.assertEqual(
            result,
            "Chicken Rice"
        )

    def test_required_value_rejects_empty_string(self):
        with self.assertRaises(ValidationError):
            Validator.required(
                "   ",
                "Menu item"
            )

    def test_required_value_rejects_none(self):
        with self.assertRaises(ValidationError):
            Validator.required(
                None,
                "Menu item"
            )

    def test_positive_integer_is_valid(self):
        result = Validator.positive_integer(
            "5",
            "Quantity"
        )

        self.assertEqual(result, 5)

    def test_positive_integer_rejects_zero(self):
        with self.assertRaises(ValidationError):
            Validator.positive_integer(
                0,
                "Quantity"
            )

    def test_positive_integer_rejects_negative(self):
        with self.assertRaises(ValidationError):
            Validator.positive_integer(
                -1,
                "Quantity"
            )

    def test_positive_integer_rejects_text(self):
        with self.assertRaises(ValidationError):
            Validator.positive_integer(
                "abc",
                "Quantity"
            )

    def test_positive_number_is_valid(self):
        result = Validator.positive_number(
            "15.50",
            "Price"
        )

        self.assertEqual(result, 15.50)

    def test_positive_number_rejects_negative(self):
        with self.assertRaises(ValidationError):
            Validator.positive_number(
                -5,
                "Price"
            )

    def test_valid_email(self):
        result = Validator.email(
            "customer@example.com"
        )

        self.assertEqual(
            result,
            "customer@example.com"
        )

    def test_invalid_email(self):
        with self.assertRaises(ValidationError):
            Validator.email(
                "invalid-email"
            )

    def test_valid_phone(self):
        result = Validator.phone(
            "+675 70000000"
        )

        self.assertEqual(
            result,
            "+675 70000000"
        )

    def test_invalid_phone(self):
        with self.assertRaises(ValidationError):
            Validator.phone(
                "ABC123"
            )

    def test_boolean_values(self):
        self.assertTrue(
            Validator.boolean(True, "Active")
        )

        self.assertFalse(
            Validator.boolean(False, "Active")
        )

    def test_invalid_boolean(self):
        with self.assertRaises(ValidationError):
            Validator.boolean(
                "maybe",
                "Active"
            )


if __name__ == "__main__":
    unittest.main()