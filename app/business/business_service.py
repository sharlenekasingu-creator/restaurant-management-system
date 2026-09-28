from __future__ import annotations

from collections.abc import Iterable

from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ResourceNotFoundError,
)


class BusinessService:
    """Common business-rule validation helpers."""

    @staticmethod
    def require_authenticated(user) -> None:
        """Ensure that a user is authenticated."""
        if user is None:
            raise AuthenticationError(
                "Authentication is required."
            )

    @staticmethod
    def require_authorized(
        allowed_roles: Iterable[str],
        user_role: str,
    ) -> None:
        """Ensure that the user's role is authorized."""
        if user_role not in allowed_roles:
            raise AuthorizationError(
                f"Role '{user_role}' is not authorized "
                "to perform this operation."
            )

    @staticmethod
    def require_resource(
        resource,
        resource_name: str,
    ):
        """Ensure that a requested resource exists."""
        if resource is None:
            raise ResourceNotFoundError(
                f"{resource_name} was not found."
            )

        return resource

    @staticmethod
    def require_business_condition(
        condition: bool,
        message: str,
    ) -> None:
        """Ensure that a business rule condition is satisfied."""
        if not condition:
            raise BusinessRuleError(message)