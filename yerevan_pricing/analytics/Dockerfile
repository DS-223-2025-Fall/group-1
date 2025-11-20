FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /analytics

COPY requirements.txt /analytics/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /analytics/

ENV PYTHONPATH="/analytics:/analytics/utils"

CMD ["python", "run_baseline.py"]
