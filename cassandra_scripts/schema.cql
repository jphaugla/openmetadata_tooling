-- Create a keyspace for the demo
CREATE KEYSPACE IF NOT EXISTS ecommerce_demo 
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE ecommerce_demo;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id uuid PRIMARY KEY,
    first_name text,
    last_name text,
    email text,
    phone text,
    created_at timestamp,
    city text,
    state text
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id uuid PRIMARY KEY,
    name text,
    category text,
    description text,
    price decimal,
    stock_quantity int,
    created_at timestamp
);

-- Orders table (partitioned by user_id for demonstration)
CREATE TABLE IF NOT EXISTS orders_by_user (
    user_id uuid,
    order_id uuid,
    order_date timestamp,
    total_amount decimal,
    status text,
    PRIMARY KEY (user_id, order_date)
) WITH CLUSTERING ORDER BY (order_date DESC);

-- Inventory movements for time-series demonstration
CREATE TABLE IF NOT EXISTS inventory_log (
    product_id uuid,
    movement_id timeuuid,
    change_amount int,
    reason text,
    timestamp timestamp,
    PRIMARY KEY (product_id, movement_id)
) WITH CLUSTERING ORDER BY (movement_id DESC);
