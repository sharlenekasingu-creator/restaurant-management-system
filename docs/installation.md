# RMS Installation Instructions

## 1. Requirements

- Python 3.x. Python 3.10 or newer is recommended.
- A Windows PowerShell, Command Prompt, Linux shell, or macOS terminal.
- No external Python packages are required by the current project.

## 2. Obtain the project

Extract the RMS project so the project root contains `main.py`, `app/`, `database/`, `tests/`, `scripts/`, and `docs/`.

## 3. Verify Python

```powershell
python --version
```

If `python` is not available, install Python 3.x and ensure it is available on PATH.

## 4. Create the database

From the project root:

```powershell
python main.py --init-db
```

For an empty schema without sample data:

```powershell
python main.py --init-db --no-seed
```

The database is stored in `database/restaurant_management.db`.

The application already resolves the database path relative to the project root, so it does not depend on the terminal's current subdirectory.

## 5. Create the first user

Use the interactive user-creation utility:

```powershell
python scripts/create_user.py
```

Choose one of the roles exactly as displayed:

- Administrator
- Manager
- Staff/Cashier

The password is entered with `getpass` and is passed to the existing authentication service, which stores only a PBKDF2-SHA256 hash.

## 6. Start the application

```powershell
python main.py
```

Enter the username and password created in the previous step.

## 7. Verify installation

Run:

```powershell
python scripts/clean_install_check.py
```

This creates a disposable copy, initializes the database, verifies the schema, and verifies authentication without modifying the live database.
