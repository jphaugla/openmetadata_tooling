-- One Database, Two Schemas (The most common Postgres pattern)
CREATE DATABASE ecommerce_db;
\c ecommerce_db

CREATE SCHEMA raw;
CREATE SCHEMA analytics;

-- Producer
CREATE TABLE raw.orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    total_amount NUMERIC(10,2),
    status VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Consumer (The view that connects the dots)
CREATE VIEW analytics.daily_sales_summary AS
SELECT 
    order_date,
    count(order_id) as transaction_count,
    sum(total_amount) as revenue
FROM raw.orders
WHERE status = 'shipped'
GROUP BY order_date;

-- Add the foreign key constraint
ALTER TABLE raw.orders 
ADD CONSTRAINT fk_customer 
FOREIGN KEY (customer_id) 
REFERENCES raw.customers(customer_id)
ON DELETE CASCADE;

SET search_path TO public;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
