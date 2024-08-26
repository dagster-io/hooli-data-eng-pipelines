
select
        order_date,
        company,
        count(*) as n_orders,
        sum(order_total) as total_revenue
from DEMO_DB2_BRANCH.analytics.orders_augmented
group by 1, 2