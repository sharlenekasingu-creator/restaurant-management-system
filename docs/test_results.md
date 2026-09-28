# RMS Test Results

## Phase 14 regression baseline

The completed Phase 14 project was executed with:

```powershell
python -m unittest discover -s tests -v
```

Result in the deployment verification environment:

```text
Ran 216 tests in 27.147s
OK
```

This confirms 216 existing unit, integration, system, security, and regression tests passed before the Phase 15 deployment additions.

## Phase 15 deployment tests

Five additional deployment tests were added. They cover database initialization, seeded data, secure user creation, the 10-unit low-stock configuration, and SQLite backup/restore integrity.

Run:

```powershell
python -m unittest tests.test_deployment_phase15 -v
```

The deployment test file verifies database initialization, seeded data, secure user creation, the 10-unit low-stock configuration, and SQLite backup/restore integrity.

Executed result:

```text
Ran 5 tests in 0.208s
OK
```

## Clean installation smoke test

Run:

```powershell
python scripts/clean_install_check.py
```

Expected result:

```text
Clean installation check passed.
Database initialization: OK
Schema verification: OK
Authentication verification: OK
```

## Important distinction

The 216-test result is the executed Phase 14 regression result. Phase 15 adds deployment-specific tests and must be executed after these files are copied into the final project. The final deployment verification executed the complete suite after the Phase 15 additions:

```text
Ran 221 tests in 27.646s
OK
```

The disposable clean-install smoke test also passed with database initialization, schema verification, and authentication verification all reported as OK.
