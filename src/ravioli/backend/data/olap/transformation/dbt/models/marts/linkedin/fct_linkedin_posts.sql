{{ config(
    enabled=var('enable_linkedin_models', false),
    tags=['marts', 'linkedin', 'posts']
) }}

with source as (
    select * from {{ ref('stg_linkedin__basic_content_top_posts') }}
),
with_raw as (
    select
        to_jsonb(s) as raw
    from source s
),
extracted as (
    select
        raw,

        nullif(
            coalesce(
                raw->>'post_url',
                raw->>'post_url_1',
                raw->>'post_link',
                raw->>'post_link_1',
                raw->>'permalink',
                raw->>'post_permalink',
                raw->>'share_link',
                raw->>'url',
                raw->>'link'
            ),
            ''
        ) as extracted_post_url,

        nullif(
            coalesce(
                raw->>'posted_at',
                raw->>'posted_at_1',
                raw->>'posted_on',
                raw->>'posted_on_1',
                raw->>'post_date',
                raw->>'post_date_1',
                raw->>'post_datetime',
                raw->>'post_datetime_1',
                raw->>'date',
                raw->>'date_1',
                raw->>'created_at',
                raw->>'created_at_1',
                raw->>'published_at',
                raw->>'published_at_1',
                raw->>'published_on',
                raw->>'published_on_1',
                raw->>'post_publish_date',
                raw->>'post_publish_date_1',
                raw->>'time',
                raw->>'time_1'
            ),
            ''
        ) as extracted_posted_at_text
    from with_raw
),
standardized as (
    select
        md5(coalesce(extracted_post_url, '') || '|' || coalesce(extracted_posted_at_text, '')) as linked_post_key,
        extracted_post_url as post_url,

        case
            when extracted_posted_at_text is null then null::timestamp
            when extracted_posted_at_text ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}($|[ T][0-9]{2}:[0-9]{2})' then cast(extracted_posted_at_text as timestamp)
            when extracted_posted_at_text ~ '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}' then to_timestamp(extracted_posted_at_text, 'MM/DD/YYYY')::timestamp
            else null::timestamp
        end as posted_at,

        cast(
            case
                when extracted_posted_at_text is null then null::timestamp
                when extracted_posted_at_text ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}($|[ T][0-9]{2}:[0-9]{2})' then cast(extracted_posted_at_text as timestamp)
                when extracted_posted_at_text ~ '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}' then to_timestamp(extracted_posted_at_text, 'MM/DD/YYYY')::timestamp
                else null::timestamp
            end as date
        ) as posted_date,

        raw
    from extracted
)

select *
from standardized
where post_url is not null
  and posted_at is not null
