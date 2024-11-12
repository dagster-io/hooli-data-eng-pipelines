with source as (
    
select *
from {{ source("raw_data", "locations") }}

),

source_renamed as (

    select l_user_id as user_id,
           l_street_address as street_address,
           l_state as state,
           l_country as country,
           l_zip_code as zip_code,
           _sling_loaded_at
    from source

)

select *
from source_renamed