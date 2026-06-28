-- dbt model: fct_customer_orders (demo file for Dispatch PR workflow)
-- This file intentionally references customer_segment (old name)
-- Dispatch will propose: rename customer_segment -> customer_tier

SELECT
    o.order_id,
    o.order_date,
    o.order_total,
    c.customer_id,
    c.customer_segment,
    c.company,
    SUM(o.order_total) AS total_revenue
FROM {{ ref('orders_cleaned') }} o
LEFT JOIN {{ ref('users_cleaned') }} c ON o.user_id = c.user_id
GROUP BY 1,2,3,4,5,6
