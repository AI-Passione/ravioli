WITH posts AS (
    SELECT * FROM {{ ref('stg_substack__posts') }}
)

SELECT
    post_id,
    post_at,
    is_published,
    email_sent_at,
    inbox_sent_at,
    post_type,
    post_audience,
    title,
    subtitle,
    podcast_url
FROM posts
