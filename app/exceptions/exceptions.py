class RMSException(Exception):
    """Base exception for the Restaurant Management System."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(RMSException):
    """Raised when user or application input is invalid."""


class AuthenticationError(RMSException):
    """Raised when authentication fails."""


class AuthorizationError(RMSException):
    """Raised when a user is not authorized to perform an action."""


class DatabaseError(RMSException):
    """Raised when a database operation fails."""


class ResourceNotFoundError(RMSException):
    """Raised when a requested resource cannot be found."""


class BusinessRuleError(RMSException):
    """Raised when a business rule is violated."""