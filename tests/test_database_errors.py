import tempfile
import unittest
from pathlib import Path

from app.data_access.database import DatabaseManager
from app.exceptions import DatabaseError


class TestDatabaseErrors(unittest.TestCase):

    def test_missing_sql_script_raises_database_error(self):
        with tempfile.TemporaryDirectory() as temp_directory:

            database_path = (
                Path(temp_directory)
                / "test_restaurant.db"
            )

            manager = DatabaseManager(
                str(database_path)
            )

            missing_script = (
                Path(temp_directory)
                / "missing.sql"
            )

            with self.assertRaises(DatabaseError):
                manager.execute_script(
                    str(missing_script)
                )

    def test_invalid_sql_raises_database_error(self):
        with tempfile.TemporaryDirectory() as temp_directory:

            database_path = (
                Path(temp_directory)
                / "test_restaurant.db"
            )

            manager = DatabaseManager(
                str(database_path)
            )

            invalid_sql = (
                Path(temp_directory)
                / "invalid.sql"
            )

            invalid_sql.write_text(
                "THIS IS NOT VALID SQL;",
                encoding="utf-8"
            )

            with self.assertRaises(DatabaseError):
                manager.execute_script(
                    str(invalid_sql)
                )

    def test_database_connection_is_created(self):
        with tempfile.TemporaryDirectory() as temp_directory:

            database_path = (
                Path(temp_directory)
                / "test_restaurant.db"
            )

            manager = DatabaseManager(
                str(database_path)
            )

            connection = manager.connect()

            try:
                self.assertIsNotNone(connection)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()