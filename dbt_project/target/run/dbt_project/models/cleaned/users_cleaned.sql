
  
    

        create or replace transient table DEMO_DB2.analytics.users_cleaned  as
        (select
        user_id,
        company
from DEMO_DB2.raw_data.users
where not is_test_user
        );
      
  