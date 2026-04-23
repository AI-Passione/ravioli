WITH delivers AS (
    SELECT
        post_id,
        delivered_at AS event_at,
        email,
        post_type,
        post_audience,
        is_active_subscription,
        'delivery' AS event_type,
        NULL AS country,
        NULL AS city,
        NULL AS region,
        NULL AS device_type,
        NULL AS client_os,
        NULL AS client_type,
        NULL AS user_agent,
        _source_folder
    FROM {{ ref('stg_substack__post_delivers') }}
),

opens AS (
    SELECT
        post_id,
        opened_at AS event_at,
        email,
        post_type,
        post_audience,
        is_active_subscription,
        'open' AS event_type,
        country,
        city,
        region,
        device_type,
        client_os,
        client_type,
        user_agent,
        _source_folder
    FROM {{ ref('stg_substack__post_opens') }}
),

unified AS (
    SELECT * FROM delivers
    UNION ALL
    SELECT * FROM opens
),

deduplicated AS (
    -- Deduplicate overlapping events across different export folders
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY post_id, email, event_at, event_type 
            ORDER BY _source_folder DESC -- Heuristic: take newest export folder
        ) as row_num
    FROM unified
),

final AS (
    SELECT
        md5(
            coalesce(d.post_id, '') || '|' || 
            coalesce(d.email, '') || '|' || 
            coalesce(d.event_at::text, '') || '|' || 
            coalesce(d.event_type, '')
        ) AS event_key,
        d.post_id,
        d.event_at,
        d.email,
        d.post_type,
        d.post_audience,
        d.is_active_subscription,
        d.event_type,
        d.country,
        d.city,
        d.region,
        d.device_type,
        d.client_os,
        d.client_type,
        d.user_agent,
        d._source_folder,
        p.title AS post_title,
        p.subtitle AS post_subtitle,
        p.post_at AS post_published_at
    FROM deduplicated d
    LEFT JOIN {{ ref('dim_substack__posts') }} p ON d.post_id = p.post_id
    WHERE d.row_num = 1
)

SELECT * FROM final
