# Restaurant Management System

## Phase 1 - Project Foundation

This project is the initial foundation for a Restaurant Management System (RMS).

The application is developed using Python 3.x and follows a three-layer architecture:

- Presentation Layer
- Business Logic Layer
- Data Access Layer

SQLite will be used as the relational database during development.

## Current Functionality

Phase 1 provides:

- Python project structure
- Command-line interface
- Restaurant Management System title
- Main menu
- Exit option
- Clean application startup
- Clean application shutdown
- Basic automated tests

The following features are intentionally NOT implemented in Phase 1:

- Authentication
- User accounts
- Role-based authorization
- Menu management
- Orders
- Payments
- Inventory
- Reports
- GUI
- Web application
- Mobile application
- Online ordering

These features can be implemented in later phases.

## Project Structure

```text
restaurant_management_system/
├── app/
│   ├── presentation/
│   ├── business/
│   ├── data_access/
│   ├── models/
│   ├── validation/
│   └── exceptions/
├── database/
├── tests/
├── docs/
├── main.py
├── requirements.txt
└── README.md