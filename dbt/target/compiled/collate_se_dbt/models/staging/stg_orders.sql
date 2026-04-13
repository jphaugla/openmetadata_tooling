-- dbt/models/staging/stg_orders.sql
SELECT
    ID as order_id,
    USER_ID as customer_id,
    ORDER_DATE,
    STATUS
FROM CUSTOMERS.COLLATE_SE.RAW_ORDERS