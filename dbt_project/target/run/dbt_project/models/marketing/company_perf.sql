
  
    

        create or replace transient table DEMO_DB2.analytics.company_perf  as
        (select
        company,
        sum(n_orders) as n_orders,
        sum(total_revenue) as total_revenue
from DEMO_DB2.analytics.company_stats
group by 1
        );
      
  