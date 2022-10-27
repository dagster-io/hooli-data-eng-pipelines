select
        date,
        sku,
        count(*) as n_orders,
        sum(order_total) as total_revenue
from DEMO_DB2.analytics.orders_augmented
group by 1, 2