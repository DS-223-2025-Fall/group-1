# etl/Dockerfile
FROM python:3.10-slim-bullseye

# Install system dependencies for psycopg2 & numerical libs
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /etl

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only code (CSV files will be mounted as a volume)
COPY . .

# Ensure local imports (db_connect, database package) work
ENV PYTHONPATH="/etl"

# Run your ETL loader
CMD ["python", "database/load_data.py"]
