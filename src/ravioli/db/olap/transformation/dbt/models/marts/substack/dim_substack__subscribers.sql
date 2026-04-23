WITH subscribers AS (
    SELECT * FROM {{ ref('stg_substack__emails') }}
)

SELECT
    email,
    is_active_subscription,
    expiry_at,
    subscription_plan,
    is_email_disabled,
    created_at,
    first_payment_at
FROM subscribers
