WITH source AS (
    SELECT * FROM {{ source('substack', 'posts') }}
),

renamed AS (
    SELECT
        split_part(post_id, '.', 1) AS post_id,
        CASE WHEN post_date = '' THEN NULL ELSE post_date END::timestamp AS post_at,
        is_published::boolean AS is_published,
        CASE WHEN email_sent_at = '' THEN NULL ELSE email_sent_at END::timestamp AS email_sent_at,
        CASE WHEN inbox_sent_at = '' THEN NULL ELSE inbox_sent_at END::timestamp AS inbox_sent_at,
        type AS post_type,
        audience AS post_audience,
        title,
        subtitle,
        podcast_url,
        _source_folder
    FROM source
),

deduplicated AS (
    -- Handle duplicates across multiple exports by taking the latest one (or just one)
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY post_id ORDER BY post_at DESC NULLS LAST) as row_num
    FROM renamed
)

SELECT 
    *
FROM deduplicated
WHERE row_num = 1
