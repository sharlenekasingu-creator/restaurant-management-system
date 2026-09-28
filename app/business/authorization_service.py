from __future__ import annotations

from enum import Enum

from app.models.user import User, UserSession


class AuthorizationError(Exception):
    """Raised when a user is not authorized to perform an action."""


class Permission(str, Enum):
    """System permissions."""

    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"

    MANAGE_MENU = "manage_menu"

    MANAGE_INVENTORY = "manage_inventory"
    VIEW_INVENTORY = "view_inventory"

    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"

    VIEW_REPORTS = "view_reports"

    MANAGE_ORDERS = "manage_orders"

    VIEW_CUSTOMERS = "view_customers"

    VIEW_MENU = "view_menu"

    PROCESS_PAYMENTS = "process_payments"


class AuthorizationService:
    """Provides role-based access control."""

    ROLE_PERMISSIONS = {
        "administrator": {
            Permission.MANAGE_USERS,
            Permission.MANAGE_ROLES,
            Permission.MANAGE_MENU,
            Permission.MANAGE_INVENTORY,
            Permission.VIEW_INVENTORY,
            Permission.MANAGE_SYSTEM_SETTINGS,
            Permission.VIEW_REPORTS,
            Permission.MANAGE_ORDERS,
            Permission.VIEW_CUSTOMERS,
            Permission.VIEW_MENU,
            Permission.PROCESS_PAYMENTS,
        },
        "manager": {
            Permission.MANAGE_MENU,
            Permission.MANAGE_ORDERS,
            Permission.VIEW_INVENTORY,
            Permission.VIEW_REPORTS,
            Permission.VIEW_CUSTOMERS,
            Permission.VIEW_MENU,
        },
        "staff/cashier": {
            Permission.MANAGE_ORDERS,
            Permission.VIEW_MENU,
            Permission.PROCESS_PAYMENTS,
        },
    }

    @classmethod
    def has_permission(
        cls,
        user: User,
        permission: Permission,
    ) -> bool:
        """Check whether a user has a specific permission."""

        if not user.is_active:
            return False

        role_name = user.role.name.strip().lower()

        permissions = cls.ROLE_PERMISSIONS.get(
            role_name,
            set(),
        )

        return permission in permissions

    @classmethod
    def require_permission(
        cls,
        user: User,
        permission: Permission,
    ) -> None:
        """
        Protect a function by requiring a specific permission.
        """

        if not cls.has_permission(user, permission):
            raise AuthorizationError(
                f"User '{user.username}' is not authorized "
                f"to perform '{permission.value}'."
            )

    @classmethod
    def require_authenticated(
        cls,
        session: UserSession | None,
    ) -> User:
        """Require an active authenticated session."""

        if session is None:
            raise AuthorizationError(
                "Authentication is required."
            )

        if not session.authenticated:
            raise AuthorizationError(
                "Authentication is required."
            )

        if not session.user.is_active:
            raise AuthorizationError(
                "The user account is inactive."
            )

        return session.user

    @classmethod
    def require_permission_for_session(
        cls,
        session: UserSession | None,
        permission: Permission,
    ) -> User:
        """
        Require an authenticated session and a specific permission.
        """

        user = cls.require_authenticated(session)

        cls.require_permission(
            user,
            permission,
        )

        return user