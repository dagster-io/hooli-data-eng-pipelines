{{
        config(
                dagster_auto_materialize_policy={"type":"lazy"}
        )
}}
select
        order_date,
        company,
        count(*) as n_orders,
        sum(order_total) as total_revenue
from {{ ref("orders_augmented") }}
group by 1, 2
