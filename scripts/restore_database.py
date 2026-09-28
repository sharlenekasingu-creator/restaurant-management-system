from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path


def validate_database(path: str | Path) -> None:
    """Validate SQLite integrity before a restore is accepted."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Backup not found: {path}")

    connection = sqlite3.connect(str(path))
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise sqlite3.DatabaseError(
                f"Integrity check failed: {result[0] if result else 'unknown'}"
            )
    finally:
        connection.close()


def restore_database(backup: str | Path, destination: str | Path) -> Path | None:
    """Restore a validated backup, preserving the current DB first."""
    backup_path = Path(backup)
    destination_path = Path(destination)
    validate_database(backup_path)

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    pre_restore_backup: Path | None = None

    if destination_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore_backup = destination_path.with_name(
            f"{destination_path.stem}_pre_restore_{timestamp}.db"
        )
        shutil.copy2(destination_path, pre_restore_backup)

    with tempfile.NamedTemporaryFile(
        prefix="rms_restore_",
        suffix=".db",
        dir=destination_path.parent,
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        shutil.copy2(backup_path, temp_path)
        validate_database(temp_path)
        os.replace(temp_path, destination_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return pre_restore_backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore the RMS SQLite database.")
    parser.add_argument("backup", help="Validated SQLite backup file.")
    parser.add_argument(
        "--destination",
        default="database/restaurant_management.db",
        help="Destination database path.",
    )
    args = parser.parse_args()

    try:
        previous = restore_database(args.backup, args.destination)
    except (OSError, sqlite3.Error) as exc:
        print(f"Restore failed: {exc}")
        return 1

    print(f"Database restored to: {args.destination}")
    if previous:
        print(f"Previous database preserved at: {previous}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
