# RMS Phase 15 Test Plan

## Objectives

Verify that the completed RMS can be installed into a clean environment, initialize its database, start, authenticate users, execute core operational workflows, and recover from a database backup.

## Test levels

1. Unit tests: models, validation, services, calculations, repositories.
2. Integration tests: database and service integration.
3. System tests: role-aware CLI workflows.
4. Security tests: hashing, authentication, RBAC, SQL injection, invalid input, database errors.
5. Regression tests: all previous phase tests.
6. Deployment tests: initialization, sample data, default configuration, backup, restore, and clean-install smoke test.

## Entry criteria

- Project files are present.
- Python 3.x is installed.
- No third-party package installation is required.

## Exit criteria

- Complete test suite passes.
- Clean-install check passes.
- Backup and restore integrity checks pass.
- Manual smoke test completes for Administrator, Manager, and Staff/Cashier.

## Known limitation

Production MySQL/PostgreSQL compatibility is outside the evidence because the implementation has not been tested against those database engines.
