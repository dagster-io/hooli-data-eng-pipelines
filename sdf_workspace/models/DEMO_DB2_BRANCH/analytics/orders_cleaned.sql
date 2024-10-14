
select
        user_id,
        quantity,
        purchase_price,
        sku,
        dt,
        cast(dt as datetime) as order_date,
        quantity * purchase_price as order_total
from DEMO_DB2_BRANCH.raw_data.orders
