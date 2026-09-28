"""Application exceptions for the Restaurant Management System."""

from app.exceptions.exceptions import (
    RMSException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ResourceNotFoundError,
    BusinessRuleError,
)

__all__ = [
    "RMSException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "DatabaseError",
    "ResourceNotFoundError",
    "BusinessRuleError",
]