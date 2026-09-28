# RMS Deployment Checklist

## Installation

- [ ] Python 3.x installed
- [ ] Project extracted
- [ ] `python --version` verified
- [ ] `python main.py --init-db` completed
- [ ] Database file exists
- [ ] Sample data verified
- [ ] User created with `scripts/create_user.py`

## Application

- [ ] `python main.py` starts
- [ ] Authentication succeeds
- [ ] Administrator menu tested
- [ ] Manager menu tested
- [ ] Staff/Cashier menu tested
- [ ] Menu tested
- [ ] Customer management tested
- [ ] Orders tested
- [ ] Payments tested
- [ ] Inventory tested
- [ ] Reports tested
- [ ] Logout tested
- [ ] Exit tested

## Security

- [ ] Passwords are not stored in plaintext
- [ ] Unauthorized service calls are rejected
- [ ] SQL injection tests pass
- [ ] Invalid input tests pass

## Testing

- [ ] Full unittest suite passes
- [ ] Phase 15 deployment tests pass
- [ ] Clean-install check passes
- [ ] Backup created
- [ ] Backup integrity validated
- [ ] Restore tested on a separate destination

## Production limitation

- [ ] Do not claim MySQL/PostgreSQL compatibility unless the RMS has been separately ported and tested against the selected production database.
