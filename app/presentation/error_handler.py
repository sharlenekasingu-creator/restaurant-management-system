from __future__ import annotations

import sqlite3

from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    DatabaseError,
    ResourceNotFoundError,
    ValidationError,
)


class CLIErrorHandler:
    """Converts application exceptions into safe CLI messages."""

    @staticmethod
    def get_user_message(error: Exception) -> str:
        """
        Return a safe message suitable for normal CLI users.
        """

        if isinstance(error, ValidationError):
            return f"Validation error: {error.message}"

        if isinstance(error, AuthenticationError):
            return f"Authentication error: {error.message}"

        if isinstance(error, AuthorizationError):
            return f"Authorization error: {error.message}"

        if isinstance(error, ResourceNotFoundError):
            return f"Not found: {error.message}"

        if isinstance(error, BusinessRuleError):
            return f"Business rule error: {error.message}"

        if isinstance(error, DatabaseError):
            return (
                "Database error: "
                "The requested database operation could not be completed."
            )

        if isinstance(error, sqlite3.Error):
            return (
                "Database error: "
                "The requested database operation could not be completed."
            )

        return "An unexpected error occurred."

    @staticmethod
    def handle(error: Exception) -> str:
        """Return the safe user-facing error message."""
        return CLIErrorHandler.get_user_message(error)