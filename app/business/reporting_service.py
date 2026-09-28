from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict

from app.business.authorization_service import (
    AuthorizationService,
    Permission,
)
from app.data_access.reporting_repository import (
    ReportingRepository,
    ReportingRepositoryError,
)
from app.models.user import UserSession


class ReportingService(ABC):
    """Abstraction for reporting functionality."""

    @abstractmethod
    def generate_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """Generate a complete operational report."""
        raise NotImplementedError

    @abstractmethod
    def get_sales_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """Generate the sales report."""
        raise NotImplementedError

    @abstractmethod
    def get_order_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """Generate the order report."""
        raise NotImplementedError

    @abstractmethod
    def get_menu_performance_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """Generate the menu-performance report."""
        raise NotImplementedError

    @abstractmethod
    def get_inventory_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """Generate the inventory report."""
        raise NotImplementedError


class BasicReportingService(ReportingService):
    """
    Operational reporting service for Phase 12.

    Reports use persisted database information through the
    ReportingRepository and are protected by the existing
    VIEW_REPORTS permission.
    """

    LOW_STOCK_THRESHOLD = 10

    def __init__(
        self,
        repository: ReportingRepository,
    ) -> None:
        self._repository = repository

    # ============================================================
    # AUTHORIZATION
    # ============================================================

    @staticmethod
    def _require_report_access(
        session: UserSession | None,
    ) -> None:
        """
        Require an authenticated user with report-viewing
        permission.
        """

        AuthorizationService.require_permission_for_session(
            session,
            Permission.VIEW_REPORTS,
        )

    # ============================================================
    # COMPLETE REPORT
    # ============================================================

    def generate_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """
        Generate all Phase 12 operational reports.

        This method is retained for compatibility with the
        original ReportingService abstraction.
        """

        self._require_report_access(session)

        return {
            "sales": self.get_sales_report(session),
            "orders": self.get_order_report(session),
            "menu_performance": (
                self.get_menu_performance_report(session)
            ),
            "inventory": self.get_inventory_report(session),
        }

    # ============================================================
    # SALES REPORT
    # ============================================================

    def get_sales_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """Generate the operational sales report."""

        self._require_report_access(session)

        try:
            rows = self._repository.get_sales_report()

            records = []
            total_sales = Decimal("0.00")

            for row in rows:
                amount = Decimal(str(row["amount"]))

                records.append(
                    {
                        "payment_id": row["payment_id"],
                        "order_id": row["order_id"],
                        "amount": amount,
                        "payment_method": row[
                            "payment_method"
                        ],
                        "status": row["status"],
                    }
                )

                total_sales += amount

            return {
                "records": records,
                "total_sales": total_sales,
            }

        except ReportingRepositoryError as exc:
            raise ReportingServiceError(
                f"Unable to generate sales report: {exc}"
            ) from exc

    # ============================================================
    # ORDER REPORT
    # ============================================================

    def get_order_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """Generate the operational order report."""

        self._require_report_access(session)

        try:
            rows = self._repository.get_order_report()

            records = []
            total_orders = 0

            for row in rows:
                order_count = int(
                    row["order_count"]
                )

                records.append(
                    {
                        "status": row["status"],
                        "order_count": order_count,
                    }
                )

                total_orders += order_count

            return {
                "records": records,
                "total_orders": total_orders,
            }

        except ReportingRepositoryError as exc:
            raise ReportingServiceError(
                f"Unable to generate order report: {exc}"
            ) from exc

    # ============================================================
    # MENU PERFORMANCE REPORT
    # ============================================================

    def get_menu_performance_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """Generate the menu-performance report."""

        self._require_report_access(session)

        try:
            rows = (
                self._repository
                .get_menu_performance_report()
            )

            records = []

            for row in rows:
                records.append(
                    {
                        "item_id": row["item_id"],
                        "item_name": row["item_name"],
                        "category_name": row[
                            "category_name"
                        ],
                        "quantity_sold": int(
                            row["quantity_sold"]
                        ),
                        "revenue": Decimal(
                            str(row["revenue"])
                        ),
                    }
                )

            return {
                "records": records,
            }

        except ReportingRepositoryError as exc:
            raise ReportingServiceError(
                "Unable to generate menu-performance "
                f"report: {exc}"
            ) from exc

    # ============================================================
    # INVENTORY REPORT
    # ============================================================

    def get_inventory_report(
        self,
        session: UserSession | None,
    ) -> Dict[str, Any]:
        """Generate the operational inventory report."""

        self._require_report_access(session)

        try:
            rows = self._repository.get_inventory_report(
                low_stock_threshold=self.LOW_STOCK_THRESHOLD
            )

            records = []

            for row in rows:
                records.append(
                    {
                        "inventory_id": row[
                            "inventory_id"
                        ],
                        "item_name": row["item_name"],
                        "quantity": float(
                            row["quantity"]
                        ),
                        "unit": row["unit"],
                        "supplier_name": row[
                            "supplier_name"
                        ],
                        "is_low_stock": bool(
                            row["is_low_stock"]
                        ),
                    }
                )

            return {
                "records": records,
                "low_stock_threshold": (
                    self.LOW_STOCK_THRESHOLD
                ),
            }

        except ReportingRepositoryError as exc:
            raise ReportingServiceError(
                f"Unable to generate inventory report: {exc}"
            ) from exc


class ReportingServiceError(Exception):
    """Raised when a reporting business operation fails."""