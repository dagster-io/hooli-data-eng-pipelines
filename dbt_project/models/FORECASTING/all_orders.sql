select order_date, num_orders from {{ source("FORECASTING", "predicted_orders") }}