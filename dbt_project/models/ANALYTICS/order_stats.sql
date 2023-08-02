{{
        config(
                dagster_auto_materialize_policy={"type":"eager"}
        )
}}
select
        {{ date_trunc("day", "order_date") }} as order_date,
        count(*) as n_orders,
        sum(order_total) as total_revenue
from {{ ref("orders_augmented") }}
{% if is_incremental() %}
WHERE {{ date_trunc("day", "order_date") }} >=  '{{ var('min_date') }}' AND {{ date_trunc("day", "order_date") }} <=  '{{ var('max_date') }}'
{% endif %}
group by 1