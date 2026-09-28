from __future__ import annotations

from typing import Optional

from app.business.authorization_service import (
    AuthorizationService,
    Permission,
)
from app.data_access.repositories import (
    CustomerRepository,
    RepositoryError,
)
from app.exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
    ValidationError,
)
from app.models.customer import Customer
from app.models.user import UserSession
from app.validation.validators import Validator


class CustomerService:
    """Business service for customer management."""

    def __init__(
        self,
        repository: CustomerRepository,
    ) -> None:
        self._repository = repository

    # ========================================================
    # AUTHORIZATION
    # ========================================================

    @staticmethod
    def _require_customer_access(
        session: UserSession | None,
    ):
        """
        Require an authenticated user with customer-view
        permission.

        The existing RBAC configuration grants VIEW_CUSTOMERS
        to Administrator and Manager.
        """

        return AuthorizationService.require_permission_for_session(
            session,
            Permission.VIEW_CUSTOMERS,
        )

    # ========================================================
    # CREATE
    # ========================================================

    def create_customer(
        self,
        session: UserSession | None,
        name: str,
        phone: str = "",
        email: str = "",
    ) -> Customer:
        """Create a new customer."""

        self._require_customer_access(session)

        validated_name = Validator.required(
            name,
            "Customer name",
        )

        validated_phone = Validator.phone(
            phone,
            "Phone",
        )

        validated_email = Validator.email(
            email,
            "Email",
        )

        customer = Customer(
            name=validated_name,
            phone=validated_phone,
            email=validated_email,
        )

        try:
            return self._repository.create(customer)

        except RepositoryError:
            raise

        except ValueError as exc:
            raise ValidationError(
                f"Invalid customer information: {exc}"
            ) from exc

    # ========================================================
    # READ
    # ========================================================

    def get_customer(
        self,
        session: UserSession | None,
        customer_id: int,
    ) -> Customer:
        """Retrieve a customer by ID."""

        self._require_customer_access(session)

        validated_id = Validator.positive_integer(
            customer_id,
            "Customer ID",
        )

        customer = self._repository.get_by_id(
            validated_id
        )

        if customer is None:
            raise ResourceNotFoundError(
                f"Customer with ID {validated_id} was not found."
            )

        return customer

    def get_all_customers(
        self,
        session: UserSession | None,
    ) -> list[Customer]:
        """Retrieve all customers."""

        self._require_customer_access(session)

        return self._repository.get_all()

    # ========================================================
    # SEARCH
    # ========================================================

    def search_customers(
        self,
        session: UserSession | None,
        search_term: str,
    ) -> list[Customer]:
        """
        Search customers by name, phone, or email.

        This method is also available for future order
        processing where an existing customer must be found.
        """

        self._require_customer_access(session)

        term = Validator.required(
            search_term,
            "Search term",
        )

        return self._repository.search(term)

    # ========================================================
    # UPDATE
    # ========================================================

    def update_customer(
        self,
        session: UserSession | None,
        customer_id: int,
        name: str,
        phone: str = "",
        email: str = "",
    ) -> Customer:
        """Update an existing customer."""

        self._require_customer_access(session)

        validated_id = Validator.positive_integer(
            customer_id,
            "Customer ID",
        )

        validated_name = Validator.required(
            name,
            "Customer name",
        )

        validated_phone = Validator.phone(
            phone,
            "Phone",
        )

        validated_email = Validator.email(
            email,
            "Email",
        )

        existing_customer = self._repository.get_by_id(
            validated_id
        )

        if existing_customer is None:
            raise ResourceNotFoundError(
                f"Customer with ID {validated_id} was not found."
            )

        updated_customer = Customer(
            customer_id=validated_id,
            name=validated_name,
            phone=validated_phone,
            email=validated_email,
        )

        try:
            success = self._repository.update(
                updated_customer
            )

        except RepositoryError:
            raise

        if not success:
            raise ResourceNotFoundError(
                f"Customer with ID {validated_id} was not found."
            )

        return updated_customer

    # ========================================================
    # DELETE
    # ========================================================

    def delete_customer(
        self,
        session: UserSession | None,
        customer_id: int,
    ) -> bool:
        """Delete an existing customer."""

        self._require_customer_access(session)

        validated_id = Validator.positive_integer(
            customer_id,
            "Customer ID",
        )

        customer = self._repository.get_by_id(
            validated_id
        )

        if customer is None:
            raise ResourceNotFoundError(
                f"Customer with ID {validated_id} was not found."
            )

        try:
            return self._repository.delete(
                validated_id
            )

        except RepositoryError as exc:
            raise BusinessRuleError(
                "Customer cannot be deleted because it may "
                "be referenced by an existing order."
            ) from exc