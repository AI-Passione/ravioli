WITH source AS (
    SELECT * FROM {{ source('substack', 'emails') }}
),

renamed AS (
    SELECT
        email,
        active_subscription::boolean AS is_active_subscription,
        CASE WHEN expiry = '' THEN NULL ELSE expiry END::timestamp AS expiry_at,
        plan AS subscription_plan,
        email_disabled::boolean AS is_email_disabled,
        CASE WHEN created_at = '' THEN NULL ELSE created_at END::timestamp AS created_at,
        CASE WHEN first_payment_at = '' THEN NULL ELSE first_payment_at END::timestamp AS first_payment_at,
        _source_folder
    FROM source
),

deduplicated AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at DESC NULLS LAST) as row_num
    FROM renamed
)

SELECT 
    *
FROM deduplicated
WHERE row_num = 1
