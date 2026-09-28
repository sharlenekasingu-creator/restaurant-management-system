from __future__ import annotations

import hashlib
import hmac
import os
import re
from abc import ABC, abstractmethod
from typing import Optional

from app.data_access.repositories import RepositoryError, RoleRepository, UserRepository
from app.models.user import Role, User, UserSession


class AuthenticationError(Exception):
    """Raised when authentication fails."""


class RegistrationError(Exception):
    """Raised when user registration fails."""


class AuthenticationService(ABC):
    """Abstraction for authentication operations."""

    @abstractmethod
    def register_user(
        self,
        username: str,
        password: str,
        role_name: str,
        full_name: str = "",
        email: str = "",
    ) -> User:
        """Register a new user."""

    @abstractmethod
    def authenticate(
        self,
        username: str,
        password: str,
    ) -> UserSession:
        """Authenticate a user."""

    @abstractmethod
    def logout(self) -> None:
        """Log out the current user."""

    @abstractmethod
    def get_current_session(self) -> Optional[UserSession]:
        """Return the current authenticated session."""


class PasswordHasher:
    """Secure password hashing and verification using PBKDF2-HMAC."""

    ALGORITHM = "sha256"
    ITERATIONS = 600_000
    SALT_LENGTH = 32
    HASH_LENGTH = 32

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Create a secure password hash."""

        if not isinstance(password, str) or not password:
            raise ValueError("Password cannot be empty.")

        salt = os.urandom(cls.SALT_LENGTH)

        password_bytes = password.encode("utf-8")

        password_hash = hashlib.pbkdf2_hmac(
            cls.ALGORITHM,
            password_bytes,
            salt,
            cls.ITERATIONS,
            dklen=cls.HASH_LENGTH,
        )

        return (
            f"pbkdf2_{cls.ALGORITHM}$"
            f"{cls.ITERATIONS}$"
            f"{salt.hex()}$"
            f"{password_hash.hex()}"
        )

    @classmethod
    def verify_password(
        cls,
        password: str,
        stored_hash: str,
    ) -> bool:
        """Verify a password against a stored password hash."""

        if not isinstance(password, str):
            return False

        if not isinstance(stored_hash, str) or not stored_hash:
            return False

        try:
            algorithm_part, iterations_part, salt_hex, hash_hex = (
                stored_hash.split("$", 3)
            )

            if algorithm_part != f"pbkdf2_{cls.ALGORITHM}":
                return False

            iterations = int(iterations_part)

            salt = bytes.fromhex(salt_hex)
            expected_hash = bytes.fromhex(hash_hex)

            calculated_hash = hashlib.pbkdf2_hmac(
                cls.ALGORITHM,
                password.encode("utf-8"),
                salt,
                iterations,
                dklen=len(expected_hash),
            )

            return hmac.compare_digest(
                calculated_hash,
                expected_hash,
            )

        except (ValueError, TypeError):
            return False


class AuthenticationServiceImplementation(AuthenticationService):
    """
    Business logic for user registration, authentication,
    authenticated session management and logout.
    """

    ALLOWED_ROLES = {
        "administrator",
        "manager",
        "staff/cashier",
    }

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
    ) -> None:
        self._user_repository = user_repository
        self._role_repository = role_repository
        self._current_session: Optional[UserSession] = None

    def register_user(
        self,
        username: str,
        password: str,
        role_name: str,
        full_name: str = "",
        email: str = "",
    ) -> User:
        """Register a new user with a securely hashed password."""

        username = self._validate_username(username)
        password = self._validate_password(password)
        role_name = self._validate_role(role_name)

        existing_user = self._user_repository.get_by_username(username)

        if existing_user is not None:
            raise RegistrationError(
                "Username is already registered."
            )

        role = self._role_repository.get_by_name(role_name)

        if role is None:
            raise RegistrationError(
                f"Role '{role_name}' does not exist."
            )

        password_hash = PasswordHasher.hash_password(password)

        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            full_name=full_name,
            email=email,
        )

        try:
            return self._user_repository.create(user)

        except RepositoryError as exc:
            raise RegistrationError(
                f"Unable to register user: {exc}"
            ) from exc

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> UserSession:
        """Authenticate a user and create an authenticated session."""

        if not isinstance(username, str) or not username.strip():
            raise AuthenticationError(
                "Username and password are required."
            )

        if not isinstance(password, str) or not password:
            raise AuthenticationError(
                "Username and password are required."
            )

        username = username.strip()

        try:
            user = self._user_repository.get_by_username(username)

        except RepositoryError as exc:
            raise AuthenticationError(
                "Unable to access authentication data."
            ) from exc

        if user is None:
            raise AuthenticationError(
                "Invalid username or password."
            )

        if not user.is_active:
            raise AuthenticationError(
                "This user account is inactive."
            )

        if not PasswordHasher.verify_password(
            password,
            user.password_hash,
        ):
            raise AuthenticationError(
                "Invalid username or password."
            )

        self._current_session = UserSession(user=user)

        return self._current_session

    def logout(self) -> None:
        """End the current authenticated session."""

        if self._current_session is not None:
            self._current_session.logout()

        self._current_session = None

    def get_current_session(self) -> Optional[UserSession]:
        """Return the current authenticated session."""

        if self._current_session is None:
            return None

        if not self._current_session.authenticated:
            return None

        return self._current_session

    @staticmethod
    def create_session(user: User) -> UserSession:
        """Create a session for an already authenticated user."""

        if not user.is_active:
            raise AuthenticationError(
                "Inactive users cannot create a session."
            )

        return UserSession(user=user)

    @classmethod
    def _validate_username(cls, username: str) -> str:
        """Validate a username."""

        if not isinstance(username, str):
            raise RegistrationError("Username must be text.")

        username = username.strip()

        if not username:
            raise RegistrationError("Username cannot be empty.")

        if len(username) < 3:
            raise RegistrationError(
                "Username must contain at least 3 characters."
            )

        if len(username) > 50:
            raise RegistrationError(
                "Username cannot exceed 50 characters."
            )

        if not re.fullmatch(r"[A-Za-z0-9_.-]+", username):
            raise RegistrationError(
                "Username may contain only letters, numbers, "
                "underscore, period and hyphen."
            )

        return username

    @staticmethod
    def _validate_password(password: str) -> str:
        """Validate a registration password."""

        if not isinstance(password, str):
            raise RegistrationError("Password must be text.")

        if not password:
            raise RegistrationError("Password cannot be empty.")

        if len(password) < 8:
            raise RegistrationError(
                "Password must contain at least 8 characters."
            )

        if len(password) > 128:
            raise RegistrationError(
                "Password cannot exceed 128 characters."
            )

        return password

    @classmethod
    def _validate_role(cls, role_name: str) -> str:
        """Validate a supported system role."""

        if not isinstance(role_name, str):
            raise RegistrationError("Role must be text.")

        role_name = role_name.strip()

        if role_name.lower() not in cls.ALLOWED_ROLES:
            raise RegistrationError(
                "Invalid role. Allowed roles are "
                "Administrator, Manager and Staff/Cashier."
            )

        return role_name