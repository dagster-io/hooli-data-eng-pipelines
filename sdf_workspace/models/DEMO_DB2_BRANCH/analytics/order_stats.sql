select
        date_trunc('day', order_date) as order_date,
        count(*) as n_orders,
        sum(order_total) as total_revenue
from DEMO_DB2_BRANCH.analytics.orders_augmented

group by 1