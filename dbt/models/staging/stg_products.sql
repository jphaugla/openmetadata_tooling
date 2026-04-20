-- dbt/models/staging/stg_products.sql

SELECT
    product_id,
    product_name,
    category,
    eco_friendly,
    unit_price
FROM {{ source('snowflake_raw', 'RAW_PRODUCTS') }}
