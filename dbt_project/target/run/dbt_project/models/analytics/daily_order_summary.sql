
  
    

        create or replace transient table DEMO_DB2.analytics.daily_order_summary  as
        (select
        date as order_date,
        n_orders as num_orders
from DEMO_DB2.analytics.order_stats
-- this doesn't really do anything
        );
      
  