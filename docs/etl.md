# ETL Service

The ETL stack inside `yerevan_pricing/etl` prepares operational data for the prediction API and analytical models. This folder is Docker-ready and mirrors the database schema finalized in Milestone 3.

## Layout

- `Dockerfile` – spins up the ETL worker with the dependencies from `requirements.txt`.
- `requirements.txt` – minimal Python stack (Pandas, SQL drivers) required for ingest scripts.
- `database/` – contains SQL DDL, seeds, and CSV dumps that replicate the production schema.
- `init/` – bootstrap scripts executed when the ETL container starts (loads seeds into Postgres).

## Running Locally

```bash
cd yerevan_pricing/etl
docker build -t group1-etl .
docker run --rm --network=host group1-etl
```

The container expects a Postgres database accessible through the environment variables defined in `yerevan_pricing/api/main.py`. When running alongside the API and app, rely on `yerevan_pricing/docker-compose.yml` from the repo root.

## Pipeline Responsibilities

1. Pull latest restaurant, menu, and customer datasets from the shared data source.
2. Apply cleaning rules consistent with the analytics notebooks (`yerevan_pricing/analytics`).
3. Load dimensional tables (`dim_restaurant`, `dim_menu_item`, `dim_customer`, `dim_category`) plus fact tables into the Postgres instance.
4. Export CSV snapshots to `yerevan_pricing/api/data/` so the FastAPI service can bootstrap in-memory stores during development.

## Next Additions

- Document the SQL scripts in `database/` once schema freezes.
- Add a diagram explaining relationships between ETL outputs and the CatBoost model artifacts.
- Include a cron or Airflow example for production scheduling.
