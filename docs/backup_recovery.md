# RMS Backup and Recovery Procedure

## Backup procedure

1. Stop the RMS application before a routine manual backup where possible.
2. Run:

```powershell
python scripts/backup_database.py
```

3. Confirm that a timestamped `.db` file was created under `backups/`.
4. Store a copy of the backup separately from the application directory.
5. Periodically test a backup by validating or restoring it to a separate location.

## Validate a backup

```powershell
python scripts/restore_database.py <backup-file> --destination database/test_restore.db
```

The restore utility validates SQLite integrity before replacing the destination.

## Recovery procedure

1. Stop the application.
2. Identify the most recent known-good backup.
3. Do not overwrite the current database without preserving it.
4. Run the restore command:

```powershell
python scripts/restore_database.py <backup-file>
```

5. The existing database is copied to a `*_pre_restore_YYYYMMDD_HHMMSS.db` file before replacement.
6. Start the application.
7. Verify authentication, menu, customers, orders, payments, inventory, and reports.
8. Run the regression tests if source code was changed during recovery.

## Recovery limitations

The backup utility protects the SQLite database file. It does not back up application source code, configuration files, or operating-system settings. Back up the complete project directory separately for full disaster recovery.
