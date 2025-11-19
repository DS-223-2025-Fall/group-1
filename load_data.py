from pathlib import Path
import csv

from db_connect import connect_to_db

# Folder where CSV files are located
DATA_DIR = Path(__file__).parent / "data"


def load_dim_category(conn):
    path = DATA_DIR / "dim_category.csv"
    with conn.cursor() as cur, path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_category (category_id, category_name)
                VALUES (%s, %s)
                ON CONFLICT (category_id) DO NOTHING;
                """,
                (row["category_id"], row["category_name"]),
            )
    conn.commit()
    print("✅ Loaded dim_category")


def load_dim_customer(conn):
    # Our table only contains customer_id (other attributes not used in schema)
    path = DATA_DIR / "dim_customer.csv"
    with conn.cursor() as cur, path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_customer (customer_id)
                VALUES (%s)
                ON CONFLICT (customer_id) DO NOTHING;
                """,
                (row["customer_id"],),
            )
    conn.commit()
    print("✅ Loaded dim_customer (IDs only)")


def load_dim_market(conn):
    # We use market_name as 'region' (schema only has that field)
    path = DATA_DIR / "dim_market.csv"
    with conn.cursor() as cur, path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_market (market_id, region)
                VALUES (%s, %s)
                ON CONFLICT (market_id) DO NOTHING;
                """,
                (row["market_id"], row["market_name"]),
            )
    conn.commit()
    print("✅ Loaded dim_market")


def load_dim_restaurant(conn):
    # We only load id + name (schema does not include other fields)
    path = DATA_DIR / "dim_restaurant.csv"
    with conn.cursor() as cur, path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_restaurant (restaurant_id, restaurant_name)
                VALUES (%s, %s)
                ON CONFLICT (restaurant_id) DO NOTHING;
                """,
                (row["restaurant_id"], row["name"]),
            )
    conn.commit()
    print("✅ Loaded dim_restaurant")


def load_dim_season(conn):
    path = DATA_DIR / "dim_season.csv"
    with conn.cursor() as cur, path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_season (season)
                VALUES (%s)
                ON CONFLICT (season) DO NOTHING;
                """,
                (row["season"],),
            )
    conn.commit()
    print("✅ Loaded dim_season")


def load_dim_time(conn):
    path = DATA_DIR / "dim_time.csv"
    with conn.cursor() as cur, path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_time (date, year, month, day, season)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (date) DO NOTHING;
                """,
                (
                    row["date"],
                    row["year"],
                    row["month"],
                    row["day"],
                    row["season"],
                ),
            )
    conn.commit()
    print("✅ Loaded dim_time")


def load_dim_menu_item(conn):
    path = DATA_DIR / "dim_menu_item.csv"
    with conn.cursor() as cur, path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_menu_item (product_id, product_name, price, restaurant_id, category_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO NOTHING;
                """,
                (
                    row["product_id"],
                    row["product_name"],
                    row["base_price"],
                    row["restaurant_id"],
                    row["category_id"],
                ),
            )
    conn.commit()
    print("✅ Loaded dim_menu_item")


def load_fact_market_prices(conn):
    path = DATA_DIR / "fact_market_prices.csv"
    with conn.cursor() as cur, path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO fact_market_prices (price_id, market_id, date, price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (price_id) DO NOTHING;
                """,
                (
                    row["price_id"],
                    row["market_id"],
                    row["date"],
                    row["usdprice"],  # Using normalized USD price
                ),
            )
    conn.commit()
    print("✅ Loaded fact_market_prices")


def load_fact_sales(conn):
    path = DATA_DIR / "fact_sales.csv"
    with conn.cursor() as cur, path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO fact_sales (sale_id, product_id, restaurant_id, customer_id, date, units_sold, amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sale_id) DO NOTHING;
                """,
                (
                    row["sale_id"],
                    row["product_id"],
                    row["restaurant_id"],
                    row["customer_id"],
                    row["date"],
                    row["units_sold"],
                    row["revenue"],  # amount = revenue
                ),
            )
    conn.commit()
    print("✅ Loaded fact_sales")


def main():
    conn = connect_to_db()
    if not conn:
        print("❌ Could not connect to database. Make sure Docker is running.")
        return

    try:
        # Load in foreign-key-safe order
        load_dim_category(conn)
        load_dim_restaurant(conn)
        load_dim_customer(conn)
        load_dim_season(conn)
        load_dim_time(conn)
        load_dim_market(conn)
        load_dim_menu_item(conn)

        load_fact_market_prices(conn)
        load_fact_sales(conn)
    finally:
        conn.close()
        print("🔚 Connection closed.")


if __name__ == "__main__":
    main()
