FROM python:3.12-slim


WORKDIR /analytics

COPY requirements.txt /analytics/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /analytics/

ENV PYTHONPATH="/analytics:/analytics/utils"

CMD ["python", "run_baseline.py"]
