{{ config(
    tags=['marts', 'growth', 'content']
) }}

with linkedin_daily as (
    select
        posted_date::date as activity_date,
        count(*) as linkedin_posts_published
    from {{ ref('fct_linkedin_posts') }}
    group by 1
),

substack_daily as (
    select
        (post_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/Berlin')::date as activity_date,
        count(*) as substack_posts_published
    from {{ ref('dim_substack__posts') }}
    where is_published = true
    group by 1
),

final as (
    select
        coalesce(l.activity_date, s.activity_date)::date as date_berlin,
        coalesce(l.linkedin_posts_published, 0) as linkedin_posts_published,
        coalesce(s.substack_posts_published, 0) as substack_posts_published
    from linkedin_daily l
    full outer join substack_daily s on l.activity_date = s.activity_date
),

daily_holidays as (
    select
        date,
        max(case when country_code = 'US' then 1 else 0 end) = 1 as is_public_holiday_us,
        max(case when country_code = 'DE' then 1 else 0 end) = 1 as is_public_holiday_de,
        max(case when country_code = 'FR' then 1 else 0 end) = 1 as is_public_holiday_fr
    from {{ ref('dim_public_holidays') }}
    group by 1
)

select
    f.date_berlin,
    extract(dow from f.date_berlin) as day_of_week,
    extract(day from f.date_berlin) as day_of_month,
    extract(month from f.date_berlin) as month,
    extract(year from f.date_berlin) as year,
    (extract(dow from f.date_berlin) in (0, 6)) as is_weekend,
    coalesce(h.is_public_holiday_us, false) as is_public_holiday_us,
    coalesce(h.is_public_holiday_de, false) as is_public_holiday_de,
    coalesce(h.is_public_holiday_fr, false) as is_public_holiday_fr,
    f.linkedin_posts_published,
    f.substack_posts_published
from final f
left join daily_holidays h on f.date_berlin = h.date
order by f.date_berlin desc
