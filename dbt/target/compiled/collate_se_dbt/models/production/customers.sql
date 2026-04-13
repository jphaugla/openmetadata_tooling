-- dbt/models/production/customers.sql

WITH staged AS (
    SELECT * FROM CUSTOMERS.COLLATE_SE.stg_customers
),

final AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        CONCAT(first_name, ' ', last_name) as full_name,
        CURRENT_TIMESTAMP() as last_update_at
    FROM staged
)

SELECT * FROM final