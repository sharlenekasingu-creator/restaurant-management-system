# RMS Architecture

```text
+-----------------------------+
| Presentation Layer          |
| app/presentation/cli.py     |
+-------------+---------------+
              |
              v
+-----------------------------+
| Business Logic Layer        |
| authentication              |
| authorization               |
| menu / customer / order     |
| payment / inventory         |
| reporting                   |
+-------------+---------------+
              |
              v
+-----------------------------+
| Data Access Layer           |
| DatabaseManager             |
| Repositories                |
+-------------+---------------+
              |
              v
+-----------------------------+
| SQLite                      |
| restaurant_management.db   |
+-----------------------------+
```

The layers communicate downward. Authorization and business rules remain in the business layer so protected operations cannot be bypassed by calling services directly.
