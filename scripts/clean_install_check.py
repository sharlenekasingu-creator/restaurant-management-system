from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


def run_clean_install_check(project_root: str | Path | None = None) -> None:
    """Run a disposable clean-install smoke test without touching the live DB."""
    root = Path(project_root or Path(__file__).resolve().parents[1]).resolve()
    main_py = root / "main.py"

    if not main_py.is_file():
        raise FileNotFoundError(f"main.py not found in {root}")

    with tempfile.TemporaryDirectory(prefix="rms_clean_install_") as temp_dir:
        temp_root = Path(temp_dir) / "restaurant_management_system"
        shutil.copytree(
            root,
            temp_root,
            ignore=shutil.ignore_patterns(
                "*.db",
                "*.pyc",
                "__pycache__",
                ".git",
                "backups",
            ),
        )

        def run_main(*args: str) -> None:
            completed = subprocess.run(
                [sys.executable, "main.py", *args],
                cwd=temp_root,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    "Clean-install command failed:\n"
                    + completed.stdout
                    + completed.stderr
                )

        run_main("--init-db", "--no-seed")
        run_main("--init-db")

        database_path = temp_root / "database" / "restaurant_management.db"
        if not database_path.is_file():
            raise RuntimeError("Database initialization did not create the database file.")

        connection = sqlite3.connect(str(database_path))
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = ?",
                    ("table",),
                )
            }
            required_tables = {
                "roles",
                "users",
                "menu_categories",
                "menu_items",
                "customers",
                "orders",
                "order_items",
                "payments",
                "suppliers",
                "inventory",
            }
            missing = required_tables - tables
            if missing:
                raise RuntimeError(f"Missing database tables: {sorted(missing)}")
        finally:
            connection.close()

        # Verify authentication using the application's real business layer.
        sys.path.insert(0, str(temp_root))
        try:
            from app.business.authentication_service import (
                AuthenticationServiceImplementation,
            )
            from app.data_access.database import DatabaseManager
            from app.data_access.repositories import RoleRepository, UserRepository

            database = DatabaseManager(str(database_path))
            auth = AuthenticationServiceImplementation(
                UserRepository(database),
                RoleRepository(database),
            )
            auth.register_user(
                "clean_install_admin",
                "CleanInstall123",
                "Administrator",
                "Clean Install Administrator",
                "clean@example.local",
            )
            session = auth.authenticate(
                "clean_install_admin",
                "CleanInstall123",
            )
            if not session.authenticated:
                raise RuntimeError("Clean-install authentication failed.")
        finally:
            sys.path.pop(0)

    print("Clean installation check passed.")
    print("Database initialization: OK")
    print("Schema verification: OK")
    print("Authentication verification: OK")


if __name__ == "__main__":
    run_clean_install_check()
