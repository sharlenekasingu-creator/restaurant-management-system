from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Payment:
    """Represents a payment associated with an order."""

    amount: Decimal
    payment_method: str
    payment_id: Optional[int] = None
    order_id: Optional[int] = None
    status: str = "Pending"

    def __post_init__(self) -> None:
        self.payment_method = self.payment_method.strip()
        self.status = self.status.strip()

        if self.amount <= Decimal("0"):
            raise ValueError("Payment amount must be greater than zero.")

        if not self.payment_method:
            raise ValueError("Payment method cannot be empty.")

        if not self.status:
            raise ValueError("Payment status cannot be empty.")

    def mark_completed(self) -> None:
        """Mark payment as completed."""
        self.status = "Completed"

    def mark_failed(self) -> None:
        """Mark payment as failed."""
        self.status = "Failed"