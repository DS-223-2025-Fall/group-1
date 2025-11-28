Database utilities
==================

This package contains the thin wrappers that our ETL, analytics notebooks, and
API services use to talk to the local Postgres instance provisioned through
`docker-compose`. Everything is intentionally lightweight so that new database
developers can reason about the data model without digging through multiple
layers of abstraction.


Connection settings
-------------------

`db_connect.get_connection` centralises the logic for opening a psycopg2
connection. The helper inspects the following environment variables and falls
back to sensible defaults when values are not provided:

| Variable      | Default      | Notes                                   |
| ------------- | ------------ | --------------------------------------- |
| `DB_HOST`     | `localhost`  | Use `pricing-db` when running in Docker |
| `DB_PORT`     | `5432`       |                                         |
| `DB_NAME`     | `pricing_db` | Skips empty / `admin` values            |
| `DB_USER`     | `admin`      |                                         |
| `DB_PASSWORD` | `admin123`   |                                         |

Every call site is responsible for closing the connection it receives.


Query helpers
-------------

`db_utils.execute_query` is the shared helper that handles connection creation,
execution, error handling, and optional row fetching. The module also exposes
several focused readers that power downstream services:

| Function                          | Purpose                                             |
| --------------------------------- | --------------------------------------------------- |
| `get_all_restaurants()`          | Ordered list of restaurant identifiers and names    |
| `get_products_for_restaurant(id)`| Menu catalog for a specific restaurant              |
| `get_daily_sales(date)`          | Product-level sales metrics for a calendar date     |
| `get_market_prices(date)`        | Market benchmarking prices for the supplied date    |

Each helper returns `None` when execution fails, so callers can decide whether
to retry or surface a user-facing error.


CSV loaders
-----------

`load_data.py` contains the idempotent routines that hydrate every dimension
and fact table from the curated CSV snapshots in `etl/database/data`. They are
safe to rerun because each statement uses `ON CONFLICT DO NOTHING`.

| Function                  | Target table         | Source file                  |
| ------------------------- | -------------------- | ---------------------------- |
| `load_dim_category`       | `dim_category`       | `dim_category.csv`           |
| `load_dim_season`         | `dim_season`         | `dim_season.csv`             |
| `load_dim_time`           | `dim_time`           | `dim_time.csv`               |
| `load_dim_market`         | `dim_market`         | `dim_market.csv`             |
| `load_dim_restaurant`     | `dim_restaurant`     | `dim_restaurant.csv`         |
| `load_dim_customer`       | `dim_customer`       | `dim_customer.csv`           |
| `load_dim_menu_item`      | `dim_menu_item`      | `dim_menu_item.csv`          |
| `load_fact_market_prices` | `fact_market_prices` | `fact_market_prices.csv`     |
| `load_fact_sales`         | `fact_sales`         | `fact_sales.csv`             |


Developer workflow
------------------

1. Ensure the Postgres container is running (`docker-compose up db`).
2. Export the connection overrides if needed (see table above).
3. Seed the schema locally:

   ```
   cd yerevan_pricing/etl/database
   python load_data.py
   ```

4. Use the helpers in `db_utils.py` within notebooks or services to query data.


Troubleshooting
---------------

- If a loader fails on malformed CSV rows, update the fixture file or preprocess
  the data before rerunning the script.
- When psycopg2 cannot connect, double-check that Docker is running and the
  credentials match the values defined in `docker-compose.yml`.
