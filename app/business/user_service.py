from __future__ import annotations

from app.data_access.repositories import UserRepository
from app.models.user import Role, User


class UserService:
    """Business service for user management."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def create_user(
        self,
        username: str,
        password_hash: str,
        role: Role,
        full_name: str = "",
        email: str = "",
    ) -> User:
        """Create a user domain object."""
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            full_name=full_name,
            email=email,
        )

        return self._repository.add(user)

    def activate_user(self, user: User) -> None:
        """Activate a user."""
        user.activate()

    def deactivate_user(self, user: User) -> None:
        """Deactivate a user."""
        user.deactivate()