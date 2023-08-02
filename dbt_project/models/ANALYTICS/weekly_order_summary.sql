
{{
        config(
                dagster_auto_materialize_policy={"type":"eager"},
                dagster_freshness_policy={"cron_schedule": "0 9 * * MON", "maximum_lag_minutes": (24+9)*60}
        )
}}

select
        order_date,
        n_orders as num_orders
from {{ ref("order_stats") }}
{% if is_incremental() %}
WHERE o.order_date >= '{{ var('min_date') }}' AND o.order_date <= '{{ var('max_date') }}'
{% endif %}
