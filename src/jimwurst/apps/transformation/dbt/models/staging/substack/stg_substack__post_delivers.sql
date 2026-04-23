WITH source AS (
    SELECT * FROM {{ source('substack', 'post_delivers') }}
),

renamed AS (
    SELECT
        post_id,
        {{ dbt.safe_cast("timestamp", api.Column.translate_type("timestamp")) }} AS delivered_at,
        email,
        post_type,
        post_audience,
        active_subscription::boolean AS is_active_subscription,
        _source_folder
    FROM source
)

SELECT * FROM renamed
