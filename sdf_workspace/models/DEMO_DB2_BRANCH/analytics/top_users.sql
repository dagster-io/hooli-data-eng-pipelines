select
        o.user_id,
        sum(o.order_total) as total_revenue,
        sum(o.order_total) / max(c.total_revenue) as pct_revenue
from
        DEMO_DB2_BRANCH.analytics.orders_augmented o left join
        DEMO_DB2_BRANCH.analytics.company_perf c on o.company = c.company
group by 1