select
        o.*,
        u.company
from
        {{ ref("orders_cleaned") }} o left join
        {{ ref("users_cleaned") }} u on (o.user_id = u.user_id)
{% if is_incremental() %}
WHERE o.order_date = '{{ var('datetime_to_process') }}'
{% endif %}