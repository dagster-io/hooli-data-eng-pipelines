{{ config(severity = 'warn') }}
SELECT
    user_id,
    dt,
    order_total
FROM {{ ref('orders_cleaned') }}
WHERE order_total <= 0
