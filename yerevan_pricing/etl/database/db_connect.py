import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()  #

def get_connection():
    """
    Create a psycopg2 connection using the environment-driven credentials.

    The helper automatically falls back to sensible defaults so the same code
    works inside Docker (service hostname) and on a developer laptop. All
    callers must close the returned connection object once they are done with
    it to avoid leaking DB sessions.

    Returns:
        psycopg2.extensions.connection | None: Live connection when successful,
        otherwise ``None`` after logging the failure.
    """
    try:
        # If running inside Docker, use service name; otherwise localhost
        host = os.getenv("DB_HOST", "localhost")

        conn = psycopg2.connect(
            host=host,                # postgres (inside Docker) / localhost (local)
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME") if os.getenv("DB_NAME") not in (None, "", "admin") else "pricing_db",

            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "admin123"),
        )

        print(f"✔ Connected to PostgreSQL at host={host}")
        return conn

    except Exception as error:
        print("❌ Database connection failed:", error)
        return None


if __name__ == "__main__":
    conn = get_connection()
    if conn:
        conn.close()
        print("Connection closed.")
