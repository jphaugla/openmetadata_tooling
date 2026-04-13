-- dbt/models/staging/stg_customers.sql

SELECT
    ID as customer_id,
    FIRST_NAME,
    LAST_NAME
FROM {{ source('snowflake_raw', 'RAW_CUSTOMERS') }}
