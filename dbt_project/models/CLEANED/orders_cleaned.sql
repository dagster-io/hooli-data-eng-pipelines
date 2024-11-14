{{config(tags="my_test_tag")}}
select
        user_id,
        quantity,
        purchase_price,
        sku,
        dt,
        cast(dt as datetime) as order_date,
        date_trunc('month', order_date) as order_month,
        quantity * purchase_price as order_total
from {{ source("raw_data", "orders") }}
{% if is_incremental() %}
WHERE dt >= '{{ var('min_date') }}' AND dt <= '{{ var('max_date') }}'
{% endif %}