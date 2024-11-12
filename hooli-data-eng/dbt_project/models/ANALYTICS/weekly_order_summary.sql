
{{
        config(
                tags=["core_kpis"]
        )
}}

select
        order_date,
        n_orders as num_orders
from {{ ref("order_stats") }}
{% if is_incremental() %}
WHERE o.order_date >= '{{ var('min_date') }}' AND o.order_date <= '{{ var('max_date') }}'
{% endif %}
