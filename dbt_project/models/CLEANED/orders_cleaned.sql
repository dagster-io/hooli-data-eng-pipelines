{{config(tags="all_cleaned_models")}}
select
        user_id,
        quantity,
        purchase_price,
        purchase_price * quantity as total_price,
        sku,
        dt,
        cast(dt as datetime) as order_date,
        quantity * purchase_price as order_total
from {{ source("raw_data", "orders") }}
{% if is_incremental() %}
WHERE dt >= '{{ var('min_date') }}' AND dt <= '{{ var('max_date') }}'
{% endif %}