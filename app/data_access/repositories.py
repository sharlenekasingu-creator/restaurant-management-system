from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Optional

from app.data_access.database import DatabaseManager
from app.models import (
    Customer,
    Inventory,
    MenuCategory,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    Role,
    Supplier,
    User,
)


class RepositoryError(Exception):
    """Raised when a repository operation fails."""


class BaseRepository(ABC):
    """Base class for SQLite repositories."""

    def __init__(self, database: DatabaseManager) -> None:
        self._database = database

    def _execute(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> sqlite3.Cursor:
        """Execute an INSERT, UPDATE, or DELETE statement."""
        connection = None

        try:
            connection = self._database.connect()

            cursor = connection.execute(
                query,
                parameters,
            )

            connection.commit()

            return cursor

        except sqlite3.Error as exc:
            if connection is not None:
                connection.rollback()

            raise RepositoryError(
                f"Database operation failed: {exc}"
            ) from exc

        finally:
            if connection is not None:
                connection.close()

    def _fetch_one(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> Optional[sqlite3.Row]:
        """Execute a SELECT statement and return one row."""
        connection = None

        try:
            connection = self._database.connect()

            return connection.execute(
                query,
                parameters,
            ).fetchone()

        except sqlite3.Error as exc:
            raise RepositoryError(
                f"Database query failed: {exc}"
            ) from exc

        finally:
            if connection is not None:
                connection.close()

    def _fetch_all(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[sqlite3.Row]:
        """Execute a SELECT statement and return all rows."""
        connection = None

        try:
            connection = self._database.connect()

            return connection.execute(
                query,
                parameters,
            ).fetchall()

        except sqlite3.Error as exc:
            raise RepositoryError(
                f"Database query failed: {exc}"
            ) from exc

        finally:
            if connection is not None:
                connection.close()

    @abstractmethod
    def create(self, entity: Any) -> Any:
        """Create a database record."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, record_id: int) -> Any:
        """Retrieve a record by ID."""
        raise NotImplementedError

    @abstractmethod
    def update(self, entity: Any) -> bool:
        """Update a database record."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """Delete a database record."""
        raise NotImplementedError


# ============================================================
# ROLE REPOSITORY
# ============================================================

class RoleRepository(BaseRepository):
    """Repository for Role objects."""

    def create(self, role: Role) -> Role:
        cursor = self._execute(
            """
            INSERT INTO roles (name, description)
            VALUES (?, ?)
            """,
            (
                role.name,
                role.description,
            ),
        )

        role.role_id = int(cursor.lastrowid)

        return role

    def get_by_id(self, role_id: int) -> Optional[Role]:
        row = self._fetch_one(
            """
            SELECT role_id, name, description
            FROM roles
            WHERE role_id = ?
            """,
            (role_id,),
        )

        if row is None:
            return None

        return Role(
            role_id=row["role_id"],
            name=row["name"],
            description=row["description"],
        )

    def get_by_name(self, name: str) -> Optional[Role]:
        row = self._fetch_one(
            """
            SELECT role_id, name, description
            FROM roles
            WHERE name = ?
            """,
            (name,),
        )

        if row is None:
            return None

        return Role(
            role_id=row["role_id"],
            name=row["name"],
            description=row["description"],
        )

    def get_all(self) -> list[Role]:
        rows = self._fetch_all(
            """
            SELECT role_id, name, description
            FROM roles
            ORDER BY role_id
            """
        )

        return [
            Role(
                role_id=row["role_id"],
                name=row["name"],
                description=row["description"],
            )
            for row in rows
        ]

    def update(self, role: Role) -> bool:
        if role.role_id is None:
            raise RepositoryError(
                "Cannot update a role without a role ID."
            )

        cursor = self._execute(
            """
            UPDATE roles
            SET name = ?, description = ?
            WHERE role_id = ?
            """,
            (
                role.name,
                role.description,
                role.role_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, role_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM roles
            WHERE role_id = ?
            """,
            (role_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# USER REPOSITORY
# ============================================================

class UserRepository(BaseRepository):
    """Repository for User objects."""

    def create(self, user: User) -> User:
        if user.role.role_id is None:
            raise RepositoryError(
                "User role must have a valid role ID."
            )

        cursor = self._execute(
            """
            INSERT INTO users
                (
                    username,
                    password_hash,
                    role_id,
                    full_name,
                    email,
                    is_active
                )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user.username,
                user.password_hash,
                user.role.role_id,
                user.full_name,
                user.email,
                int(user.is_active),
            ),
        )

        user.user_id = int(cursor.lastrowid)

        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        row = self._fetch_one(
            """
            SELECT
                u.user_id,
                u.username,
                u.password_hash,
                u.role_id,
                u.full_name,
                u.email,
                u.is_active,
                r.name AS role_name,
                r.description AS role_description
            FROM users u
            INNER JOIN roles r
                ON u.role_id = r.role_id
            WHERE u.user_id = ?
            """,
            (user_id,),
        )

        if row is None:
            return None

        role = Role(
            role_id=row["role_id"],
            name=row["role_name"],
            description=row["role_description"],
        )

        return User(
            username=row["username"],
            password_hash=row["password_hash"],
            role=role,
            user_id=row["user_id"],
            full_name=row["full_name"],
            email=row["email"],
            is_active=bool(row["is_active"]),
        )

    def get_by_username(
        self,
        username: str,
    ) -> Optional[User]:
        row = self._fetch_one(
            """
            SELECT
                u.user_id,
                u.username,
                u.password_hash,
                u.role_id,
                u.full_name,
                u.email,
                u.is_active,
                r.name AS role_name,
                r.description AS role_description
            FROM users u
            INNER JOIN roles r
                ON u.role_id = r.role_id
            WHERE u.username = ?
            """,
            (username,),
        )

        if row is None:
            return None

        role = Role(
            role_id=row["role_id"],
            name=row["role_name"],
            description=row["role_description"],
        )

        return User(
            username=row["username"],
            password_hash=row["password_hash"],
            role=role,
            user_id=row["user_id"],
            full_name=row["full_name"],
            email=row["email"],
            is_active=bool(row["is_active"]),
        )

    def get_all(self) -> list[User]:
        rows = self._fetch_all(
            """
            SELECT
                u.user_id,
                u.username,
                u.password_hash,
                u.role_id,
                u.full_name,
                u.email,
                u.is_active,
                r.name AS role_name,
                r.description AS role_description
            FROM users u
            INNER JOIN roles r
                ON u.role_id = r.role_id
            ORDER BY u.user_id
            """
        )

        users = []

        for row in rows:
            role = Role(
                role_id=row["role_id"],
                name=row["role_name"],
                description=row["role_description"],
            )

            users.append(
                User(
                    username=row["username"],
                    password_hash=row["password_hash"],
                    role=role,
                    user_id=row["user_id"],
                    full_name=row["full_name"],
                    email=row["email"],
                    is_active=bool(row["is_active"]),
                )
            )

        return users

    def update(self, user: User) -> bool:
        if user.user_id is None:
            raise RepositoryError(
                "Cannot update a user without a user ID."
            )

        if user.role.role_id is None:
            raise RepositoryError(
                "User role must have a valid role ID."
            )

        cursor = self._execute(
            """
            UPDATE users
            SET
                username = ?,
                password_hash = ?,
                role_id = ?,
                full_name = ?,
                email = ?,
                is_active = ?
            WHERE user_id = ?
            """,
            (
                user.username,
                user.password_hash,
                user.role.role_id,
                user.full_name,
                user.email,
                int(user.is_active),
                user.user_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, user_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# MENU CATEGORY REPOSITORY
# ============================================================

class MenuCategoryRepository(BaseRepository):
    """Repository for MenuCategory objects."""

    def create(self, category: MenuCategory) -> MenuCategory:
        cursor = self._execute(
            """
            INSERT INTO menu_categories
                (name, description)
            VALUES (?, ?)
            """,
            (
                category.name,
                category.description,
            ),
        )

        category.category_id = int(cursor.lastrowid)

        return category

    def get_by_id(
        self,
        category_id: int,
    ) -> Optional[MenuCategory]:
        row = self._fetch_one(
            """
            SELECT category_id, name, description
            FROM menu_categories
            WHERE category_id = ?
            """,
            (category_id,),
        )

        if row is None:
            return None

        return MenuCategory(
            name=row["name"],
            category_id=row["category_id"],
            description=row["description"],
        )

    def get_by_name(
        self,
        name: str,
    ) -> Optional[MenuCategory]:
        row = self._fetch_one(
            """
            SELECT category_id, name, description
            FROM menu_categories
            WHERE name = ?
            """,
            (name,),
        )

        if row is None:
            return None

        return MenuCategory(
            name=row["name"],
            category_id=row["category_id"],
            description=row["description"],
        )

    def get_all(self) -> list[MenuCategory]:
        rows = self._fetch_all(
            """
            SELECT category_id, name, description
            FROM menu_categories
            ORDER BY category_id
            """
        )

        return [
            MenuCategory(
                name=row["name"],
                category_id=row["category_id"],
                description=row["description"],
            )
            for row in rows
        ]

    def update(self, category: MenuCategory) -> bool:
        if category.category_id is None:
            raise RepositoryError(
                "Cannot update a category without an ID."
            )

        cursor = self._execute(
            """
            UPDATE menu_categories
            SET name = ?, description = ?
            WHERE category_id = ?
            """,
            (
                category.name,
                category.description,
                category.category_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, category_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM menu_categories
            WHERE category_id = ?
            """,
            (category_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# MENU ITEM REPOSITORY
# ============================================================

class MenuItemRepository(BaseRepository):
    """Repository for MenuItem objects."""

    def create(self, item: MenuItem) -> MenuItem:
        if item.category.category_id is None:
            raise RepositoryError(
                "Menu item category must have a valid ID."
            )

        cursor = self._execute(
            """
            INSERT INTO menu_items
                (
                    name,
                    price,
                    category_id,
                    description,
                    is_available
                )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                item.name,
                str(item.price),
                item.category.category_id,
                item.description,
                int(item.is_available),
            ),
        )

        item.item_id = int(cursor.lastrowid)

        return item

    def get_by_id(
        self,
        item_id: int,
    ) -> Optional[MenuItem]:
        row = self._fetch_one(
            """
            SELECT
                mi.item_id,
                mi.name,
                mi.price,
                mi.category_id,
                mi.description,
                mi.is_available,
                mc.name AS category_name,
                mc.description AS category_description
            FROM menu_items mi
            INNER JOIN menu_categories mc
                ON mi.category_id = mc.category_id
            WHERE mi.item_id = ?
            """,
            (item_id,),
        )

        if row is None:
            return None

        category = MenuCategory(
            name=row["category_name"],
            category_id=row["category_id"],
            description=row["category_description"],
        )

        return MenuItem(
            name=row["name"],
            price=Decimal(str(row["price"])),
            category=category,
            item_id=row["item_id"],
            description=row["description"],
            is_available=bool(row["is_available"]),
        )

    def get_all(self) -> list[MenuItem]:
        rows = self._fetch_all(
            """
            SELECT
                mi.item_id,
                mi.name,
                mi.price,
                mi.category_id,
                mi.description,
                mi.is_available,
                mc.name AS category_name,
                mc.description AS category_description
            FROM menu_items mi
            INNER JOIN menu_categories mc
                ON mi.category_id = mc.category_id
            ORDER BY mi.item_id
            """
        )

        return [
            self._row_to_menu_item(row)
            for row in rows
        ]

    def get_by_category(
        self,
        category_id: int,
    ) -> list[MenuItem]:
        rows = self._fetch_all(
            """
            SELECT
                mi.item_id,
                mi.name,
                mi.price,
                mi.category_id,
                mi.description,
                mi.is_available,
                mc.name AS category_name,
                mc.description AS category_description
            FROM menu_items mi
            INNER JOIN menu_categories mc
                ON mi.category_id = mc.category_id
            WHERE mi.category_id = ?
            ORDER BY mi.item_id
            """,
            (category_id,),
        )

        return [
            self._row_to_menu_item(row)
            for row in rows
        ]

    def _row_to_menu_item(
        self,
        row: sqlite3.Row,
    ) -> MenuItem:
        category = MenuCategory(
            name=row["category_name"],
            category_id=row["category_id"],
            description=row["category_description"],
        )

        return MenuItem(
            name=row["name"],
            price=Decimal(str(row["price"])),
            category=category,
            item_id=row["item_id"],
            description=row["description"],
            is_available=bool(row["is_available"]),
        )

    def update(self, item: MenuItem) -> bool:
        if item.item_id is None:
            raise RepositoryError(
                "Cannot update a menu item without an ID."
            )

        if item.category.category_id is None:
            raise RepositoryError(
                "Menu item category must have a valid ID."
            )

        cursor = self._execute(
            """
            UPDATE menu_items
            SET
                name = ?,
                price = ?,
                category_id = ?,
                description = ?,
                is_available = ?
            WHERE item_id = ?
            """,
            (
                item.name,
                str(item.price),
                item.category.category_id,
                item.description,
                int(item.is_available),
                item.item_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, item_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM menu_items
            WHERE item_id = ?
            """,
            (item_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# CUSTOMER REPOSITORY
# ============================================================

class CustomerRepository(BaseRepository):
    """Repository for Customer objects."""

    def create(self, customer: Customer) -> Customer:
        cursor = self._execute(
            """
            INSERT INTO customers
                (name, phone, email)
            VALUES (?, ?, ?)
            """,
            (
                customer.name,
                customer.phone,
                customer.email,
            ),
        )

        customer.customer_id = int(cursor.lastrowid)

        return customer

    def get_by_id(
        self,
        customer_id: int,
    ) -> Optional[Customer]:
        row = self._fetch_one(
            """
            SELECT customer_id, name, phone, email
            FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        )

        if row is None:
            return None

        return Customer(
            name=row["name"],
            customer_id=row["customer_id"],
            phone=row["phone"],
            email=row["email"],
        )

    def get_all(self) -> list[Customer]:
        rows = self._fetch_all(
            """
            SELECT customer_id, name, phone, email
            FROM customers
            ORDER BY customer_id
            """
        )
        return [
            Customer(
                name=row["name"],
                customer_id=row["customer_id"],
                phone=row["phone"],
                email=row["email"],
            )
            for row in rows
        ]

    def search(
        self,
        search_term: str,
    ) -> list[Customer]:
        """Search customers by name, phone, or email."""

        pattern = f"%{search_term}%"

        rows = self._fetch_all(
            """
            SELECT customer_id, name, phone, email
            FROM customers
            WHERE name LIKE ?
               OR phone LIKE ?
               OR email LIKE ?
            ORDER BY customer_id
            """,
            (
                pattern,
                pattern,
                pattern,
            ),
        )

        return [
            Customer(
                name=row["name"],
                customer_id=row["customer_id"],
                phone=row["phone"],
                email=row["email"],
            )
            for row in rows
        ]    

        
    def update(self, customer: Customer) -> bool:
        if customer.customer_id is None:
            raise RepositoryError(
                "Cannot update a customer without an ID."
            )

        cursor = self._execute(
            """
            UPDATE customers
            SET name = ?, phone = ?, email = ?
            WHERE customer_id = ?
            """,
            (
                customer.name,
                customer.phone,
                customer.email,
                customer.customer_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, customer_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM customers
            WHERE customer_id = ?
            """,
            (customer_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# SUPPLIER REPOSITORY
# ============================================================

class SupplierRepository(BaseRepository):
    """Repository for Supplier objects."""

    def create(self, supplier: Supplier) -> Supplier:
        cursor = self._execute(
            """
            INSERT INTO suppliers
                (name, phone, email, address)
            VALUES (?, ?, ?, ?)
            """,
            (
                supplier.name,
                supplier.phone,
                supplier.email,
                supplier.address,
            ),
        )

        supplier.supplier_id = int(cursor.lastrowid)

        return supplier

    def get_by_id(
        self,
        supplier_id: int,
    ) -> Optional[Supplier]:
        row = self._fetch_one(
            """
            SELECT
                supplier_id,
                name,
                phone,
                email,
                address
            FROM suppliers
            WHERE supplier_id = ?
            """,
            (supplier_id,),
        )

        if row is None:
            return None

        return Supplier(
            name=row["name"],
            supplier_id=row["supplier_id"],
            phone=row["phone"],
            email=row["email"],
            address=row["address"],
        )

    def get_all(self) -> list[Supplier]:
        rows = self._fetch_all(
            """
            SELECT
                supplier_id,
                name,
                phone,
                email,
                address
            FROM suppliers
            ORDER BY supplier_id
            """
        )

        return [
            Supplier(
                name=row["name"],
                supplier_id=row["supplier_id"],
                phone=row["phone"],
                email=row["email"],
                address=row["address"],
            )
            for row in rows
        ]

    def update(self, supplier: Supplier) -> bool:
        if supplier.supplier_id is None:
            raise RepositoryError(
                "Cannot update a supplier without an ID."
            )

        cursor = self._execute(
            """
            UPDATE suppliers
            SET
                name = ?,
                phone = ?,
                email = ?,
                address = ?
            WHERE supplier_id = ?
            """,
            (
                supplier.name,
                supplier.phone,
                supplier.email,
                supplier.address,
                supplier.supplier_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, supplier_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM suppliers
            WHERE supplier_id = ?
            """,
            (supplier_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# INVENTORY REPOSITORY
# ============================================================

class InventoryRepository(BaseRepository):
    """Repository for Inventory objects."""

    def create(self, inventory: Inventory) -> Inventory:
        supplier_id = None

        if inventory.supplier is not None:
            supplier_id = inventory.supplier.supplier_id

            if supplier_id is None:
                raise RepositoryError(
                    "Inventory supplier must have a valid ID."
                )

        cursor = self._execute(
            """
            INSERT INTO inventory
                (name, quantity, unit, supplier_id)
            VALUES (?, ?, ?, ?)
            """,
            (
                inventory.name,
                inventory.quantity,
                inventory.unit,
                supplier_id,
            ),
        )

        inventory.inventory_id = int(cursor.lastrowid)

        return inventory

    def get_by_id(
        self,
        inventory_id: int,
    ) -> Optional[Inventory]:
        row = self._fetch_one(
            """
            SELECT
                i.inventory_id,
                i.name,
                i.quantity,
                i.unit,
                i.supplier_id,
                s.name AS supplier_name,
                s.phone AS supplier_phone,
                s.email AS supplier_email,
                s.address AS supplier_address
            FROM inventory i
            LEFT JOIN suppliers s
                ON i.supplier_id = s.supplier_id
            WHERE i.inventory_id = ?
            """,
            (inventory_id,),
        )

        if row is None:
            return None

        supplier = None

        if row["supplier_id"] is not None:
            supplier = Supplier(
                name=row["supplier_name"],
                supplier_id=row["supplier_id"],
                phone=row["supplier_phone"],
                email=row["supplier_email"],
                address=row["supplier_address"],
            )

        return Inventory(
            name=row["name"],
            quantity=float(row["quantity"]),
            unit=row["unit"],
            inventory_id=row["inventory_id"],
            supplier=supplier,
        )

    def get_all(self) -> list[Inventory]:
        rows = self._fetch_all(
            """
            SELECT
                i.inventory_id,
                i.name,
                i.quantity,
                i.unit,
                i.supplier_id,
                s.name AS supplier_name,
                s.phone AS supplier_phone,
                s.email AS supplier_email,
                s.address AS supplier_address
            FROM inventory i
            LEFT JOIN suppliers s
                ON i.supplier_id = s.supplier_id
            ORDER BY i.inventory_id
            """
        )

        return [
            self._row_to_inventory(row)
            for row in rows
        ]

    def get_by_supplier(
        self,
        supplier_id: int,
    ) -> list[Inventory]:
        rows = self._fetch_all(
            """
            SELECT
                i.inventory_id,
                i.name,
                i.quantity,
                i.unit,
                i.supplier_id,
                s.name AS supplier_name,
                s.phone AS supplier_phone,
                s.email AS supplier_email,
                s.address AS supplier_address
            FROM inventory i
            LEFT JOIN suppliers s
                ON i.supplier_id = s.supplier_id
            WHERE i.supplier_id = ?
            ORDER BY i.inventory_id
            """,
            (supplier_id,),
        )

        return [
            self._row_to_inventory(row)
            for row in rows
        ]

    def _row_to_inventory(
        self,
        row: sqlite3.Row,
    ) -> Inventory:
        supplier = None

        if row["supplier_id"] is not None:
            supplier = Supplier(
                name=row["supplier_name"],
                supplier_id=row["supplier_id"],
                phone=row["supplier_phone"],
                email=row["supplier_email"],
                address=row["supplier_address"],
            )

        return Inventory(
            name=row["name"],
            quantity=float(row["quantity"]),
            unit=row["unit"],
            inventory_id=row["inventory_id"],
            supplier=supplier,
        )

    def update(self, inventory: Inventory) -> bool:
        if inventory.inventory_id is None:
            raise RepositoryError(
                "Cannot update inventory without an ID."
            )

        supplier_id = None

        if inventory.supplier is not None:
            supplier_id = inventory.supplier.supplier_id

            if supplier_id is None:
                raise RepositoryError(
                    "Inventory supplier must have a valid ID."
                )

        cursor = self._execute(
            """
            UPDATE inventory
            SET
                name = ?,
                quantity = ?,
                unit = ?,
                supplier_id = ?
            WHERE inventory_id = ?
            """,
            (
                inventory.name,
                inventory.quantity,
                inventory.unit,
                supplier_id,
                inventory.inventory_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, inventory_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM inventory
            WHERE inventory_id = ?
            """,
            (inventory_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# ORDER REPOSITORY
# ============================================================

class OrderRepository(BaseRepository):
    """Repository for Order objects."""

    def create(self, order: Order) -> Order:
        if order.customer.customer_id is None:
            raise RepositoryError(
                "Order customer must have a valid ID."
            )

        cursor = self._execute(
            """
            INSERT INTO orders
                (customer_id, status)
            VALUES (?, ?)
            """,
            (
                order.customer.customer_id,
                order.status,
            ),
        )

        order.order_id = int(cursor.lastrowid)

        return order

    def get_by_id(
        self,
        order_id: int,
    ) -> Optional[Order]:
        row = self._fetch_one(
            """
            SELECT
                o.order_id,
                o.customer_id,
                o.status,
                c.name AS customer_name,
                c.phone AS customer_phone,
                c.email AS customer_email
            FROM orders o
            INNER JOIN customers c
                ON o.customer_id = c.customer_id
            WHERE o.order_id = ?
            """,
            (order_id,),
        )

        if row is None:
            return None

        customer = Customer(
            name=row["customer_name"],
            customer_id=row["customer_id"],
            phone=row["customer_phone"],
            email=row["customer_email"],
        )

        return Order(
            customer=customer,
            order_id=row["order_id"],
            status=row["status"],
            items=[],
        )

    def get_all(self) -> list[Order]:
        rows = self._fetch_all(
            """
            SELECT
                o.order_id,
                o.customer_id,
                o.status,
                c.name AS customer_name,
                c.phone AS customer_phone,
                c.email AS customer_email
            FROM orders o
            INNER JOIN customers c
                ON o.customer_id = c.customer_id
            ORDER BY o.order_id
            """
        )

        return [
            self._row_to_order(row)
            for row in rows
        ]

    def get_by_customer(
        self,
        customer_id: int,
    ) -> list[Order]:
        rows = self._fetch_all(
            """
            SELECT
                o.order_id,
                o.customer_id,
                o.status,
                c.name AS customer_name,
                c.phone AS customer_phone,
                c.email AS customer_email
            FROM orders o
            INNER JOIN customers c
                ON o.customer_id = c.customer_id
            WHERE o.customer_id = ?
            ORDER BY o.order_id
            """,
            (customer_id,),
        )

        return [
            self._row_to_order(row)
            for row in rows
        ]

    def _row_to_order(
        self,
        row: sqlite3.Row,
    ) -> Order:
        customer = Customer(
            name=row["customer_name"],
            customer_id=row["customer_id"],
            phone=row["customer_phone"],
            email=row["customer_email"],
        )

        return Order(
            customer=customer,
            order_id=row["order_id"],
            status=row["status"],
            items=[],
        )

    def update(self, order: Order) -> bool:
        if order.order_id is None:
            raise RepositoryError(
                "Cannot update an order without an ID."
            )

        if order.customer.customer_id is None:
            raise RepositoryError(
                "Order customer must have a valid ID."
            )

        cursor = self._execute(
            """
            UPDATE orders
            SET customer_id = ?, status = ?
            WHERE order_id = ?
            """,
            (
                order.customer.customer_id,
                order.status,
                order.order_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, order_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM orders
            WHERE order_id = ?
            """,
            (order_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# ORDER ITEM REPOSITORY
# ============================================================

class OrderItemRepository(BaseRepository):
    """Repository for OrderItem objects."""

    def create(
        self,
        order_id: int,
        order_item: OrderItem,
    ) -> OrderItem:
        if order_item.menu_item.item_id is None:
            raise RepositoryError(
                "Menu item must have a valid ID."
            )

        cursor = self._execute(
            """
            INSERT INTO order_items
                (order_id, item_id, quantity)
            VALUES (?, ?, ?)
            """,
            (
                order_id,
                order_item.menu_item.item_id,
                order_item.quantity,
            ),
        )

        order_item.order_item_id = int(
            cursor.lastrowid
        )

        return order_item

    def get_by_id(
        self,
        order_item_id: int,
    ) -> Optional[OrderItem]:
        row = self._fetch_one(
            """
            SELECT
                oi.order_item_id,
                oi.order_id,
                oi.item_id,
                oi.quantity,
                mi.name,
                mi.price,
                mi.description,
                mi.is_available,
                mc.category_id,
                mc.name AS category_name,
                mc.description AS category_description
            FROM order_items oi
            INNER JOIN menu_items mi
                ON oi.item_id = mi.item_id
            INNER JOIN menu_categories mc
                ON mi.category_id = mc.category_id
            WHERE oi.order_item_id = ?
            """,
            (order_item_id,),
        )

        if row is None:
            return None

        return self._row_to_order_item(row)

    def get_by_order(
        self,
        order_id: int,
    ) -> list[OrderItem]:
        rows = self._fetch_all(
            """
            SELECT
                oi.order_item_id,
                oi.order_id,
                oi.item_id,
                oi.quantity,
                mi.name,
                mi.price,
                mi.description,
                mi.is_available,
                mc.category_id,
                mc.name AS category_name,
                mc.description AS category_description
            FROM order_items oi
            INNER JOIN menu_items mi
                ON oi.item_id = mi.item_id
            INNER JOIN menu_categories mc
                ON mi.category_id = mc.category_id
            WHERE oi.order_id = ?
            ORDER BY oi.order_item_id
            """,
            (order_id,),
        )

        return [
            self._row_to_order_item(row)
            for row in rows
        ]

    def _row_to_order_item(
        self,
        row: sqlite3.Row,
    ) -> OrderItem:
        category = MenuCategory(
            name=row["category_name"],
            category_id=row["category_id"],
            description=row["category_description"],
        )

        menu_item = MenuItem(
            name=row["name"],
            price=Decimal(str(row["price"])),
            category=category,
            item_id=row["item_id"],
            description=row["description"],
            is_available=bool(row["is_available"]),
        )

        return OrderItem(
            menu_item=menu_item,
            quantity=row["quantity"],
            order_item_id=row["order_item_id"],
        )

    def update(
        self,
        order_item_id: int,
        order_item: OrderItem,
        order_id: int,
    ) -> bool:
        if order_item.menu_item.item_id is None:
            raise RepositoryError(
                "Menu item must have a valid ID."
            )

        cursor = self._execute(
            """
            UPDATE order_items
            SET
                order_id = ?,
                item_id = ?,
                quantity = ?
            WHERE order_item_id = ?
            """,
            (
                order_id,
                order_item.menu_item.item_id,
                order_item.quantity,
                order_item_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, order_item_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM order_items
            WHERE order_item_id = ?
            """,
            (order_item_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# PAYMENT REPOSITORY
# ============================================================

class PaymentRepository(BaseRepository):
    """Repository for Payment objects."""

    def create(self, payment: Payment) -> Payment:
        cursor = self._execute(
            """
            INSERT INTO payments
                (
                    order_id,
                    amount,
                    payment_method,
                    status
                )
            VALUES (?, ?, ?, ?)
            """,
            (
                payment.order_id,
                str(payment.amount),
                payment.payment_method,
                payment.status,
            ),
        )

        payment.payment_id = int(cursor.lastrowid)

        return payment

    def get_by_id(
        self,
        payment_id: int,
    ) -> Optional[Payment]:
        row = self._fetch_one(
            """
            SELECT
                payment_id,
                order_id,
                amount,
                payment_method,
                status
            FROM payments
            WHERE payment_id = ?
            """,
            (payment_id,),
        )

        if row is None:
            return None

        return Payment(
            amount=Decimal(str(row["amount"])),
            payment_method=row["payment_method"],
            payment_id=row["payment_id"],
            order_id=row["order_id"],
            status=row["status"],
        )

    def get_by_order(
        self,
        order_id: int,
    ) -> list[Payment]:
        rows = self._fetch_all(
            """
            SELECT
                payment_id,
                order_id,
                amount,
                payment_method,
                status
            FROM payments
            WHERE order_id = ?
            ORDER BY payment_id
            """,
            (order_id,),
        )

        return [
            Payment(
                amount=Decimal(str(row["amount"])),
                payment_method=row["payment_method"],
                payment_id=row["payment_id"],
                order_id=row["order_id"],
                status=row["status"],
            )
            for row in rows
        ]

    def get_all(self) -> list[Payment]:
        rows = self._fetch_all(
            """
            SELECT
                payment_id,
                order_id,
                amount,
                payment_method,
                status
            FROM payments
            ORDER BY payment_id
            """
        )

        return [
            Payment(
                amount=Decimal(str(row["amount"])),
                payment_method=row["payment_method"],
                payment_id=row["payment_id"],
                order_id=row["order_id"],
                status=row["status"],
            )
            for row in rows
        ]

    def update(self, payment: Payment) -> bool:
        if payment.payment_id is None:
            raise RepositoryError(
                "Cannot update a payment without an ID."
            )

        cursor = self._execute(
            """
            UPDATE payments
            SET
                order_id = ?,
                amount = ?,
                payment_method = ?,
                status = ?
            WHERE payment_id = ?
            """,
            (
                payment.order_id,
                str(payment.amount),
                payment.payment_method,
                payment.status,
                payment.payment_id,
            ),
        )

        return cursor.rowcount > 0

    def delete(self, payment_id: int) -> bool:
        cursor = self._execute(
            """
            DELETE FROM payments
            WHERE payment_id = ?
            """,
            (payment_id,),
        )

        return cursor.rowcount > 0


# ============================================================
# TRANSACTION SUPPORT
# ============================================================

class OrderTransaction:
    """Handles atomic database transactions for orders."""

    def __init__(self, database):
        self.database = database

    def create_order_with_items(self, order, items):
        """
        Create an order and all of its items in one database transaction.

        If any part of the transaction fails, all changes are rolled back.
        """
        if not items:
            raise RepositoryError(
                "An order must contain at least one item."
            )

        if order.customer is None:
            raise RepositoryError(
                "An order must be associated with a customer."
            )

        connection = None

        try:
            connection = self.database.connect()

            cursor = connection.cursor()

            # Create the order.
            cursor.execute(
                """
                INSERT INTO orders (customer_id, status)
                VALUES (?, ?)
                """,
                (
                    order.customer.customer_id,
                    order.status,
                ),
            )

            order.order_id = cursor.lastrowid

            # Create each order item.
            for item in items:
                if item.menu_item is None:
                    raise RepositoryError(
                        "Order item must be associated with a menu item."
                    )

                cursor.execute(
                    """
                    SELECT item_id
                    FROM menu_items
                    WHERE item_id = ?
                    """,
                    (item.menu_item.item_id,),
                )

                menu_item_row = cursor.fetchone()

                if menu_item_row is None:
                    raise RepositoryError(
                        f"Menu item {item.menu_item.item_id} does not exist."
                    )

                cursor.execute(
                    """
                    INSERT INTO order_items (
                        order_id,
                        item_id,
                        quantity
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        order.order_id,
                        item.menu_item.item_id,
                        item.quantity,
                    ),
                )

                item.order_item_id = cursor.lastrowid

            connection.commit()

            return order

        except RepositoryError:
            if connection is not None:
                connection.rollback()
            raise

        except sqlite3.Error as exc:
            if connection is not None:
                connection.rollback()

            raise RepositoryError(
                f"Failed to create order transaction: {exc}"
            ) from exc

        finally:
            if connection is not None:
                connection.close()