## Start services and run ETL

Quick instructions to bring up the project services and run the ETL loader.

- Start the Docker stack (Postgres, API, ETL, analytics, app, etc):

```bash
# from project root
docker compose up -d
```

- The Postgres container runs initialization SQL from `./etl/init/init.sql` on first start.

- The `etl` service runs the loader automatically (it executes `database/load_data.py` on container start).

- To run the ETL locally (outside Docker) against the running Postgres on the host use:

```bash
# ensure Postgres is reachable on localhost:5432
DB_HOST=localhost python etl/database/load_data.py
```

- To view ETL logs from Docker:

```bash
docker compose logs -f etl
```

If you changed environment values, edit the `.env` file in the project root and restart the stack.
