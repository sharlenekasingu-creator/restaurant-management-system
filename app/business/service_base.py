from __future__ import annotations

from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ResourceNotFoundError,
)


class BusinessService:
    """
    Base class for business-layer services.

    Provides reusable checks for common business conditions.
    """

    @staticmethod
    def require_authenticated(user: object | None) -> None:
        """Ensure that a user is authenticated."""
        if user is None:
            raise AuthenticationError(
                "Authentication is required."
            )

    @staticmethod
    def require_authorized(
        allowed_roles: set[str],
        user_role: str
    ) -> None:
        """Ensure that the current role is authorized."""
        if user_role not in allowed_roles:
            raise AuthorizationError(
                "You are not authorized to perform this action."
            )

    @staticmethod
    def require_resource(
        resource: object | None,
        resource_name: str
    ) -> object:
        """Ensure that a requested resource exists."""
        if resource is None:
            raise ResourceNotFoundError(
                f"{resource_name} was not found."
            )

        return resource

    @staticmethod
    def require_business_condition(
        condition: bool,
        message: str
    ) -> None:
        """Raise a business-rule error when a condition fails."""
        if not condition:
            raise BusinessRuleError(message)