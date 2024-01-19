select
        user_id,
        created_at,
        company
from {{ source("RAW_DATA", "users") }}