{{
        config(
                dagster_auto_materialize_policy={"type":"lazy"}
        )
}}
select
        {{ date_trunc("day", "order_date") }} as order_date,
        count(*) as n_orders,
        sum(order_total) as total_revenue
from {{ ref("orders_augmented") }}
{% if is_incremental() %}
WHERE {{ date_trunc("day", "order_date") }} = '{{ var('datetime_to_process') }}'
{% endif %}
group by 1