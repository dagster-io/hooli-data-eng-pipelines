
select
        o.*,
        u.company,
        l.state,
        l.zip_code
from DEMO_DB2_BRANCH.analytics.orders_cleaned o 

left join DEMO_DB2_BRANCH.analytics.users_cleaned u
       on o.user_id = u.user_id

 left join DEMO_DB2_BRANCH.analytics.locations_cleaned l
        on o.user_id = l.user_id

