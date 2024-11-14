select
        user_id,
        created_at,
        company
from {{ source("raw_data", "users") }}
where not is_test_user