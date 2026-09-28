# RMS Test Cases

| ID | Test | Expected result |
|---|---|---|
| TC01 | Initialize database with seed | SQLite DB and required tables are created; sample operational data exists |
| TC02 | Initialize database without seed | Schema is created without sample records |
| TC03 | Create user | Password is hashed and account is stored |
| TC04 | Authenticate valid user | Authenticated session is created |
| TC05 | Authenticate invalid user | Authentication error is returned |
| TC06 | Administrator menu | Administrator sees all authorized functions |
| TC07 | Manager menu | Manager sees only authorized functions |
| TC08 | Staff/Cashier menu | Staff/Cashier sees only authorized functions |
| TC09 | Inventory threshold | Quantity 10 is low stock; quantity 11 is not |
| TC10 | Sales report | Completed payments appear in sales total |
| TC11 | Order report | Orders are grouped by status |
| TC12 | Menu performance | Quantity and revenue are calculated from completed orders |
| TC13 | Inventory report | Inventory and low-stock status are displayed |
| TC14 | SQL injection | Injection input does not bypass authentication/search |
| TC15 | Backup | Valid SQLite backup is created |
| TC16 | Restore | Valid backup restores and passes integrity check |
| TC17 | Clean install | Temporary clean copy initializes and authenticates successfully |
| TC18 | Full regression | All existing tests pass |
