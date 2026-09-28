from __future__ import annotations

import getpass

from app.business.authentication_service import (
    AuthenticationServiceImplementation,
    RegistrationError,
)
from app.data_access.database import DatabaseManager
from app.data_access.repositories import RoleRepository, UserRepository


def main() -> int:
    """Interactively create a user without storing a plaintext password."""
    database = DatabaseManager()

    if not database.database_exists():
        print("Database does not exist. Run: python main.py --init-db")
        return 1

    service = AuthenticationServiceImplementation(
        user_repository=UserRepository(database),
        role_repository=RoleRepository(database),
    )

    print("Create RMS User")
    print("================")
    username = input("Username: ").strip()
    full_name = input("Full name: ").strip()
    email = input("Email: ").strip()
    role = input("Role (Administrator/Manager/Staff/Cashier): ").strip()
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")

    if password != confirmation:
        print("Passwords do not match.")
        return 1

    try:
        user = service.register_user(
            username=username,
            password=password,
            role_name=role,
            full_name=full_name,
            email=email,
        )
    except RegistrationError as exc:
        print(f"Unable to create user: {exc}")
        return 1

    print(f"User '{user.username}' created successfully.")
    print(f"Role: {user.role.name}")
    print("The password is stored only as a secure password hash.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
