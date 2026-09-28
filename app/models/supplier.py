from dataclasses import dataclass
from typing import Optional


@dataclass
class Supplier:
    """Represents a supplier."""

    name: str
    supplier_id: Optional[int] = None
    phone: str = ""
    email: str = ""
    address: str = ""

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.phone = self.phone.strip()
        self.email = self.email.strip()
        self.address = self.address.strip()

        if not self.name:
            raise ValueError("Supplier name cannot be empty.")