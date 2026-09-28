# RMS Configuration Instructions

## Database

The default SQLite database path is:

```text
database/restaurant_management.db
```

The path is resolved by `DatabaseManager` relative to the project root.

## Database initialization options

```powershell
python main.py --init-db
```

Creates the schema and loads the sample data.

```powershell
python main.py --init-db --no-seed
```

Creates the schema without sample data.

`--no-seed` without `--init-db` is rejected.

## Low-stock threshold

The finalized default threshold is **10 units**.

Low stock is defined as:

```text
quantity <= 10
```

The value is configured in:

```text
app/config/inventory_config.py
```

Reporting also uses the same business threshold of 10 units.

## Roles

The authorization service defines these roles:

- Administrator: full operational access
- Manager: menu/order/customer/report viewing and operational management allowed by the existing RBAC, with inventory monitoring but no inventory modification
- Staff/Cashier: menu viewing, order management, and payment processing

Authorization is enforced in the business layer, not only by hiding CLI choices.

## Passwords

Do not place plaintext passwords in SQL seed files or source code. Use `scripts/create_user.py` to create accounts interactively.
