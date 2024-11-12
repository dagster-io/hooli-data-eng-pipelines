{{config(tags="my_test_tag")}}
select
        user_id,
        quantity,
        purchase_price,
        purchase_price as purchase_price_2,
        sku,
        dt,
        cast(dt as datetime) as order_date,
        quantity * purchase_price as order_total
from {{ source("raw_data", "orders") }}
{% if is_incremental() %}
WHERE dt >= '{{ var('min_date') }}' AND dt <= '{{ var('max_date') }}'
{% endif %}