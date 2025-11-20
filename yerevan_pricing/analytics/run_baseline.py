import time
import sys
from utils.db_connect import get_connection
from baseline_models import run_models


def wait_for_data(min_rows=1, timeout=60, interval=5):
    """Wait until `fact_sales` has at least `min_rows` rows or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        conn = get_connection()
        if conn:
            try:
                import pandas as pd
                cnt = pd.read_sql("SELECT count(*) as c FROM fact_sales;", conn).iloc[0, 0]
                conn.close()
                if cnt >= min_rows:
                    print(f"Found {cnt} rows in fact_sales, continuing...")
                    return True
                else:
                    print(f"fact_sales rows={cnt}; waiting for >= {min_rows}...")
            except Exception as e:
                print("Error checking fact_sales:", e)
        else:
            print("No DB connection yet; retrying...")
        time.sleep(interval)
    return False


if __name__ == "__main__":
    # Wait for ETL to populate data (helpful when services start concurrently)
    ok = wait_for_data(min_rows=1, timeout=120, interval=5)
    if not ok:
        print("Timeout waiting for data; exiting without running models.")
        sys.exit(1)
    run_models()
