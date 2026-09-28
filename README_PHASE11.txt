Phase 11 patch: Inventory and Suppliers

Included:
- app/business/inventory_service.py
- app/config/inventory_config.py
- app/config/__init__.py
- app/presentation/cli.py
- main.py
- tests/test_inventory_management.py

Existing files intentionally not replaced:
- app/models/inventory.py
- app/models/supplier.py
- app/data_access/repositories.py
- database/schema.sql
- database/seed.sql

Those already provide the supplier/inventory domain models, repositories, and database tables.

Low-stock threshold:
- DEFAULT_LOW_STOCK_THRESHOLD is None because the proposal does not define a business threshold.
- Set it explicitly in app/config/inventory_config.py when the business requirement is known.

Important Phase 10 note:
- Keep the existing Phase 10 payment_service.py and current payment persistence fix.
- Keep the latest test_cli.py from the working project. Because Phase 11 changes the main menu, update its exit choice from 3 to 4 wherever it tests application shutdown.

Validation performed on the patch:
- Python compilation passed.
- Phase 11 inventory management tests: 12 passed.
- Existing inventory/supplier model tests: 8 passed.
