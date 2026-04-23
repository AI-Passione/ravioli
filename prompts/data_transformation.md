# Data Transformation in ravioli

## Overview

This document outlines the best practices for structuring and building dbt projects, tailored for the ravioli data warehouse. ravioli is a monolithic data warehouse repository implementing an ELT (Extract, Load, Transform) pipeline designed to run 100% locally. It emphasizes tool-agnostic design with tooling abstracted into folder structure, prioritizing open-source solutions.

The architecture includes:
- **Extract & Load**: Data ingestion from various sources (manual scripts or Airbyte).
- **Transform**: dbt Core for data modeling.
- **Activate**: Metabase/Lightdash for reporting, Jupyter for analysis, Ollama for AI.

Key schemas:
- `staging`: Raw data landing.
- `intermediate`: Transformation intermediates.
- `marts`: Consumer-ready modeled data.
- `s_<source>`: Source-specific ODS (e.g., `s_spotify`).

## Why Structure Matters

Structure in dbt projects is crucial for collaborative analytics engineering. It establishes consistent patterns for file organization, naming conventions, and materializations to optimize collaboration and maintainability. A well-structured project moves data from source-conformed (shaped by external systems) to business-conformed (shaped by organizational needs).

Key principles:
- Establish a cohesive arc from source to business-conformed data.
- Use modular, reusable transformations.
- Prioritize single sources of truth.
- Document deviations from conventions.

## Learning Goals

- Understand up-to-date recommendations for dbt project structure.
- Illustrate recommendations with examples.
- Explain reasoning behind approaches to enable customization.

## Guide Structure

This guide covers:
1. **Staging**: Creating atomic building blocks from source data.
2. **Intermediate**: Purpose-built transformation steps.
3. **Marts**: Business-defined entities.
4. **Project Organization**: YAML configuration, other folders, and project splitting.

## dbt Project Structure Guide

### Why Does Structure Matter?

Analytics engineering is about enabling collaborative decision-making at scale. Consistent structure reduces decision fatigue by establishing patterns for file organization, naming, and materializations. It helps teams focus on unique problems rather than reinventing conventions.

In ravioli, structure ensures the ELT pipeline flows smoothly from source-conformed data (e.g., raw JSON/CSV from local files) to business-conformed models in the `marts` schema.

Key goals:
- Move data from narrow, source-shaped models to wider, business-shaped entities.
- Enable modular, reusable transformations.
- Maintain a single source of truth across schemas: `staging`, `intermediate`, `marts`, `s_<source>`.

### Learning Goals

- Master recommendations for dbt project structure in ravioli.
- See examples adapted to local ELT pipeline.
- Understand reasoning to customize for your needs.

### Guide Structure Overview

We'll cover the transformation layers in DAG order:
1. **Staging**: Atoms from source data.
2. **Intermediate**: Molecules with specific purposes.
3. **Marts**: Cells representing business entities.
4. **Project Organization**: YAML, folders, and splitting.

Example project structure for ravioli:
```
models/
├── staging/
│   ├── spotify/
│   │   ├── _spotify__models.yml
│   │   ├── _spotify__sources.yml
│   │   └── stg_spotify__tracks.sql
│   └── apple_health/
│       ├── _apple_health__models.yml
│       ├── _apple_health__sources.yml
│       └── stg_apple_health__workouts.sql
├── intermediate/
│   └── finance/
│       ├── _int_finance__models.yml
│       └── int_payments_aggregated.sql
├── marts/
│   ├── finance/
│   │   ├── _finance__models.yml
│   │   ├── orders.sql
│   │   └── payments.sql
│   └── marketing/
│       ├── _marketing__models.yml
│       └── customers.sql
└── utilities/
    └── all_dates.sql
```

This structure reflects data flow from sources to business entities, using schemas for separation.

### Philosophy

- Tools-agnostic: Logic separated from tools via folder structure.
- Open-source first.
- 100% local runnable.
- Casual attitude, serious architecture ("Es ist mir wurst" - excellence in DWH design).

## Staging Models

### Overview

The staging layer is the foundation of ravioli's ELT pipeline. It transforms raw, source-conformed data from local files (e.g., JSON/CSV in `~/Documents/ravioli_local_data/<source>/`) into clean, modular building blocks. These "atoms" are used throughout the project for downstream transformations.

In ravioli, staging models load data into the `staging` schema and source-specific `s_<source>` schemas.

### Files and Folders

#### Structure
- **Subdirectories by source system**: Group by data source (e.g., `spotify/`, `apple_health/`) for similar loading methods.
- **Avoid subdirectories by business grouping**: Prevents conflicting definitions; keep staging source-focused.
- **File naming**: `stg_[source]__[entity]s.sql` (e.g., `stg_spotify__tracks.sql`). Use double underscores to distinguish source and entity.

#### Example
```
models/staging/
├── spotify/
│   ├── _spotify__models.yml
│   ├── _spotify__sources.yml
│   ├── base/  # For joins if needed
│   │   └── base_spotify__tracks.sql
│   └── stg_spotify__tracks.sql
└── apple_health/
    ├── _apple_health__models.yml
    ├── _apple_health__sources.yml
    └── stg_apple_health__workouts.sql
```

### Models

#### Pattern
Each staging model follows a consistent CTE structure:
1. `source`: Pull from source using `{{ source('source_name', 'table_name') }}`.
2. `renamed`: Apply transformations (renaming, type casting, basic computations, categorization).

#### Transformations
- ✅ Renaming (e.g., `id as track_id`).
- ✅ Type casting (e.g., cents to dollars).
- ✅ Basic computations (e.g., `amount / 100.0`).
- ✅ Categorization (e.g., case statements for payment types).
- ❌ Joins (use base models if needed).
- ❌ Aggregations (preserve grain for downstream use).

#### Materialization
- ✅ Views: Ensures fresh data for downstream models; avoids storage waste.
- Config in `dbt_project.yml`: `staging: +materialized: view`

#### Example Model
```sql
-- stg_spotify__tracks.sql
with source as (
    select * from {{ source('spotify', 'tracks') }}
),
renamed as (
    select
        id as track_id,
        name as track_name,
        duration_ms / 1000.0 as duration_seconds,
        case
            when popularity > 80 then 'high'
            else 'low'
        end as popularity_category
    from source
)
select * from renamed
```

### Other Considerations

#### Base Models for Joins
Use when joins are necessary (e.g., unioning symmetrical sources or handling deletes).
- Example: Union multiple Shopify stores into a base model, then stage.

#### Codegen
Automate staging with [dbt-codegen](https://github.com/dbt-labs/dbt-codegen) for rote patterns.

#### Utilities Folder
For general models like date spines, not in staging.

#### Development Flow
Start with staging all needed sources before building intermediate/marts. Use selectors like `dbt build --select staging.spotify+`.

This layer ensures DRY transformations and clean atoms for the rest of ravioli.

## Intermediate Models

### Overview

The intermediate layer builds on staging "atoms" to create "molecules" — modular components with specific purposes. It prepares staging models for joining into the entities needed in marts.

In ravioli, intermediate models transform data towards business-conformed concepts, using the `intermediate` schema.

### Files and Folders

#### Structure
- **Subdirectories by business groupings**: Group by concern (e.g., `finance/`, `marketing/`) rather than source.
- **File naming**: `int_[entity]s_[verb]s.sql` (e.g., `int_payments_pivoted_to_orders.sql`). Use verbs to describe transformations.
- **Avoid over-optimization**: Don't split early; add subdirs only when needed (e.g., >10 marts).

#### Example
```
models/intermediate/
└── finance/
    ├── _int_finance__models.yml
    └── int_payments_pivoted_to_orders.sql
```

### Models

#### Purposes
- **Structural simplification**: Join 4-6 concepts to simplify mart logic.
- **Re-graining**: Fan out/in models (e.g., explode orders by quantity).
- **Isolating complex operations**: Move tricky logic for easier testing/debugging.

#### Materialization
- ✅ Ephemeral: Simplifies development; interpolates into referencing models.
- ✅ Views in custom schema: For troubleshooting without building into production.

#### Example Model
```sql
-- int_payments_pivoted_to_orders.sql
{% set payment_methods = ['bank_transfer', 'credit_card', 'coupon', 'gift_card'] %}
with payments as (
    select * from {{ ref('stg_stripe__payments') }}
),
pivot_and_aggregate_payments_to_order_grain as (
    select
        order_id,
        {% for payment_method in payment_methods -%}
        sum(case when payment_method = '{{ payment_method }}' and status = 'success' then amount else 0 end) as {{ payment_method }}_amount,
        {% endfor -%}
        sum(case when status = 'success' then amount end) as total_amount
    from payments
    group by 1
)
select * from pivot_and_aggregate_payments_to_order_grain
```

#### Best Practices
- **Not exposed to end users**: Keep in intermediate schema with permissions.
- **DRY and readable**: Use Jinja for repetition; descriptive CTE names.
- **Narrow DAG**: Multiple inputs OK; avoid multiple outputs.
- **Warehouse tidiness**: Materialize thoughtfully to avoid clutter.

This layer modularizes complexity, enabling cleaner marts in ravioli.

## Mart Models

### Overview

The marts layer represents the final business-defined entities in ravioli. These are wide, denormalized tables containing all useful data about a concept at its grain (e.g., orders, customers). They are designed for end-user consumption in BI tools like Metabase.

In ravioli, marts populate the `marts` schema with consumer-ready data.

### Files and Folders

#### Structure
- **Subdirectories by department/business area**: Group by concern (e.g., `finance/`, `marketing/`).
- **File naming**: By entity (e.g., `customers.sql`, `orders.sql`). Avoid time dimensions here (use metrics for rollups).
- **Avoid duplicate concepts**: Don't create `finance_orders` and `marketing_orders`; use single sources of truth.

#### Example
```
models/marts/
├── finance/
│   ├── _finance__models.yml
│   ├── orders.sql
│   └── payments.sql
└── marketing/
    ├── _marketing__models.yml
    └── customers.sql
```

### Models

#### Characteristics
- **Entity-grained**: All data about a concept (e.g., orders include customer/payment details).
- **Wide and denormalized**: Cheap storage, expensive compute; pack in relevant data.
- **Materialized as tables/incrementals**: Build data for performance; start with views, move to tables/incrementals as needed.

#### Best Practices
- **Avoid too many joins**: If >4-5 concepts, use intermediate models.
- **Build on marts thoughtfully**: OK for efficiency, but watch for circular dependencies.
- **Troubleshoot via tables**: Temporarily materialize chains for debugging.

#### Example Models
```sql
-- orders.sql
with orders as (
    select * from {{ ref('stg_jaffle_shop__orders') }}
),
order_payments as (
    select * from {{ ref('int_payments_pivoted_to_orders') }}
),
orders_and_order_payments_joined as (
    select
        orders.order_id,
        orders.customer_id,
        orders.order_date,
        coalesce(order_payments.total_amount, 0) as amount,
        coalesce(order_payments.gift_card_amount, 0) as gift_card_amount
    from orders
    left join order_payments on orders.order_id = order_payments.order_id
)
select * from orders_and_order_payments_joined
```

```sql
-- customers.sql
with customers as (
    select * from {{ ref('stg_jaffle_shop__customers') }}
),
orders as (
    select * from {{ ref('orders') }}  -- Building on mart
),
customer_orders as (
    select
        customer_id,
        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date,
        count(order_id) as number_of_orders,
        sum(amount) as lifetime_value
    from orders
    group by 1
),
customers_and_customer_orders_joined as (
    select
        customers.customer_id,
        customers.first_name,
        customers.last_name,
        customer_orders.first_order_date,
        customer_orders.most_recent_order_date,
        coalesce(customer_orders.number_of_orders, 0) as number_of_orders,
        customer_orders.lifetime_value
    from customers
    left join customer_orders on customers.customer_id = customer_orders.customer_id
)
select * from customers_and_customer_orders_joined
```

### dbt Semantic Layer Considerations

Without Semantic Layer: Denormalize heavily.
With Semantic Layer: Normalize more for MetricFlow flexibility.

In ravioli, focus on denormalized marts for BI consumption.

This layer delivers the "cells" powering ravioli's data products.

## Project Organization

### Overview

Beyond the `models/` folder, ravioli uses other dbt folders for specific purposes. This ensures clean separation of concerns in the ELT pipeline.

### YAML Configuration

#### Structure
- **Config per folder**: `_ [directory]__models.yml` and `_ [directory]__sources.yml` per directory.
- **Cascade configs**: Set defaults in `dbt_project.yml`, override per model.
- **Avoid monolith**: Don't put all YAML in one file.

#### Example dbt_project.yml
```yaml
models:
  ravioli:
    staging:
      +materialized: view
      +schema: staging
    intermediate:
      +materialized: ephemeral
      +schema: intermediate
    marts:
      +materialized: table
      +schema: marts
      finance:
        +schema: finance
      marketing:
        +schema: marketing
```

**Note**: The `+schema` configurations will create schemas prefixed with the target schema from your `profiles.yml`. To avoid `public_` prefixes, set `schema: ""` (empty string) in your dbt profile target. If `schema` is required, you may need to adjust your profile configuration or accept the prefixed schemas.

#### Groups
Define access controls:
```yaml
groups:
  - name: finance
    owner:
      email: finance@ravioli.com
```

### Other Folders

#### Seeds
- **For lookup tables**: Static data not in sources (e.g., zip codes).
- **Not for source data**: Use ELT tools for loading.
- **Naming**: If a seed represents a final dimension for consumption, name it `dim_<name>.csv` (e.g., `dim_public_holidays.csv`).
- **Schema Hygiene**: Always map seeds to their appropriate schema (`staging` or `marts`) in `dbt_project.yml`. Never leave seeds in the default `public` schema.

#### Analyses
- **For auditing queries**: Version-control checks with `dbt-audit-helper`.

#### Tests
- **For multi-table tests**: Integration tests across models.

#### Snapshots
- **For SCD Type 2**: Handle slowly changing dimensions.

#### Macros
- **For DRY transformations**: Document in `_macros.yml`.

### Project Splitting

#### When to Split
- **Business groups**: Use dbt Mesh for departmental ownership.
- **Data governance**: Separate sensitive data.
- **Size**: >1000 models.

#### ravioli Approach
As a monolithic repo, keep together unless governance requires splitting. Use Mesh for collaboration.

### Final Considerations

Consistency trumps perfection. Document deviations. This guide evolves with dbt and ravioli's needs.

For ravioli's local, open-source focus, prioritize simplicity and reusability.

## Additional Resources

- [dbt Best Practices](https://docs.getdbt.com/best-practices)
- [How we structure our dbt projects](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)
- [Staging Models](https://docs.getdbt.com/best-practices/how-we-structure/2-staging)
- [Intermediate Models](https://docs.getdbt.com/best-practices/how-we-structure/3-intermediate)
- [Mart Models](https://docs.getdbt.com/best-practices/how-we-structure/4-marts)
- [Project Organization](https://docs.getdbt.com/best-practices/how-we-structure/5-the-rest-of-the-project)