select
        user_id,
        created_at,
        company
from {{ source("RAW_DATA", "users") }}
where not is_test_user