{{ config(materialized='view', enabled=var('enable_linkedin_models', false), tags=['staging', 'linkedin', 'basic_content']) }}

select * from {{ source('linkedin', 'basic_content_2025_12_17_2025_12_23_jimmypang_followers') }}
