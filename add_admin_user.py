from app.data_access.database import DatabaseManager
from app.data_access.repositories import UserRepository, RoleRepository
from app.business.authentication_service import (
    AuthenticationServiceImplementation,
    RegistrationError,
)


def main() -> None:
    database = DatabaseManager()

    user_repository = UserRepository(database)
    role_repository = RoleRepository(database)

    authentication_service = AuthenticationServiceImplementation(
        user_repository=user_repository,
        role_repository=role_repository,
    )
    import getpass

    username = "admin"
    password = getpass.getpass("Enter password for admin user: ")
    role_name = "Administrator"


    existing_user = user_repository.get_by_username(username)

    if existing_user is not None:
        print(f"User '{username}' already exists.")
        return

    try:
        user = authentication_service.register_user(
            username=username,
            password=password,
            role_name=role_name,
            full_name="System Administrator",
            email="admin@restaurant.local",
        )

        print("Administrator account created successfully.")
        print(f"Username: {user.username}")
        print("Password: Admin123")
        print(f"Role: {user.role.name}")

    except RegistrationError as exc:
        print(f"Unable to create administrator: {exc}")


if __name__ == "__main__":
    main()