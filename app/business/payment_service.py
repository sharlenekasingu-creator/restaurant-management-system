from __future__ import annotations

from decimal import Decimal

from app.business.authorization_service import (
    AuthorizationService,
    Permission,
)
from app.data_access.repositories import PaymentRepository
from app.models.payment import Payment
from app.models.user import UserSession


class PaymentService:
    """Business service for authorized payment processing."""

    def __init__(self, repository: PaymentRepository) -> None:
        self._repository = repository

    @staticmethod
    def _require_payment_access(session: UserSession | None) -> None:
        """Require an authenticated user with payment permission."""
        AuthorizationService.require_permission_for_session(
            session,
            Permission.PROCESS_PAYMENTS,
        )

    def create_payment(
        self,
        session: UserSession | None,
        amount: Decimal,
        payment_method: str,
        order_id: int | None = None,
    ) -> Payment:
        """Create a payment for an authorized user."""
        self._require_payment_access(session)

        payment = Payment(
            amount=amount,
            payment_method=payment_method,
            order_id=order_id,
        )

        return self._repository.create(payment)

    def complete_payment(
        self,
        session: UserSession | None,
        payment: Payment,
    ) -> None:
        """Complete a payment for an authorized user."""
        self._require_payment_access(session)

        payment.mark_completed()

        updated = self._repository.update(payment)

        if not updated:
            raise ValueError(
                "Payment could not be updated."
            )

    def fail_payment(
        self,
        session: UserSession | None,
        payment: Payment,
    ) -> None:
        """Mark a payment as failed for an authorized user."""
        self._require_payment_access(session)
        payment.mark_failed()
