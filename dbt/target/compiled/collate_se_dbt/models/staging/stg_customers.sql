-- dbt/models/staging/stg_customers.sql

SELECT
    ID as customer_id,
    FIRST_NAME,
    LAST_NAME
FROM CUSTOMERS.COLLATE_SE.RAW_CUSTOMERS