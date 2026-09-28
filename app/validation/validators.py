from __future__ import annotations

import re
from typing import Any, Optional

from app.exceptions import ValidationError


class Validator:
    """Reusable validation functions for the RMS."""

    @staticmethod
    def required(value: Any, field_name: str) -> str:
        """
        Validate that a value is present and not empty.

        Returns the cleaned string value.
        """
        if value is None:
            raise ValidationError(
                f"{field_name} is required."
            )

        value = str(value).strip()

        if not value:
            raise ValidationError(
                f"{field_name} cannot be empty."
            )

        return value

    @staticmethod
    def optional_string(
        value: Optional[Any],
        field_name: str
    ) -> str:
        """Validate an optional text value."""
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def positive_integer(
        value: Any,
        field_name: str
    ) -> int:
        """Validate that a value is a positive integer."""
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                f"{field_name} must be a valid integer."
            ) from exc

        if number <= 0:
            raise ValidationError(
                f"{field_name} must be greater than zero."
            )

        return number

    @staticmethod
    def non_negative_integer(
        value: Any,
        field_name: str
    ) -> int:
        """Validate that a value is zero or a positive integer."""
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                f"{field_name} must be a valid integer."
            ) from exc

        if number < 0:
            raise ValidationError(
                f"{field_name} cannot be negative."
            )

        return number

    @staticmethod
    def positive_number(
        value: Any,
        field_name: str
    ) -> float:
        """Validate that a value is a positive number."""
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                f"{field_name} must be a valid number."
            ) from exc

        if number <= 0:
            raise ValidationError(
                f"{field_name} must be greater than zero."
            )

        return number

    @staticmethod
    def non_negative_number(
        value: Any,
        field_name: str
    ) -> float:
        """Validate that a value is zero or greater."""
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                f"{field_name} must be a valid number."
            ) from exc

        if number < 0:
            raise ValidationError(
                f"{field_name} cannot be negative."
            )

        return number

    @staticmethod
    def email(
        value: Optional[Any],
        field_name: str = "Email"
    ) -> str:
        """Validate an optional email address."""
        if value is None:
            return ""

        email = str(value).strip()

        if not email:
            return ""

        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(pattern, email):
            raise ValidationError(
                f"{field_name} must be a valid email address."
            )

        return email

    @staticmethod
    def phone(
        value: Optional[Any],
        field_name: str = "Phone"
    ) -> str:
        """Validate an optional phone number."""
        if value is None:
            return ""

        phone = str(value).strip()

        if not phone:
            return ""

        if not re.fullmatch(r"[0-9+\-\s()]+", phone):
            raise ValidationError(
                f"{field_name} contains invalid characters."
            )

        return phone

    @staticmethod
    def boolean(
        value: Any,
        field_name: str
    ) -> bool:
        """Validate a boolean value."""
        if isinstance(value, bool):
            return value

        if value in (0, 1):
            return bool(value)

        if isinstance(value, str):
            cleaned = value.strip().lower()

            if cleaned in ("true", "yes", "1"):
                return True

            if cleaned in ("false", "no", "0"):
                return False

        raise ValidationError(
            f"{field_name} must be a boolean value."
        )