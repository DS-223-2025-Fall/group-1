from pathlib import Path
import csv
from db_connect import get_connection

"""
Helper routines that bulk-load the local Postgres database from the CSV
snapshots in ``etl/database/data``. Each loader is intentionally idempotent so
developers can reseed their environment safely.
"""

DATA_DIR = Path(__file__).parent / "data"

def to_bool(x: str):
    """
    Translate CSV truthy strings into ``True``/``False`` booleans.

    Args:
        x (str): Raw value from the CSV reader.

    Returns:
        bool | None: ``None`` if the cell is empty, otherwise a boolean.
    """
    if x is None:
        return None
    s = str(x).strip().lower()
    return s in ("1", "true", "yes", "y")


def load_dim_category(conn):
    """
    Load the category dimension from ``dim_category.csv``.

    Args:
        conn: psycopg2 connection used to execute INSERT statements.
    """
    path = DATA_DIR / "dim_category.csv"
    with conn.cursor() as cur, path.open(encoding="utf-8") as f:
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
    print("✅ dim_category loaded")


def load_dim_season(conn):
    """
    Load season metadata from ``dim_season.csv`` into ``dim_season``.

    Args:
        conn: psycopg2 connection.
    """
    path = DATA_DIR / "dim_season.csv"
    with conn.cursor() as cur, path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_season (season, months)
                VALUES (%s, %s)
                ON CONFLICT (season) DO NOTHING;
                """,
                (row["season"], row["months"]),
            )
    conn.commit()
    print("✅ dim_season loaded")


def load_dim_time(conn):
    """
    Populate ``dim_time`` from ``dim_time.csv`` with day-level metadata.

    Args:
        conn: psycopg2 connection.
    """
    path = DATA_DIR / "dim_time.csv"
    with conn.cursor() as cur, path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_time (date, year, month, day, day_of_week, season)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO NOTHING;
                """,
                (
                    row["date"],
                    row["year"],
                    row["month"],
                    row["day"],
                    row["day_of_week"],
                    row["season"],
                ),
            )
    conn.commit()
    print("✅ dim_time loaded")


def load_dim_market(conn):
    """
    Load ``dim_market`` with administrative and geo metadata.

    Args:
        conn: psycopg2 connection.
    """
    path = DATA_DIR / "dim_market.csv"
    with conn.cursor() as cur, path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_market (market_id, admin1, admin2, market_name, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (market_id) DO NOTHING;
                """,
                (
                    row["market_id"],
                    row["admin1"],
                    row["admin2"],
                    row["market_name"],
                    row["latitude"],
                    row["longitude"],
                ),
            )
    conn.commit()
    print("✅ dim_market loaded")


def load_dim_restaurant(conn):
    """
    Load restaurant properties from ``dim_restaurant.csv``.

    Args:
        conn: psycopg2 connection.
    """
    path = DATA_DIR / "dim_restaurant.csv"
    with conn.cursor() as cur, path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_restaurant
                    (restaurant_id, name, location, type, avg_customer_count, rating, owner_contact)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (restaurant_id) DO NOTHING;
                """,
                (
                    row["restaurant_id"],
                    row["name"],
                    row["location"],
                    row["type"],
                    row["avg_customer_count"],
                    row["rating"],
                    row["owner_contact"],
                ),
            )
    conn.commit()
    print("✅ dim_restaurant loaded")


def load_dim_customer(conn):
    """
    Load ``dim_customer`` from ``dim_customer.csv``.

    Args:
        conn: psycopg2 connection.
    """
    path = DATA_DIR / "dim_customer.csv"
    with conn.cursor() as cur, path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_customer
                    (customer_id, gender, age_group, avg_spending, visit_frequency)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO NOTHING;
                """,
                (
                    row["customer_id"],
                    row["gender"],
                    row["age_group"],
                    row["avg_spending"],
                    row["visit_frequency"],
                ),
            )
    conn.commit()
    print("✅ dim_customer loaded")


def load_dim_menu_item(conn):
    """
    Load ``dim_menu_item`` by parsing ``dim_menu_item.csv`` records.

    Args:
        conn: psycopg2 connection.
    """
    path = DATA_DIR / "dim_menu_item.csv"
    with conn.cursor() as cur, path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO dim_menu_item
                    (product_id, restaurant_id, product_name, category_id,
                     base_price, cost, portion_size, available)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id) DO NOTHING;
                """,
                (
                    row["product_id"],
                    row["restaurant_id"],
                    row["product_name"],
                    row["category_id"],
                    row["base_price"],
                    row["cost"],
                    row["portion_size"],
                    to_bool(row["available"]),
                ),
            )
    conn.commit()
    print("✅ dim_menu_item loaded")


def load_fact_market_prices(conn):
    """
    Load ``fact_market_prices`` from ``fact_market_prices.csv``.

    Args:
        conn: psycopg2 connection.
    """
    path = DATA_DIR / "fact_market_prices.csv"
    with conn.cursor() as cur, path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO fact_market_prices
                    (price_id, date, market_id, category, commodity, unit,
                     priceflag, pricetype, currency, price, usdprice)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (price_id) DO NOTHING;
                """,
                (
                    row["price_id"],
                    row["date"],
                    row["market_id"],
                    row["category"],
                    row["commodity"],
                    row["unit"],
                    row["priceflag"],
                    row["pricetype"],
                    row["currency"],
                    row["price"],
                    row["usdprice"],
                ),
            )
    conn.commit()
    print("✅ fact_market_prices loaded")


def load_fact_sales(conn):
    """
    Load ``fact_sales`` from ``fact_sales.csv`` for downstream analytics.

    Args:
        conn: psycopg2 connection.
    """
    path = DATA_DIR / "fact_sales.csv"  # make sure the file has these columns
    with conn.cursor() as cur, path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO fact_sales
                    (sale_id, product_id, restaurant_id, customer_id,
                     date, units_sold, price_sold, revenue)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sale_id) DO NOTHING;
                """,
                (
                    row["sale_id"],
                    row["product_id"],
                    row["restaurant_id"],
                    row["customer_id"],
                    row["date"],
                    row["units_sold"],
                    row["price_sold"],
                    row["revenue"],
                ),
            )
    conn.commit()
    print("✅ fact_sales loaded")


def main():
    """
    CLI entry point to populate every dimension and fact table.

    Opens a single connection and sequentially executes all loaders so a local
    developer can run ``python load_data.py`` and get a ready-to-use schema.
    """
    conn = get_connection()
    try:
        load_dim_category(conn)
        load_dim_season(conn)
        load_dim_time(conn)
        load_dim_market(conn)
        load_dim_restaurant(conn)
        load_dim_customer(conn)
        load_dim_menu_item(conn)
        load_fact_market_prices(conn)
        load_fact_sales(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
