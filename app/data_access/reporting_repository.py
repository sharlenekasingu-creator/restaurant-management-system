from __future__ import annotations

import sqlite3
from typing import Any

from app.data_access.database import DatabaseManager


class ReportingRepositoryError(Exception):
    """Raised when a reporting database operation fails."""


class ReportingRepository:
    """
    Data-access repository for operational reports.

    This repository only retrieves persisted information from the
    SQLite database. Business rules and authorization remain in
    the reporting service.
    """

    def __init__(
        self,
        database: DatabaseManager,
    ) -> None:
        self._database = database

    # ============================================================
    # INTERNAL QUERY HELPER
    # ============================================================

    def _fetch_all(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[sqlite3.Row]:
        """
        Execute a parameterized SELECT query and return all rows.
        """

        connection = None

        try:
            connection = self._database.connect()

            return connection.execute(
                query,
                parameters,
            ).fetchall()

        except sqlite3.Error as exc:
            raise ReportingRepositoryError(
                f"Database query failed: {exc}"
            ) from exc

        finally:
            if connection is not None:
                connection.close()

    # ============================================================
    # SALES REPORT
    # ============================================================

    def get_sales_report(
        self,
    ) -> list[sqlite3.Row]:
        """
        Retrieve completed sales/payment records.

        Only completed payments are treated as sales.
        """

        query = """
            SELECT
                payment_id,
                order_id,
                amount,
                payment_method,
                status
            FROM payments
            WHERE status = ?
            ORDER BY payment_id
        """

        return self._fetch_all(
            query,
            ("Completed",),
        )

    # ============================================================
    # ORDER REPORT
    # ============================================================

    def get_order_report(
        self,
    ) -> list[sqlite3.Row]:
        """
        Retrieve order counts grouped by order status.
        """

        query = """
            SELECT
                status,
                COUNT(*) AS order_count
            FROM orders
            GROUP BY status
            ORDER BY status
        """

        return self._fetch_all(query)

    # ============================================================
    # MENU PERFORMANCE REPORT
    # ============================================================

    def get_menu_performance_report(
        self,
    ) -> list[sqlite3.Row]:
        """
        Retrieve menu-item sales performance.

        Quantity sold and revenue are calculated from completed
        orders only.
        """

        query = """
            SELECT
                mi.item_id,
                mi.name AS item_name,
                mc.name AS category_name,
                COALESCE(
                    SUM(
                        CASE
                            WHEN o.status = ?
                            THEN oi.quantity
                            ELSE 0
                        END
                    ),
                    0
                ) AS quantity_sold,
                COALESCE(
                    SUM(
                        CASE
                            WHEN o.status = ?
                            THEN oi.quantity * mi.price
                            ELSE 0
                        END
                    ),
                    0
                ) AS revenue
            FROM menu_items mi

            INNER JOIN menu_categories mc
                ON mi.category_id = mc.category_id

            LEFT JOIN order_items oi
                ON mi.item_id = oi.item_id

            LEFT JOIN orders o
                ON oi.order_id = o.order_id

            GROUP BY
                mi.item_id,
                mi.name,
                mc.name

            ORDER BY
                mi.item_id
        """

        return self._fetch_all(
            query,
            (
                "Completed",
                "Completed",
            ),
        )

    # ============================================================
    # INVENTORY REPORT
    # ============================================================

    def get_inventory_report(
        self,
        low_stock_threshold: float,
    ) -> list[sqlite3.Row]:
        """
        Retrieve all inventory records and calculate whether
        each item is at or below the supplied low-stock threshold.
        """

        query = """
            SELECT
                i.inventory_id,
                i.name AS item_name,
                i.quantity,
                i.unit,
                s.name AS supplier_name,

                CASE
                    WHEN i.quantity <= ?
                    THEN 1
                    ELSE 0
                END AS is_low_stock

            FROM inventory i

            LEFT JOIN suppliers s
                ON i.supplier_id = s.supplier_id

            ORDER BY
                i.inventory_id
        """

        return self._fetch_all(
            query,
            (low_stock_threshold,),
        )