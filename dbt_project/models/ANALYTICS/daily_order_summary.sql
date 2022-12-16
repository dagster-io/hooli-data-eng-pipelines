
{{
        config(
                dagster_freshness_policy={"cron_schedule": "0 9 * * *", "maximum_lag_minutes": 60}
        )
}}

select
        order_date,
        n_orders as num_orders
from {{ ref("order_stats") }}
