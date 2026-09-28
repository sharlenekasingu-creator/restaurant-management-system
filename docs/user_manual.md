# RMS User Manual

## Login

1. Start the application with `python main.py`.
2. Enter your username.
3. Enter your password when prompted.
4. The system displays the authenticated user's role.
5. The main menu contains only functions permitted for that role.

## Administrator

Administrator access includes:

- Menu Management / View Menu
- Customer Management
- Customer Order Management
- Payment Processing
- Inventory Management
- Reporting
- Logout
- Exit

## Manager

Manager access includes the functions permitted by the current RBAC configuration. Inventory is view/monitor only. Inventory creation, stock changes, and supplier management are protected by the business-layer authorization checks.

## Staff/Cashier

Staff/Cashier access is limited to the functions permitted by the current RBAC configuration, including menu viewing, customer order management, and payment processing.

## Menu

Use Menu Management / View Menu to:

- View menu items
- View categories
- Perform authorized category and item management
- Change authorized item availability

## Customers

Customer Management provides:

- View customers
- Search customers
- Create customer
- Update customer
- Delete customer

## Orders

Customer Order Management provides:

- Create customer order
- View order
- Return

During order creation, select or create a customer, choose menu items, enter quantities, calculate the order total, and save the order.

## Payments

Payment Processing loads an order, accepts the payment amount and payment method, calculates change, records the payment, and displays a receipt.

## Inventory

Inventory Management provides authorized functions for viewing inventory, low-stock monitoring, stock changes, and supplier management according to RBAC.

Low-stock status is based on `quantity <= 10`.

## Reports

Reporting provides:

1. Sales Report
2. Order Report
3. Menu Performance Report
4. Inventory Report

Manager and Administrator roles have report access according to the existing authorization policy.

## Logout and Exit

- **Logout** ends the authenticated session and returns control to login.
- **Exit** shuts down the application.
