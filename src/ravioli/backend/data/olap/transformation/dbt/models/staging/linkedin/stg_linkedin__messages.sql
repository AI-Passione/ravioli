{{ config(materialized='view', enabled=var('enable_linkedin_models', false), tags=['staging', 'linkedin']) }}

with source as (
    select * from {{ source('linkedin', 'complete_messages') }}
),
renamed as (
    select
        conversation_title as conversation_name,
        "from" as sender,
        sender_profile_url,
        "to" as recipient,
        recipient_profile_urls,
        content as body,
        cast("date" as timestamp) as sent_at,
        subject,
        folder,
        attachments
    from source
)

select * from renamed
