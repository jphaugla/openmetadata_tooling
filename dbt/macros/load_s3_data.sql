{% macro load_s3_data() %}

{% set aws_key = env_var('AWS_ACCESS_KEY_ID', '') %}
{% set aws_secret = env_var('AWS_SECRET_ACCESS_KEY', '') %}
{% set aws_token = env_var('AWS_SESSION_TOKEN', '') %}

{% set creds_str = "" %}
{% if aws_key != '' %}
  {% set creds_str = "CREDENTIALS = (AWS_KEY_ID='" ~ aws_key ~ "' AWS_SECRET_KEY='" ~ aws_secret ~ "' AWS_TOKEN='" ~ aws_token ~ "')" %}
{% else %}
  {{ log("WARNING: Missing AWS env variables! COPY INTO will likely fail.", info=True) }}
{% endif %}


{% set customers_sql %}
COPY INTO CUSTOMERS.COLLATE_SE.RAW_CUSTOMERS
FROM 's3://collate-snowflake-interchange-118146679784/customers/raw_customers_export.csv'
{{ creds_str }}
FILE_FORMAT = (TYPE = 'CSV', SKIP_HEADER = 1, FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';
{% endset %}

{% set orders_sql %}
COPY INTO CUSTOMERS.COLLATE_SE.RAW_ORDERS
FROM 's3://collate-snowflake-interchange-118146679784/orders/raw_orders_export.csv'
{{ creds_str }}
FILE_FORMAT = (TYPE = 'CSV', SKIP_HEADER = 1, FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';
{% endset %}

{% set items_sql %}
COPY INTO CUSTOMERS.COLLATE_SE.RAW_ORDER_ITEMS
FROM 's3://collate-snowflake-interchange-118146679784/order_items/raw_order_items_export.csv'
{{ creds_str }}
FILE_FORMAT = (TYPE = 'CSV', SKIP_HEADER = 1, FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';
{% endset %}

{% set products_sql %}
COPY INTO CUSTOMERS.COLLATE_SE.RAW_PRODUCTS
FROM 's3://collate-snowflake-interchange-118146679784/products/raw_products_export.csv'
{{ creds_str }}
FILE_FORMAT = (TYPE = 'CSV', SKIP_HEADER = 1, FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';
{% endset %}

{{ log("Copying Customers from S3...", info=True) }}
{% do run_query(customers_sql) %}

{{ log("Copying Orders from S3...", info=True) }}
{% do run_query(orders_sql) %}

{{ log("Copying Order Items from S3...", info=True) }}
{% do run_query(items_sql) %}

{{ log("Copying Products from S3...", info=True) }}
{% do run_query(products_sql) %}

{{ log("✅ S3 Data successfully loaded into Snowflake RAW tables!", info=True) }}

{% endmacro %}
