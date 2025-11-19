import psycopg2

def connect_to_db():
    try:
        # Connection details match your docker-compose.yml
        connection = psycopg2.connect(
            host="localhost",
            port="5432",
            database="pricing_db",
            user="admin",
            password="admin123"
        )

        print("✔ Successfully connected to PostgreSQL database!")
        return connection

    except Exception as error:
        print("❌ Error while connecting to PostgreSQL:", error)
        return None


if __name__ == "__main__":
    conn = connect_to_db()

    if conn:
        conn.close()
        print("Connection closed.")
