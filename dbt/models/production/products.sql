-- dbt/models/production/products.sql

WITH staged AS (
    SELECT * FROM {{ ref('stg_products') }}
),

final AS (
    SELECT
        product_id,
        product_name,
        category,
        eco_friendly,
        unit_price
    FROM staged
)

SELECT * FROM final
