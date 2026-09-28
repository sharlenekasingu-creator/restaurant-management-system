# RMS Technical Documentation

## Architecture

The project follows three layers.

### Presentation Layer

`app/presentation/cli.py` handles command-line interaction, menu navigation, input collection, and presentation of results.

### Business Logic Layer

`app/business/` contains authentication, authorization, menu, customer, order, payment, inventory, and reporting services. Business services validate input and enforce authorization before protected operations.

### Data Access Layer

`app/data_access/` contains `DatabaseManager` and repositories. SQLite operations use parameterized SQL for data values.

## Database

SQLite is the development database. `DatabaseManager` creates the database directory, opens connections, enables foreign-key enforcement, executes the schema, and optionally executes the seed script.

The current schema contains:

- roles
- users
- menu_categories
- menu_items
- customers
- orders
- order_items
- payments
- suppliers
- inventory

Indexes support common foreign-key and lookup operations.

## Authentication

Passwords are hashed using PBKDF2-HMAC-SHA256 with a random salt. The authentication service verifies the stored hash and rejects invalid or inactive accounts.

## Authorization

`AuthorizationService` maps roles to permissions and exposes `require_permission_for_session()` for protected business operations.

## Reporting

`ReportingRepository` retrieves persisted data using parameterized SELECT statements. `BasicReportingService` applies authorization and transforms repository rows into report structures used by the CLI.

## Inventory threshold

The finalized low-stock rule is:

```text
quantity <= 10
```

## Error handling

Repository failures are converted into application-specific errors by the business services where appropriate. CLI methods catch expected application exceptions and display an error rather than exposing a traceback to normal users.

## Production database limitation

The implementation has been developed and tested against SQLite. It has **not** been tested against MySQL or PostgreSQL. Therefore this project does not claim production compatibility with either database engine.
