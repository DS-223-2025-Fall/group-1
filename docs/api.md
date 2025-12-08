# FastAPI Service

The backend lives in `yerevan_pricing/api` and exposes REST plus ML endpoints that align with the PM specs for `/predict-price` and `/forecast-price`.

## Directory Highlights

- `main.py` – FastAPI application with routers, Pydantic models, and CatBoost inference hooks.
- `API_SPEC.md` – product-facing contract that mirrors the documented endpoints.
- `data/` – CSV snapshots delivered by ETL for rapid local bootstrapping (dim tables).
- `model/` – serialized CatBoost `.cbm` plus legacy Random Forest artifact.
- `database/` – SQL helpers for connecting to Postgres when running outside mock mode.
- `requirements.txt` – FastAPI + ML dependency list.

## Key Endpoints

| Endpoint | Method | Summary |
| --- | --- | --- |
| `/health` | GET | Reports service status and DB connectivity. |
| `/restaurants` | GET/POST/PUT/DELETE | CRUD for restaurant metadata. |
| `/menu-items` | GET/POST/PUT/DELETE | CRUD for menu items tied to restaurants. |
| `/customers` | GET | Read-only view over anonymized customer segments. |
| `/predict-price` | POST | CatBoost-powered optimal price recommendation. |
| `/forecast-price` | POST | Short-horizon forecast for a menu item. |
| `/analytics/historical` | GET | Aggregated historical pricing metrics. |

The in-memory bootstrap performed in `main.py` uses the CSV files from `data/`. When switching to a live database, flip the feature flag or environment variable once a connection layer is implemented.

## Running Locally

```bash
cd yerevan_pricing/api
uvicorn main:app --reload --port 8000
```

Set `CATBOOST_MODEL_PATH` and `DATA_DIR` through environment variables if you relocate the artifacts. For Docker-based workflows use the compose file at `yerevan_pricing/docker-compose.yml`, which mounts ETL outputs and keeps services on the same network.

## Testing Ideas

- Exercise CRUD endpoints with the sample payloads embedded inside each Pydantic model `ConfigDict`.
- Hit `/predict-price` using requests from the Streamlit UI (`yerevan_pricing/app/app.py`) to validate integration.
- Add automated tests under `yerevan_pricing/api/tests` (folder to be created) using `pytest` and `httpx`.
