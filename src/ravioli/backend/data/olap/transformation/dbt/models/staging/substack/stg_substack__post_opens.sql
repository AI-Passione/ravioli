WITH source AS (
    SELECT * FROM {{ source('substack', 'post_opens') }}
),

renamed AS (
    SELECT
        post_id,
        {{ dbt.safe_cast("timestamp", api.Column.translate_type("timestamp")) }} AS opened_at,
        email,
        post_type,
        post_audience,
        active_subscription::boolean AS is_active_subscription,
        country,
        city,
        region,
        device_type,
        client_os,
        client_type,
        user_agent,
        _source_folder
    FROM source
)

SELECT * FROM renamed
