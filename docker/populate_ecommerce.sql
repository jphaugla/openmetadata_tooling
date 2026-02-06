-- Ensure you are in the raw schema
\c ecommerce_db
SET search_path TO raw, public;

-- Clean out any existing data if necessary
TRUNCATE TABLE orders;

-- Insert 10 sample records
INSERT INTO orders (order_id, customer_id, order_date, total_amount, status) VALUES
(101, 5001, '2026-01-15', 150.25, 'shipped'),
(102, 5002, '2026-01-15', 45.00,  'shipped'),
(103, 5003, '2026-01-16', 210.10, 'pending'),
(104, 5001, '2026-01-16', 99.99,  'shipped'),
(105, 5004, '2026-01-17', 12.50,  'cancelled'),
(106, 5005, '2026-01-17', 300.00, 'shipped'),
(107, 5002, '2026-01-18', 55.20,  'shipped'),
(108, 5006, '2026-01-18', 88.00,  'shipped'),
(109, 5007, '2026-01-19', 125.40, 'pending'),
(110, 5001, '2026-01-20', 25.00,  'shipped');

INSERT INTO raw.customers (customer_id, customer_name, email) VALUES
(5001, 'Alice Smith', 'alice@example.com'),
(5002, 'Bob Jones', 'bob@example.com'),
(5003, 'Charlie Brown', 'charlie@example.com'),
(5004, 'David Wilson', 'david@example.com'),
(5005, 'Eve Davis', 'eve@example.com'),
(5006, 'Frank Miller', 'frank@example.com'),
(5007, 'Grace Hopper', 'grace@example.com')
ON CONFLICT (customer_id) DO NOTHING;

-- Verify the data
SELECT * FROM orders;
SELECT * FROM customers;

-- Check if the analytics view is correctly picking up the 'shipped' orders
SELECT * FROM analytics.daily_sales_summary;
