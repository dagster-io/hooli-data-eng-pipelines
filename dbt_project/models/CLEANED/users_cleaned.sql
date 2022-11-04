select
        user_id,
        company
from {{ source("RAW_DATA", "users") }}
where not is_test_user