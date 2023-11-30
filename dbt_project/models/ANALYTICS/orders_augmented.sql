select
        o.*,
        u.company,
        l.state,
        l_zip_code
from {{ ref("orders_cleaned") }} o 

left join {{ ref("users_cleaned") }} u
       on o.user_id = u.user_id

 left join {{ ref("location_cleaned") }} l
        on o.user_id = l.user_id

{% if is_incremental() %}
WHERE o.order_date >= '{{ var('min_date') }}' AND o.order_date <= '{{ var('max_date') }}'
{% endif %}