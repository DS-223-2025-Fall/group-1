import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()  #

def get_connection():
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
