select
        o.*,
        u.company
from
        DEMO_DB2.analytics.orders_cleaned o left join
        DEMO_DB2.analytics.users_cleaned u on (o.user_id = u.user_id)