select
    date::date as date,
    country_code,
    subdivision_code,
    holiday_name
from {{ ref('public_holidays') }}
