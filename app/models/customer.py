from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    """Represents a restaurant customer."""

    name: str
    customer_id: Optional[int] = None
    phone: str = ""
    email: str = ""

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.phone = self.phone.strip()
        self.email = self.email.strip()

        if not self.name:
            raise ValueError("Customer name cannot be empty.")