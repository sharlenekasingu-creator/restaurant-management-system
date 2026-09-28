from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path


def backup_database(source: str | Path, destination: str | Path | None = None) -> Path:
    """Create a consistent SQLite backup using SQLite's backup API."""
    source_path = Path(source)
    if not source_path.is_file():
        raise FileNotFoundError(f"Database not found: {source_path}")

    if destination is None:
        destination_path = Path("backups") / (
            f"restaurant_management_{datetime.now():%Y%m%d_%H%M%S}.db"
        )
    else:
        destination_path = Path(destination)

    destination_path.parent.mkdir(parents=True, exist_ok=True)

    source_connection = sqlite3.connect(str(source_path))
    try:
        destination_connection = sqlite3.connect(str(destination_path))
        try:
            source_connection.backup(destination_connection)
            destination_connection.commit()
        finally:
            destination_connection.close()
    finally:
        source_connection.close()

    return destination_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Back up the RMS SQLite database.")
    parser.add_argument(
        "--source",
        default="database/restaurant_management.db",
        help="Path to the source SQLite database.",
    )
    parser.add_argument(
        "--destination",
        help="Optional destination .db file.",
    )
    args = parser.parse_args()

    try:
        path = backup_database(args.source, args.destination)
    except (OSError, sqlite3.Error) as exc:
        print(f"Backup failed: {exc}")
        return 1

    print(f"Backup created: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
