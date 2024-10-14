select
        user_id,
        created_at,
        company
from DEMO_DB2_BRANCH.raw_data.users
where not is_test_user