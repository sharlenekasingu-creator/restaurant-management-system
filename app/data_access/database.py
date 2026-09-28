from __future__ import annotations

import sqlite3

from pathlib import Path
from typing import Optional

from app.exceptions import DatabaseError


class DatabaseManager:
    """Manages SQLite database connections and initialization."""

    def __init__(
        self,
        database_path: Optional[str] = None
    ) -> None:

        if database_path is None:
            project_root = Path(__file__).resolve().parents[2]

            database_path = str(
                project_root
                / "database"
                / "restaurant_management.db"
            )

        self._database_path = Path(database_path)

    @property
    def database_path(self) -> Path:
        """Return the database file path."""
        return self._database_path

    def connect(self) -> sqlite3.Connection:
        """Create a SQLite database connection."""

        try:
            self._database_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            connection = sqlite3.connect(
                str(self._database_path)
            )

            connection.execute(
                "PRAGMA foreign_keys = ON"
            )

            connection.row_factory = sqlite3.Row

            return connection

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to connect to database: {exc}"
            ) from exc

    def execute_script(
        self,
        script_path: str
    ) -> None:
        """Execute a SQL script and close the connection."""

        path = Path(script_path)

        if not path.is_file():
            raise DatabaseError(
                f"SQL script was not found: {path}"
            )

        connection = None

        try:
            sql_script = path.read_text(
                encoding="utf-8"
            )

            connection = self.connect()

            connection.executescript(sql_script)

            connection.commit()

        except (OSError, sqlite3.Error) as exc:

            if connection is not None:
                connection.rollback()

            raise DatabaseError(
                f"Unable to execute SQL script: {exc}"
            ) from exc

        finally:

            if connection is not None:
                connection.close()

    def initialize_database(
        self,
        seed: bool = True
    ) -> None:
        """Create the database schema and optionally seed data."""

        project_root = Path(__file__).resolve().parents[2]

        schema_path = (
            project_root
            / "database"
            / "schema.sql"
        )

        seed_path = (
            project_root
            / "database"
            / "seed.sql"
        )

        self.execute_script(str(schema_path))

        if seed:
            self.execute_script(str(seed_path))

    def database_exists(self) -> bool:
        """Check whether the database file exists."""
        return self._database_path.is_file()

    def table_exists(
        self,
        table_name: str
    ) -> bool:
        """Check whether a table exists."""

        if not table_name.strip():
            raise DatabaseError(
                "Table name cannot be empty."
            )

        query = """
            SELECT name
            FROM sqlite_master
            WHERE type = ?
              AND name = ?
        """

        connection = None

        try:
            connection = self.connect()

            result = connection.execute(
                query,
                ("table", table_name)
            ).fetchone()

            return result is not None

        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Unable to check table: {exc}"
            ) from exc

        finally:

            if connection is not None:
                connection.close()