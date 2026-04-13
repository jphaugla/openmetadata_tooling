-- dbt/models/production/orders.sql

WITH staged AS (
    SELECT * FROM CUSTOMERS.COLLATE_SE.stg_orders
)

SELECT
    order_id,
    customer_id,
    order_date,
    status
FROM staged