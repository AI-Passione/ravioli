{{ config(materialized='view', enabled=var('enable_linkedin_models', false), tags=['staging', 'linkedin']) }}

with source as (
    select * from {{ source('linkedin', 'complete_connections') }}
),
renamed as (
    select
        -- Current export only contains a single column "notes:"; preserve it and add placeholders.
        null::text as connection_name,
        null::text as company,
        null::text as position,
        null::text as email_address,
        null::date as connected_on,
        "notes:" as notes_raw
    from source
)

select * from renamed
