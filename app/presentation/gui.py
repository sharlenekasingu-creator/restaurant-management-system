from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.business.authentication_service import (
    AuthenticationServiceImplementation,
    AuthenticationError,
)
from app.business.authorization_service import (
    AuthorizationService,
    AuthorizationError,
    Permission,
)
from app.business.menu_service import MenuService
from app.business.customer_service import CustomerService
from app.business.order_service import OrderService, OrderServiceError
from app.business.payment_service import PaymentService
from app.business.inventory_service import InventoryService
from app.business.reporting_service import (
    BasicReportingService,
    ReportingServiceError,
)
from app.data_access.repositories import (
    MenuCategoryRepository,
    MenuItemRepository,
    CustomerRepository,
    OrderRepository,
    PaymentRepository,
    InventoryRepository,
    SupplierRepository,
)
from app.models.menu import MenuCategory, MenuItem
from app.models.customer import Customer
from app.models.user import UserSession


class RestaurantManagementGUI:
    """
    Tkinter presentation layer for the Restaurant Management System.

    This class is responsible for:
        - GUI windows
        - user input
        - displaying results
        - navigation

    Business rules remain in the existing business services.
    Database operations remain in repositories.
    """

    SYSTEM_NAME = "Restaurant Management System"

    def __init__(
        self,
        root: tk.Tk,
        database,
        authentication_service: AuthenticationServiceImplementation,
        menu_service: MenuService,
        customer_service: CustomerService,
        order_service: OrderService,
        payment_service: PaymentService,
        inventory_service,
        reporting_service: BasicReportingService,
    ) -> None:

        self.root = root
        self.database = database

        self.authentication_service = authentication_service
        self.menu_service = menu_service
        self.customer_service = customer_service
        self.order_service = order_service
        self.payment_service = payment_service
        self.inventory_service = inventory_service
        self.reporting_service = reporting_service

        self.session: Optional[UserSession] = None

        self.root.title(self.SYSTEM_NAME)
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)

        self.style = ttk.Style()

        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self._configure_styles()

        self.login_frame = None
        self.dashboard_frame = None
        self.content_frame = None

        self.show_login()

    # ============================================================
    # STYLING
    # ============================================================

    def _configure_styles(self) -> None:
        self.style.configure(
            "Title.TLabel",
            font=("Segoe UI", 24, "bold"),
        )

        self.style.configure(
            "Subtitle.TLabel",
            font=("Segoe UI", 12),
        )

        self.style.configure(
            "Heading.TLabel",
            font=("Segoe UI", 18, "bold"),
        )

        self.style.configure(
            "Menu.TButton",
            font=("Segoe UI", 11),
            padding=10,
        )

        self.style.configure(
            "Action.TButton",
            font=("Segoe UI", 10),
            padding=7,
        )

    # ============================================================
    # GENERAL HELPERS
    # ============================================================

    def clear_root(self) -> None:
        for widget in self.root.winfo_children():
            widget.destroy()

    def clear_content(self) -> None:
        if self.content_frame is not None:
            for widget in self.content_frame.winfo_children():
                widget.destroy()

    def show_error(self, message: str) -> None:
        messagebox.showerror(
            self.SYSTEM_NAME,
            str(message),
            parent=self.root,
        )

    def show_info(self, message: str) -> None:
        messagebox.showinfo(
            self.SYSTEM_NAME,
            str(message),
            parent=self.root,
        )

    def confirm(self, message: str) -> bool:
        return messagebox.askyesno(
            self.SYSTEM_NAME,
            message,
            parent=self.root,
        )

    def has_permission(self, permission: Permission) -> bool:
        if self.session is None:
            return False

        try:
            AuthorizationService.require_permission_for_session(
                self.session,
                permission,
            )
            return True
        except AuthorizationError:
            return False

    def require_permission(
        self,
        permission: Permission,
    ) -> bool:

        if not self.has_permission(permission):
            self.show_error(
                "You are not authorized to perform this operation."
            )
            return False

        return True

    # ============================================================
    # LOGIN
    # ============================================================

    def show_login(self) -> None:
        self.clear_root()

        self.root.geometry("520x500")

        outer = ttk.Frame(self.root, padding=30)
        outer.pack(expand=True)

        title = ttk.Label(
            outer,
            text=self.SYSTEM_NAME,
            style="Title.TLabel",
        )
        title.pack(pady=(20, 5))

        subtitle = ttk.Label(
            outer,
            text="Secure Login",
            style="Subtitle.TLabel",
        )
        subtitle.pack(pady=(0, 30))

        form = ttk.Frame(outer)
        form.pack(fill="x")

        ttk.Label(
            form,
            text="Username:",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=8,
        )

        self.username_entry = ttk.Entry(
            form,
            width=35,
        )
        self.username_entry.grid(
            row=0,
            column=1,
            pady=8,
            padx=(10, 0),
        )

        ttk.Label(
            form,
            text="Password:",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=8,
        )

        self.password_entry = ttk.Entry(
            form,
            width=35,
            show="*",
        )
        self.password_entry.grid(
            row=1,
            column=1,
            pady=8,
            padx=(10, 0),
        )

        self.login_status = ttk.Label(
            outer,
            text="",
        )
        self.login_status.pack(pady=15)

        login_button = ttk.Button(
            outer,
            text="Login",
            command=self.login,
            width=25,
        )
        login_button.pack(pady=10)

        exit_button = ttk.Button(
            outer,
            text="Exit",
            command=self.root.destroy,
            width=25,
        )
        exit_button.pack(pady=5)

        self.username_entry.focus_set()

        self.root.bind(
            "<Return>",
            lambda event: self.login(),
        )

    def login(self) -> None:
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username:
            self.login_status.config(
                text="Username is required."
            )
            return

        if not password:
            self.login_status.config(
                text="Password is required."
            )
            return

        try:
            self.session = (
                self.authentication_service.authenticate(
                    username,
                    password,
                )
            )

            self.root.unbind("<Return>")

            self.show_dashboard()

        except AuthenticationError as exc:
            self.login_status.config(
                text=str(exc)
            )
            self.password_entry.delete(
                0,
                tk.END,
            )
            self.password_entry.focus_set()

    # ============================================================
    # DASHBOARD
    # ============================================================

    def show_dashboard(self) -> None:
        self.clear_root()

        self.root.geometry("1200x750")

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True)

        # Header
        header = ttk.Frame(
            main,
            padding=(20, 15),
        )
        header.pack(
            fill="x",
        )

        user = self.session.user

        ttk.Label(
            header,
            text=self.SYSTEM_NAME,
            style="Title.TLabel",
        ).pack(side="left")

        user_text = (
            f"{user.full_name or user.username}  |  "
            f"{user.role.name}"
        )

        ttk.Label(
            header,
            text=user_text,
            style="Subtitle.TLabel",
        ).pack(side="right")

        separator = ttk.Separator(
            main,
            orient="horizontal",
        )
        separator.pack(fill="x")

        body = ttk.Frame(main)
        body.pack(
            fill="both",
            expand=True,
        )

        # Sidebar
        self.dashboard_frame = ttk.Frame(
            body,
            padding=15,
        )
        self.dashboard_frame.pack(
            side="left",
            fill="y",
        )

        # Content
        self.content_frame = ttk.Frame(
            body,
            padding=25,
        )
        self.content_frame.pack(
            side="right",
            fill="both",
            expand=True,
        )

        self._build_navigation()

        # Default page
        self.show_home()

    def _build_navigation(self) -> None:

        ttk.Label(
            self.dashboard_frame,
            text="MAIN MENU",
            font=("Segoe UI", 10, "bold"),
        ).pack(
            pady=(0, 10),
        )

        if self.has_permission(Permission.VIEW_MENU):
            self._nav_button(
                "Menu Management",
                self.show_menu,
            )

        if self.has_permission(Permission.VIEW_CUSTOMERS):
            self._nav_button(
                "Customers",
                self.show_customers,
            )

        if self.has_permission(Permission.MANAGE_ORDERS):
            self._nav_button(
                "Customer Orders",
                self.show_orders,
            )

        if self.has_permission(Permission.PROCESS_PAYMENTS):
            self._nav_button(
                "Payment Processing",
                self.show_payments,
            )

        if self.has_permission(Permission.VIEW_INVENTORY):
            self._nav_button(
                "Inventory",
                self.show_inventory,
            )

            if self.has_permission(
                Permission.MANAGE_INVENTORY
            ):
                self._nav_button(
                    "Suppliers",
                    self.show_suppliers,
                )

        if self.has_permission(Permission.VIEW_REPORTS):
            self._nav_button(
                "Reports",
                self.show_reports,
            )

        ttk.Separator(
            self.dashboard_frame,
            orient="horizontal",
        ).pack(
            fill="x",
            pady=15,
        )

        self._nav_button(
            "Logout",
            self.logout,
        )

        self._nav_button(
            "Exit",
            self.root.destroy,
        )

    def _nav_button(
        self,
        text: str,
        command,
    ) -> None:

        ttk.Button(
            self.dashboard_frame,
            text=text,
            command=command,
            style="Menu.TButton",
            width=22,
        ).pack(
            fill="x",
            pady=4,
        )

    # ============================================================
    # HOME
    # ============================================================

    def show_home(self) -> None:
        self.clear_content()

        user = self.session.user

        ttk.Label(
            self.content_frame,
            text="Dashboard",
            style="Heading.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

        ttk.Label(
            self.content_frame,
            text=(
                f"Welcome, "
                f"{user.full_name or user.username}."
            ),
            font=("Segoe UI", 16),
        ).pack(
            anchor="w",
            pady=5,
        )

        ttk.Label(
            self.content_frame,
            text=f"Role: {user.role.name}",
            font=("Segoe UI", 12),
        ).pack(
            anchor="w",
            pady=5,
        )

        ttk.Label(
            self.content_frame,
            text=(
                "Select a function from the navigation "
                "menu."
            ),
            font=("Segoe UI", 11),
        ).pack(
            anchor="w",
            pady=20,
        )

    # ============================================================
    # MENU
    # ============================================================

    def show_menu(self) -> None:
        self.clear_content()

        ttk.Label(
            self.content_frame,
            text="Menu Management",
            style="Heading.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 10),
        )

        toolbar = ttk.Frame(
            self.content_frame,
        )
        toolbar.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Button(
            toolbar,
            text="Refresh Menu",
            command=self.load_menu,
            style="Action.TButton",
        ).pack(
            side="left",
            padx=3,
        )

        if self.has_permission(Permission.MANAGE_MENU):
            ttk.Button(
                toolbar,
                text="Create Category",
                command=self.create_category_dialog,
                style="Action.TButton",
            ).pack(
                side="left",
                padx=3,
            )

            ttk.Button(
                toolbar,
                text="Create Menu Item",
                command=self.create_menu_item_dialog,
                style="Action.TButton",
            ).pack(
                side="left",
                padx=3,
            )

        columns = (
            "id",
            "name",
            "category",
            "price",
            "availability",
        )

        self.menu_tree = ttk.Treeview(
            self.content_frame,
            columns=columns,
            show="headings",
        )

        headings = {
            "id": "ID",
            "name": "Item",
            "category": "Category",
            "price": "Price",
            "availability": "Available",
        }

        for column in columns:
            self.menu_tree.heading(
                column,
                text=headings[column],
            )

        self.menu_tree.column(
            "id",
            width=60,
        )

        self.menu_tree.column(
            "name",
            width=220,
        )

        self.menu_tree.column(
            "category",
            width=180,
        )

        self.menu_tree.column(
            "price",
            width=100,
        )

        self.menu_tree.column(
            "availability",
            width=100,
        )

        self.menu_tree.pack(
            fill="both",
            expand=True,
        )

        if self.has_permission(Permission.MANAGE_MENU):
            actions = ttk.Frame(
                self.content_frame,
            )
            actions.pack(
                fill="x",
                pady=10,
            )

            ttk.Button(
                actions,
                text="Update Selected",
                command=self.update_menu_item_dialog,
            ).pack(
                side="left",
                padx=3,
            )

            ttk.Button(
                actions,
                text="Delete Selected",
                command=self.delete_menu_item,
            ).pack(
                side="left",
                padx=3,
            )

            ttk.Button(
                actions,
                text="Toggle Availability",
                command=self.toggle_menu_item,
            ).pack(
                side="left",
                padx=3,
            )

        self.load_menu()

    def load_menu(self) -> None:
        if not hasattr(self, "menu_tree"):
            return

        try:
            items = self.menu_service.get_all_items(
                self.session
            )

            for row in self.menu_tree.get_children():
                self.menu_tree.delete(row)

            for item in items:
                self.menu_tree.insert(
                    "",
                    "end",
                    values=(
                        item.item_id,
                        item.name,
                        item.category.name,
                        f"K{item.price:.2f}",
                        (
                            "Yes"
                            if item.is_available
                            else "No"
                        ),
                    ),
                )

        except Exception as exc:
            self.show_error(exc)

    def create_category_dialog(self) -> None:
        if not self.require_permission(
            Permission.MANAGE_MENU
        ):
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Create Category")
        dialog.geometry("420x250")
        dialog.transient(self.root)
        dialog.grab_set()

        name_var = tk.StringVar()
        desc_var = tk.StringVar()

        ttk.Label(
            dialog,
            text="Category Name:",
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5),
        )

        ttk.Entry(
            dialog,
            textvariable=name_var,
            width=40,
        ).pack(
            padx=20,
        )

        ttk.Label(
            dialog,
            text="Description:",
        ).pack(
            anchor="w",
            padx=20,
            pady=(10, 5),
        )

        ttk.Entry(
            dialog,
            textvariable=desc_var,
            width=40,
        ).pack(
            padx=20,
        )

        def save() -> None:
            try:
                self.menu_service.create_category(
                    self.session,
                    name_var.get(),
                    desc_var.get(),
                )

                dialog.destroy()
                self.show_info(
                    "Category created successfully."
                )
                self.load_menu()

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Save",
            command=save,
        ).pack(
            pady=20,
        )

    def create_menu_item_dialog(self) -> None:
        if not self.require_permission(
            Permission.MANAGE_MENU
        ):
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Create Menu Item")
        dialog.geometry("450x420")
        dialog.transient(self.root)
        dialog.grab_set()

        categories = self.menu_service.get_all_categories(
            self.session
        )

        category_map = {
            f"{c.category_id} - {c.name}": c
            for c in categories
        }

        name_var = tk.StringVar()
        price_var = tk.StringVar()
        category_var = tk.StringVar()
        description_var = tk.StringVar()

        self._entry_row(
            dialog,
            "Item Name:",
            name_var,
        )

        self._entry_row(
            dialog,
            "Price:",
            price_var,
        )

        ttk.Label(
            dialog,
            text="Category:",
        ).pack(
            anchor="w",
            padx=20,
            pady=(10, 5),
        )

        category_box = ttk.Combobox(
            dialog,
            textvariable=category_var,
            values=list(category_map.keys()),
            state="readonly",
            width=38,
        )
        category_box.pack(
            padx=20,
        )

        ttk.Label(
            dialog,
            text="Description:",
        ).pack(
            anchor="w",
            padx=20,
            pady=(10, 5),
        )

        ttk.Entry(
            dialog,
            textvariable=description_var,
            width=40,
        ).pack(
            padx=20,
        )

        def save() -> None:
            try:
                category = category_map.get(
                    category_var.get()
                )

                if category is None:
                    raise ValueError(
                        "Please select a category."
                    )

                price = Decimal(
                    price_var.get().strip()
                )

                self.menu_service.create_item(
                    self.session,
                    name_var.get(),
                    price,
                    category.category_id,
                    description_var.get(),
                    True,
                )

                dialog.destroy()

                self.show_info(
                    "Menu item created successfully."
                )

                self.load_menu()

            except (
                InvalidOperation,
                ValueError,
            ) as exc:
                self.show_error(exc)

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Save",
            command=save,
        ).pack(
            pady=20,
        )

    def update_menu_item_dialog(self) -> None:
        if not self.require_permission(
            Permission.MANAGE_MENU
        ):
            return

        selected = self.menu_tree.selection()

        if not selected:
            self.show_error(
                "Select a menu item first."
            )
            return

        item_id = int(
            self.menu_tree.item(
                selected[0]
            )["values"][0]
        )

        try:
            item = self.menu_service.get_item(
                self.session,
                item_id,
            )

            if item is None:
                raise ValueError(
                    "Menu item was not found."
                )

            dialog = tk.Toplevel(self.root)
            dialog.title("Update Menu Item")
            dialog.geometry("450x420")
            dialog.transient(self.root)
            dialog.grab_set()

            name_var = tk.StringVar(
                value=item.name
            )

            price_var = tk.StringVar(
                value=str(item.price)
            )

            description_var = tk.StringVar(
                value=item.description
            )

            categories = (
                self.menu_service.get_all_categories(
                    self.session
                )
            )

            category_map = {
                f"{c.category_id} - {c.name}": c
                for c in categories
            }

            current_category = next(
                (
                    key
                    for key, value
                    in category_map.items()
                    if value.category_id
                    == item.category.category_id
                ),
                "",
            )

            category_var = tk.StringVar(
                value=current_category
            )

            self._entry_row(
                dialog,
                "Item Name:",
                name_var,
            )

            self._entry_row(
                dialog,
                "Price:",
                price_var,
            )

            ttk.Label(
                dialog,
                text="Category:",
            ).pack(
                anchor="w",
                padx=20,
                pady=(10, 5),
            )

            ttk.Combobox(
                dialog,
                textvariable=category_var,
                values=list(category_map.keys()),
                state="readonly",
                width=38,
            ).pack(
                padx=20,
            )

            ttk.Label(
                dialog,
                text="Description:",
            ).pack(
                anchor="w",
                padx=20,
                pady=(10, 5),
            )

            ttk.Entry(
                dialog,
                textvariable=description_var,
                width=40,
            ).pack(
                padx=20,
            )

            def save() -> None:
                try:
                    category = category_map.get(
                        category_var.get()
                    )

                    if category is None:
                        raise ValueError(
                            "Please select a category."
                        )

                    updated = (
                        self.menu_service.update_item(
                            self.session,
                            item_id,
                            name_var.get(),
                            Decimal(
                                price_var.get()
                            ),
                            category.category_id,
                            description_var.get(),
                            item.is_available,
                        )
                    )

                    if updated is None:
                        raise ValueError(
                            "Menu item was not updated."
                        )

                    dialog.destroy()
                    self.show_info(
                        "Menu item updated successfully."
                    )
                    self.load_menu()

                except Exception as exc:
                    self.show_error(exc)

            ttk.Button(
                dialog,
                text="Save Changes",
                command=save,
            ).pack(
                pady=20,
            )

        except Exception as exc:
            self.show_error(exc)

    def delete_menu_item(self) -> None:
        if not self.require_permission(
            Permission.MANAGE_MENU
        ):
            return

        selected = self.menu_tree.selection()

        if not selected:
            self.show_error(
                "Select a menu item first."
            )
            return

        item_id = int(
            self.menu_tree.item(
                selected[0]
            )["values"][0]
        )

        if not self.confirm(
            "Delete the selected menu item?"
        ):
            return

        try:
            self.menu_service.delete_item(
                self.session,
                item_id,
            )

            self.show_info(
                "Menu item deleted successfully."
            )

            self.load_menu()

        except Exception as exc:
            self.show_error(exc)

    def toggle_menu_item(self) -> None:
        if not self.require_permission(
            Permission.MANAGE_MENU
        ):
            return

        selected = self.menu_tree.selection()

        if not selected:
            self.show_error(
                "Select a menu item first."
            )
            return

        item_id = int(
            self.menu_tree.item(
                selected[0]
            )["values"][0]
        )

        try:
            item = self.menu_service.get_item(
                self.session,
                item_id,
            )

            if item.is_available:
                self.menu_service.make_unavailable(
                    self.session,
                    item_id,
                )
            else:
                self.menu_service.make_available(
                    self.session,
                    item_id,
                )

            self.load_menu()

        except Exception as exc:
            self.show_error(exc)

    # ============================================================
    # CUSTOMERS
    # ============================================================

    def show_customers(self) -> None:
        self.clear_content()

        ttk.Label(
            self.content_frame,
            text="Customer Management",
            style="Heading.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 10),
        )

        toolbar = ttk.Frame(
            self.content_frame,
        )
        toolbar.pack(
            fill="x",
            pady=10,
        )

        ttk.Button(
            toolbar,
            text="Refresh",
            command=self.load_customers,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            toolbar,
            text="Search",
            command=self.search_customers_dialog,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            toolbar,
            text="Create Customer",
            command=self.create_customer_dialog,
        ).pack(
            side="left",
            padx=3,
        )

        columns = (
            "id",
            "name",
            "phone",
            "email",
        )

        self.customer_tree = ttk.Treeview(
            self.content_frame,
            columns=columns,
            show="headings",
        )

        for column, heading in {
            "id": "ID",
            "name": "Name",
            "phone": "Phone",
            "email": "Email",
        }.items():
            self.customer_tree.heading(
                column,
                text=heading,
            )

        self.customer_tree.column(
            "id",
            width=60,
        )

        self.customer_tree.column(
            "name",
            width=220,
        )

        self.customer_tree.column(
            "phone",
            width=150,
        )

        self.customer_tree.column(
            "email",
            width=280,
        )

        self.customer_tree.pack(
            fill="both",
            expand=True,
        )

        actions = ttk.Frame(
            self.content_frame,
        )
        actions.pack(
            fill="x",
            pady=10,
        )

        ttk.Button(
            actions,
            text="Update Selected",
            command=self.update_customer_dialog,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            actions,
            text="Delete Selected",
            command=self.delete_customer,
        ).pack(
            side="left",
            padx=3,
        )

        self.load_customers()

    def load_customers(self) -> None:
        try:
            customers = (
                self.customer_service.get_all_customers(
                    self.session
                )
            )

            for row in self.customer_tree.get_children():
                self.customer_tree.delete(row)

            for customer in customers:
                self.customer_tree.insert(
                    "",
                    "end",
                    values=(
                        customer.customer_id,
                        customer.name,
                        customer.phone,
                        customer.email,
                    ),
                )

        except Exception as exc:
            self.show_error(exc)

    def create_customer_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Customer")
        dialog.geometry("420x300")
        dialog.transient(self.root)
        dialog.grab_set()

        name_var = tk.StringVar()
        phone_var = tk.StringVar()
        email_var = tk.StringVar()

        self._entry_row(
            dialog,
            "Name:",
            name_var,
        )

        self._entry_row(
            dialog,
            "Phone:",
            phone_var,
        )

        self._entry_row(
            dialog,
            "Email:",
            email_var,
        )

        def save() -> None:
            try:
                self.customer_service.create_customer(
                    self.session,
                    name_var.get(),
                    phone_var.get(),
                    email_var.get(),
                )

                dialog.destroy()

                self.show_info(
                    "Customer created successfully."
                )

                self.load_customers()

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Save",
            command=save,
        ).pack(
            pady=20,
        )

    def update_customer_dialog(self) -> None:
        selected = self.customer_tree.selection()

        if not selected:
            self.show_error(
                "Select a customer first."
            )
            return

        values = self.customer_tree.item(
            selected[0]
        )["values"]

        customer_id = int(values[0])

        dialog = tk.Toplevel(self.root)
        dialog.title("Update Customer")
        dialog.geometry("420x300")
        dialog.transient(self.root)
        dialog.grab_set()

        name_var = tk.StringVar(
            value=values[1]
        )

        phone_var = tk.StringVar(
            value=values[2]
        )

        email_var = tk.StringVar(
            value=values[3]
        )

        self._entry_row(
            dialog,
            "Name:",
            name_var,
        )

        self._entry_row(
            dialog,
            "Phone:",
            phone_var,
        )

        self._entry_row(
            dialog,
            "Email:",
            email_var,
        )

        def save() -> None:
            try:
                self.customer_service.update_customer(
                    self.session,
                    customer_id,
                    name_var.get(),
                    phone_var.get(),
                    email_var.get(),
                )

                dialog.destroy()

                self.show_info(
                    "Customer updated successfully."
                )

                self.load_customers()

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Save Changes",
            command=save,
        ).pack(
            pady=20,
        )

    def delete_customer(self) -> None:
        selected = self.customer_tree.selection()

        if not selected:
            self.show_error(
                "Select a customer first."
            )
            return

        customer_id = int(
            self.customer_tree.item(
                selected[0]
            )["values"][0]
        )

        if not self.confirm(
            "Delete the selected customer?"
        ):
            return

        try:
            self.customer_service.delete_customer(
                self.session,
                customer_id,
            )

            self.show_info(
                "Customer deleted successfully."
            )

            self.load_customers()

        except Exception as exc:
            self.show_error(exc)

    def search_customers_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Search Customers")
        dialog.geometry("400x180")
        dialog.transient(self.root)
        dialog.grab_set()

        search_var = tk.StringVar()

        ttk.Label(
            dialog,
            text="Search term:",
        ).pack(
            pady=(20, 5),
        )

        entry = ttk.Entry(
            dialog,
            textvariable=search_var,
            width=35,
        )
        entry.pack()

        def search() -> None:
            try:
                customers = (
                    self.customer_service.search_customers(
                        self.session,
                        search_var.get(),
                    )
                )

                dialog.destroy()

                for row in self.customer_tree.get_children():
                    self.customer_tree.delete(row)

                for customer in customers:
                    self.customer_tree.insert(
                        "",
                        "end",
                        values=(
                            customer.customer_id,
                            customer.name,
                            customer.phone,
                            customer.email,
                        ),
                    )

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Search",
            command=search,
        ).pack(
            pady=20,
        )

        entry.focus_set()

    # ============================================================
    # ORDERS
    # ============================================================

    def show_orders(self) -> None:
        self.clear_content()

        ttk.Label(
            self.content_frame,
            text="Customer Order Management",
            style="Heading.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

        ttk.Label(
            self.content_frame,
            text=(
                "Use the existing order workflow to create "
                "orders, add menu items and calculate totals."
            ),
            wraplength=700,
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

        ttk.Button(
            self.content_frame,
            text="Create Customer Order",
            command=self.create_order_dialog,
            style="Action.TButton",
        ).pack(
            anchor="w",
            pady=5,
        )

        ttk.Button(
            self.content_frame,
            text="View Order",
            command=self.view_order_dialog,
            style="Action.TButton",
        ).pack(
            anchor="w",
            pady=5,
        )

    def create_order_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Customer Order")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()

        customers = (
            self.order_service.get_all_customers(
                self.session
            )
        )

        customer_map = {
            f"{c.customer_id} - {c.name}": c
            for c in customers
        }

        customer_var = tk.StringVar()

        ttk.Label(
            dialog,
            text="Customer:",
        ).pack(
            anchor="w",
            padx=20,
            pady=(20, 5),
        )

        customer_box = ttk.Combobox(
            dialog,
            textvariable=customer_var,
            values=list(customer_map.keys()),
            state="readonly",
            width=55,
        )
        customer_box.pack(
            padx=20,
        )

        ttk.Label(
            dialog,
            text="Menu Item:",
        ).pack(
            anchor="w",
            padx=20,
            pady=(15, 5),
        )

        menu_items = (
            self.order_service.get_available_menu_items(
                self.session
            )
        )

        menu_map = {
            f"{i.item_id} - {i.name} - K{i.price:.2f}": i
            for i in menu_items
        }

        item_var = tk.StringVar()

        item_box = ttk.Combobox(
            dialog,
            textvariable=item_var,
            values=list(menu_map.keys()),
            state="readonly",
            width=55,
        )
        item_box.pack(
            padx=20,
        )

        ttk.Label(
            dialog,
            text="Quantity:",
        ).pack(
            anchor="w",
            padx=20,
            pady=(15, 5),
        )

        quantity_var = tk.StringVar(
            value="1"
        )

        ttk.Entry(
            dialog,
            textvariable=quantity_var,
            width=10,
        ).pack(
            padx=20,
            anchor="w",
        )

        order_items = []

        tree = ttk.Treeview(
            dialog,
            columns=(
                "item",
                "quantity",
                "price",
                "subtotal",
            ),
            show="headings",
            height=8,
        )

        for column, heading in {
            "item": "Item",
            "quantity": "Qty",
            "price": "Unit Price",
            "subtotal": "Subtotal",
        }.items():
            tree.heading(
                column,
                text=heading,
            )

        tree.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=15,
        )

        def add_item() -> None:
            try:
                item = menu_map.get(
                    item_var.get()
                )

                if item is None:
                    raise ValueError(
                        "Select a menu item."
                    )

                quantity = int(
                    quantity_var.get()
                )

                if quantity <= 0:
                    raise ValueError(
                        "Quantity must be greater than zero."
                    )

                order_items.append(
                    (
                        item,
                        quantity,
                    )
                )

                subtotal = item.price * quantity

                tree.insert(
                    "",
                    "end",
                    values=(
                        item.name,
                        quantity,
                        f"K{item.price:.2f}",
                        f"K{subtotal:.2f}",
                    ),
                )

            except Exception as exc:
                self.show_error(exc)

        def save_order() -> None:
            try:
                customer = customer_map.get(
                    customer_var.get()
                )

                if customer is None:
                    raise ValueError(
                        "Select a customer."
                    )

                if not order_items:
                    raise ValueError(
                        "Add at least one menu item."
                    )

                order = self.order_service.create_order(
                    self.session,
                    customer.customer_id,
                )

                for item, quantity in order_items:
                    self.order_service.add_item(
                        self.session,
                        order,
                        item.item_id,
                        quantity,
                    )

                order = self.order_service.save_order(
                    self.session,
                    order,
                )

                dialog.destroy()

                self.show_info(
                    f"Order {order.order_id} "
                    "created successfully."
                )

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Add Item",
            command=add_item,
        ).pack(
            side="left",
            padx=20,
            pady=10,
        )

        ttk.Button(
            dialog,
            text="Save Order",
            command=save_order,
        ).pack(
            side="right",
            padx=20,
            pady=10,
        )

    def view_order_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("View Order")
        dialog.geometry("750x550")
        dialog.transient(self.root)
        dialog.grab_set()

        order_id_var = tk.StringVar()

        ttk.Label(
            dialog,
            text="Order ID:",
        ).pack(
            pady=(20, 5),
        )

        ttk.Entry(
            dialog,
            textvariable=order_id_var,
            width=15,
        ).pack()

        text = tk.Text(
            dialog,
            wrap="word",
            height=20,
        )
        text.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )

        def load_order() -> None:
            try:
                order_id = int(
                    order_id_var.get()
                )

                order = self.order_service.get_order(
                    self.session,
                    order_id,
                )

                text.delete(
                    "1.0",
                    tk.END,
                )

                text.insert(
                    tk.END,
                    f"Order ID: {order.order_id}\n"
                )

                text.insert(
                    tk.END,
                    f"Customer: {order.customer.name}\n"
                )

                text.insert(
                    tk.END,
                    f"Status: {order.status}\n\n"
                )

                for item in order.items:
                    text.insert(
                        tk.END,
                        (
                            f"{item.menu_item.name} | "
                            f"Qty: {item.quantity} | "
                            f"Price: K{item.menu_item.price:.2f} | "
                            f"Subtotal: "
                            f"K{item.subtotal:.2f}\n"
                        ),
                    )

                text.insert(
                    tk.END,
                    f"\nTOTAL: K{order.calculate_total():.2f}",
                )

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Load Order",
            command=load_order,
        ).pack()

    # ============================================================
    # PAYMENTS
    # ============================================================

    def show_payments(self) -> None:
        self.clear_content()

        ttk.Label(
            self.content_frame,
            text="Payment Processing",
            style="Heading.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 20),
        )

        ttk.Button(
            self.content_frame,
            text="Process Payment",
            command=self.payment_dialog,
            style="Action.TButton",
        ).pack(
            anchor="w",
        )

    def payment_dialog(self) -> None:
        if not self.require_permission(
            Permission.PROCESS_PAYMENTS
        ):
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Process Payment")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()

        order_var = tk.StringVar()
        amount_var = tk.StringVar()
        method_var = tk.StringVar(
            value="Cash"
        )

        self._entry_row(
            dialog,
            "Order ID:",
            order_var,
        )

        self._entry_row(
            dialog,
            "Amount:",
            amount_var,
        )

        ttk.Label(
            dialog,
            text="Payment Method:",
        ).pack(
            anchor="w",
            padx=20,
            pady=(10, 5),
        )

        ttk.Combobox(
            dialog,
            textvariable=method_var,
            values=(
                "Cash",
                "Card",
                "Bank Transfer",
            ),
            state="readonly",
            width=35,
        ).pack(
            padx=20,
        )

        def process() -> None:
            try:
                order_id = int(
                    order_var.get()
                )

                amount = Decimal(
                    amount_var.get()
                )

                if amount <= 0:
                    raise ValueError(
                        "Payment amount must be greater than zero."
                    )

                payment = (
                    self.payment_service.create_payment(
                        self.session,
                        amount,
                        method_var.get(),
                        order_id,
                    )
                )

                self.payment_service.complete_payment(
                    self.session,
                    payment,
                )

                self.show_info(
                    "Payment completed successfully."
                )

                dialog.destroy()

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Process Payment",
            command=process,
        ).pack(
            pady=25,
        )

    # ============================================================
    # INVENTORY
    # ============================================================

    def show_inventory(self) -> None:
        self.clear_content()

        ttk.Label(
            self.content_frame,
            text="Inventory Management",
            style="Heading.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 10),
        )

        toolbar = ttk.Frame(
            self.content_frame,
        )
        toolbar.pack(
            fill="x",
            pady=10,
        )

        ttk.Button(
            toolbar,
            text="Refresh",
            command=self.load_inventory,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            toolbar,
            text="Low Stock",
            command=self.load_low_stock,
        ).pack(
            side="left",
            padx=3,
        )

        if self.has_permission(
            Permission.MANAGE_INVENTORY
        ):
            ttk.Button(
                toolbar,
                text="Add Inventory",
                command=self.add_inventory_dialog,
            ).pack(
                side="left",
                padx=3,
            )

            ttk.Button(
                toolbar,
                text="Add Stock",
                command=self.add_stock_dialog,
            ).pack(
                side="left",
                padx=3,
            )

            ttk.Button(
                toolbar,
                text="Remove Stock",
                command=self.remove_stock_dialog,
            ).pack(
                side="left",
                padx=3,
            )

        columns = (
            "id",
            "name",
            "quantity",
            "unit",
            "supplier",
        )

        self.inventory_tree = ttk.Treeview(
            self.content_frame,
            columns=columns,
            show="headings",
        )

        for column, heading in {
            "id": "ID",
            "name": "Item",
            "quantity": "Quantity",
            "unit": "Unit",
            "supplier": "Supplier",
        }.items():
            self.inventory_tree.heading(
                column,
                text=heading,
            )

        self.inventory_tree.pack(
            fill="both",
            expand=True,
        )

        self.load_inventory()

    def load_inventory(self) -> None:
        try:
            items = (
                self.inventory_service.get_all_inventory(
                    self.session
                )
            )

            self._populate_inventory(items)

        except Exception as exc:
            self.show_error(exc)

    def load_low_stock(self) -> None:
        try:
            items = (
                self.inventory_service.get_low_stock_items(
                    self.session
                )
            )

            self._populate_inventory(items)

        except Exception as exc:
            self.show_error(exc)

    def _populate_inventory(
        self,
        items,
    ) -> None:

        for row in self.inventory_tree.get_children():
            self.inventory_tree.delete(row)

        for item in items:
            supplier_name = ""

            if item.supplier is not None:
                supplier_name = item.supplier.name

            self.inventory_tree.insert(
                "",
                "end",
                values=(
                    item.inventory_id,
                    item.name,
                    item.quantity,
                    item.unit,
                    supplier_name,
                ),
            )

    def add_inventory_dialog(self) -> None:
        if not self.require_permission(
            Permission.MANAGE_INVENTORY
        ):
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Add Inventory")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()

        name_var = tk.StringVar()
        quantity_var = tk.StringVar()
        unit_var = tk.StringVar()
        supplier_var = tk.StringVar()

        self._entry_row(
            dialog,
            "Item Name:",
            name_var,
        )

        self._entry_row(
            dialog,
            "Quantity:",
            quantity_var,
        )

        self._entry_row(
            dialog,
            "Unit:",
            unit_var,
        )

        suppliers = (
            self.inventory_service.get_all_suppliers(
                self.session
            )
        )

        supplier_map = {
            f"{s.supplier_id} - {s.name}": s
            for s in suppliers
        }

        ttk.Label(
            dialog,
            text="Supplier:",
        ).pack(
            anchor="w",
            padx=20,
            pady=(10, 5),
        )

        supplier_box = ttk.Combobox(
            dialog,
            textvariable=supplier_var,
            values=list(supplier_map.keys()),
            state="readonly",
            width=38,
        )
        supplier_box.pack(
            padx=20,
        )

        def save() -> None:
            try:
                supplier = supplier_map.get(
                    supplier_var.get()
                )

                supplier_id = (
                    supplier.supplier_id
                    if supplier
                    else None
                )

                self.inventory_service.create_inventory_item(
                    self.session,
                    name_var.get(),
                    float(quantity_var.get()),
                    unit_var.get(),
                    supplier_id,
                )

                dialog.destroy()

                self.show_info(
                    "Inventory item added successfully."
                )

                self.load_inventory()

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Save",
            command=save,
        ).pack(
            pady=20,
        )

    def add_stock_dialog(self) -> None:
        self._stock_dialog(
            add=True
        )

    def remove_stock_dialog(self) -> None:
        self._stock_dialog(
            add=False
        )

    def _stock_dialog(
        self,
        add: bool,
    ) -> None:

        if not self.require_permission(
            Permission.MANAGE_INVENTORY
        ):
            return

        selected = self.inventory_tree.selection()

        if not selected:
            self.show_error(
                "Select an inventory item first."
            )
            return

        values = self.inventory_tree.item(
            selected[0]
        )["values"]

        inventory_id = int(values[0])

        dialog = tk.Toplevel(self.root)
        dialog.title(
            "Add Stock" if add else "Remove Stock"
        )
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()

        quantity_var = tk.StringVar()

        ttk.Label(
            dialog,
            text="Quantity:",
        ).pack(
            pady=(25, 5),
        )

        ttk.Entry(
            dialog,
            textvariable=quantity_var,
            width=20,
        ).pack()

        def save() -> None:
            try:
                quantity = float(
                    quantity_var.get()
                )

                if add:
                    self.inventory_service.add_stock(
                        self.session,
                        inventory_id,
                        quantity,
                    )
                else:
                    self.inventory_service.remove_stock(
                        self.session,
                        inventory_id,
                        quantity,
                    )

                dialog.destroy()

                self.show_info(
                    "Inventory updated successfully."
                )

                self.load_inventory()

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Save",
            command=save,
        ).pack(
            pady=20,
        )

    # ============================================================
    # SUPPLIERS
    # ============================================================

    def show_suppliers(self) -> None:
        if not self.require_permission(
            Permission.MANAGE_INVENTORY
        ):
            return

        self.clear_content()

        ttk.Label(
            self.content_frame,
            text="Supplier Management",
            style="Heading.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

        ttk.Button(
            self.content_frame,
            text="Refresh Suppliers",
            command=self.load_suppliers,
        ).pack(
            anchor="w",
            pady=5,
        )

        ttk.Button(
            self.content_frame,
            text="Create Supplier",
            command=self.create_supplier_dialog,
        ).pack(
            anchor="w",
            pady=5,
        )

        columns = (
            "id",
            "name",
            "phone",
            "email",
            "address",
        )

        self.supplier_tree = ttk.Treeview(
            self.content_frame,
            columns=columns,
            show="headings",
        )

        for column, heading in {
            "id": "ID",
            "name": "Name",
            "phone": "Phone",
            "email": "Email",
            "address": "Address",
        }.items():
            self.supplier_tree.heading(
                column,
                text=heading,
            )

        self.supplier_tree.pack(
            fill="both",
            expand=True,
            pady=15,
        )

        self.load_suppliers()

    def load_suppliers(self) -> None:
        try:
            suppliers = (
                self.inventory_service.get_all_suppliers(
                    self.session
                )
            )

            for row in self.supplier_tree.get_children():
                self.supplier_tree.delete(row)

            for supplier in suppliers:
                self.supplier_tree.insert(
                    "",
                    "end",
                    values=(
                        supplier.supplier_id,
                        supplier.name,
                        supplier.phone,
                        supplier.email,
                        supplier.address,
                    ),
                )

        except Exception as exc:
            self.show_error(exc)

    def create_supplier_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Supplier")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()

        name_var = tk.StringVar()
        phone_var = tk.StringVar()
        email_var = tk.StringVar()
        address_var = tk.StringVar()

        self._entry_row(
            dialog,
            "Name:",
            name_var,
        )

        self._entry_row(
            dialog,
            "Phone:",
            phone_var,
        )

        self._entry_row(
            dialog,
            "Email:",
            email_var,
        )

        self._entry_row(
            dialog,
            "Address:",
            address_var,
        )

        def save() -> None:
            try:
                self.inventory_service.create_supplier(
                    self.session,
                    name_var.get(),
                    phone_var.get(),
                    email_var.get(),
                    address_var.get(),
                )

                dialog.destroy()

                self.show_info(
                    "Supplier created successfully."
                )

                self.load_suppliers()

            except Exception as exc:
                self.show_error(exc)

        ttk.Button(
            dialog,
            text="Save",
            command=save,
        ).pack(
            pady=20,
        )

    # ============================================================
    # REPORTS
    # ============================================================

    def show_reports(self) -> None:
        if not self.require_permission(
            Permission.VIEW_REPORTS
        ):
            return

        self.clear_content()

        ttk.Label(
            self.content_frame,
            text="Operational Reports",
            style="Heading.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

        buttons = ttk.Frame(
            self.content_frame,
        )
        buttons.pack(
            fill="x",
            pady=10,
        )

        ttk.Button(
            buttons,
            text="Sales Report",
            command=self.show_sales_report,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            buttons,
            text="Order Report",
            command=self.show_order_report,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            buttons,
            text="Menu Performance",
            command=self.show_menu_performance_report,
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Button(
            buttons,
            text="Inventory Report",
            command=self.show_inventory_report,
        ).pack(
            side="left",
            padx=3,
        )

        self.report_text = tk.Text(
            self.content_frame,
            wrap="none",
            font=("Consolas", 10),
        )

        self.report_text.pack(
            fill="both",
            expand=True,
            pady=15,
        )

    def _display_report(
        self,
        title: str,
        report,
    ) -> None:

        self.report_text.delete(
            "1.0",
            tk.END,
        )

        self.report_text.insert(
            tk.END,
            f"{title}\n"
        )

        self.report_text.insert(
            tk.END,
            "=" * 90 + "\n\n"
        )

        self.report_text.insert(
            tk.END,
            str(report),
        )

    def show_sales_report(self) -> None:
        try:
            report = (
                self.reporting_service.get_sales_report(
                    self.session
                )
            )

            text = (
                "SALES REPORT\n\n"
                "Payment ID | Order ID | Amount | "
                "Method | Status\n"
            )

            text += "-" * 80 + "\n"

            for record in report["records"]:
                text += (
                    f"{record['payment_id']} | "
                    f"{record['order_id']} | "
                    f"{record['amount']:.2f} | "
                    f"{record['payment_method']} | "
                    f"{record['status']}\n"
                )

            text += (
                "\nTOTAL SALES: "
                f"{report['total_sales']:.2f}"
            )

            self.report_text.delete(
                "1.0",
                tk.END,
            )

            self.report_text.insert(
                tk.END,
                text,
            )

        except Exception as exc:
            self.show_error(exc)

    def show_order_report(self) -> None:
        try:
            report = (
                self.reporting_service.get_order_report(
                    self.session
                )
            )

            text = (
                "ORDER REPORT\n\n"
                "Status | Number of Orders\n"
            )

            text += "-" * 50 + "\n"

            for record in report["records"]:
                text += (
                    f"{record['status']} | "
                    f"{record['order_count']}\n"
                )

            text += (
                "\nTOTAL ORDERS: "
                f"{report['total_orders']}"
            )

            self.report_text.delete(
                "1.0",
                tk.END,
            )

            self.report_text.insert(
                tk.END,
                text,
            )

        except Exception as exc:
            self.show_error(exc)

    def show_menu_performance_report(self) -> None:
        try:
            report = (
                self.reporting_service
                .get_menu_performance_report(
                    self.session
                )
            )

            text = (
                "MENU PERFORMANCE REPORT\n\n"
                "Item | Category | Qty Sold | Revenue\n"
            )

            text += "-" * 80 + "\n"

            for record in report["records"]:
                text += (
                    f"{record['item_name']} | "
                    f"{record['category_name']} | "
                    f"{record['quantity_sold']} | "
                    f"{record['revenue']:.2f}\n"
                )

            self.report_text.delete(
                "1.0",
                tk.END,
            )

            self.report_text.insert(
                tk.END,
                text,
            )

        except Exception as exc:
            self.show_error(exc)

    def show_inventory_report(self) -> None:
        try:
            report = (
                self.reporting_service
                .get_inventory_report(
                    self.session
                )
            )

            text = (
                "INVENTORY REPORT\n\n"
                "Item | Quantity | Unit | Supplier | Status\n"
            )

            text += "-" * 90 + "\n"

            threshold = report[
                "low_stock_threshold"
            ]

            for record in report["records"]:
                text += (
                    f"{record['item_name']} | "
                    f"{record['quantity']} | "
                    f"{record['unit']} | "
                    f"{record['supplier_name']} | "
                    f"{record['status']}\n"
                )

            text += (
                "\nLow-stock threshold: "
                f"{threshold}"
            )

            self.report_text.delete(
                "1.0",
                tk.END,
            )

            self.report_text.insert(
                tk.END,
                text,
            )

        except Exception as exc:
            self.show_error(exc)

    # ============================================================
    # LOGOUT
    # ============================================================

    def logout(self) -> None:
        if not self.confirm(
            "Are you sure you want to logout?"
        ):
            return

        try:
            self.authentication_service.logout()
        except Exception:
            pass

        self.session = None
        self.show_login()

    # ============================================================
    # UTILITY
    # ============================================================

    def _entry_row(
        self,
        parent,
        label_text: str,
        variable: tk.StringVar,
    ) -> ttk.Entry:

        ttk.Label(
            parent,
            text=label_text,
        ).pack(
            anchor="w",
            padx=20,
            pady=(10, 5),
        )

        entry = ttk.Entry(
            parent,
            textvariable=variable,
            width=40,
        )

        entry.pack(
            padx=20,
        )

        return entry