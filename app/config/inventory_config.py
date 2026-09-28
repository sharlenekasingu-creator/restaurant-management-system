from __future__ import annotations

from dataclasses import dataclass


# Default low-stock threshold used across the RMS.
# Items with quantity less than or equal to this value are considered low stock.
DEFAULT_LOW_STOCK_THRESHOLD: float | None = 10


@dataclass(frozen=True)
class InventorySettings:
    """Configuration for inventory management."""

    low_stock_threshold: float | None = DEFAULT_LOW_STOCK_THRESHOLD

    def __post_init__(self) -> None:
        if self.low_stock_threshold is not None:
            try:
                threshold = float(self.low_stock_threshold)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Low-stock threshold must be a valid number."
                ) from exc

            if threshold < 0:
                raise ValueError(
                    "Low-stock threshold cannot be negative."
                ) from None