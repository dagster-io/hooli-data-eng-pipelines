
  
    

        create or replace transient table DEMO_DB2.analytics.all_orders  as
        (select order_date, num_orders from DEMO_DB2.forecasting.predicted_orders
        );
      
  