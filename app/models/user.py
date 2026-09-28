from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Role:
    """Represents a system role."""

    role_id: Optional[int] = None
    name: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.description = self.description.strip()

        if not self.name:
            raise ValueError("Role name cannot be empty.")


@dataclass
class User:
    """Represents a system user."""

    username: str
    password_hash: str
    role: Role
    user_id: Optional[int] = None
    full_name: str = ""
    email: str = ""
    is_active: bool = True

    def __post_init__(self) -> None:
        self.username = self.username.strip()
        self.full_name = self.full_name.strip()
        self.email = self.email.strip()

        if not self.username:
            raise ValueError("Username cannot be empty.")

        if not self.password_hash:
            raise ValueError("Password hash cannot be empty.")

    def deactivate(self) -> None:
        """Deactivate the user."""
        self.is_active = False

    def activate(self) -> None:
        """Activate the user."""
        self.is_active = True

    def has_role(self, role_name: str) -> bool:
        """Check whether the user has the specified role."""
        return self.role.name.lower() == role_name.strip().lower()


@dataclass
class UserSession:
    """Represents an authenticated user session."""

    user: User
    authenticated: bool = field(default=True)

    def logout(self) -> None:
        """End the current session."""
        self.authenticated = False