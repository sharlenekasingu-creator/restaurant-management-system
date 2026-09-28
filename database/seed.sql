PRAGMA foreign_keys = ON;

INSERT OR IGNORE INTO roles (name, description)
VALUES
    (
        'Administrator',
        'Full system access'
    ),
    (
        'Manager',
        'Restaurant management role'
    ),
    (
        'Staff/Cashier',
        'Restaurant staff and cashier role'
    );

INSERT OR IGNORE INTO menu_categories (name, description)
VALUES
    ('Main Meals', 'Main meals served by the restaurant'),
    ('Drinks', 'Cold and hot drinks');

INSERT OR IGNORE INTO menu_items
    (name, price, category_id, description, is_available)
VALUES
    (
        'Chicken Rice',
        15.00,
        (SELECT category_id
         FROM menu_categories
         WHERE name = 'Main Meals'),
        'Chicken served with rice',
        1
    ),
    (
        'Beef Burger',
        12.00,
        (SELECT category_id
         FROM menu_categories
         WHERE name = 'Main Meals'),
        'Beef burger',
        1
    ),
    (
        'Soft Drink',
        4.00,
        (SELECT category_id
         FROM menu_categories
         WHERE name = 'Drinks'),
        'Cold soft drink',
        1
    );

INSERT OR IGNORE INTO suppliers
    (name, phone, email, address)
VALUES
    (
        'Fresh Foods Supplier',
        '12345678',
        'supplier@example.com',
        'Port Moresby'
    );

INSERT OR IGNORE INTO inventory
    (name, quantity, unit, supplier_id)
VALUES
    (
        'Rice',
        50,
        'kg',
        (
            SELECT supplier_id
            FROM suppliers
            WHERE name = 'Fresh Foods Supplier'
        )
    ),
    (
        'Beef',
        25,
        'kg',
        (
            SELECT supplier_id
            FROM suppliers
            WHERE name = 'Fresh Foods Supplier'
        )
    );

INSERT OR IGNORE INTO customers
    (name, phone, email)
VALUES
    (
        'Sample Customer',
        '70000000',
        'customer@example.com'
    );