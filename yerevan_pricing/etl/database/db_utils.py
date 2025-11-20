from db_connect import get_connection


# -----------------------------
# Basic DB Helper Functions
# -----------------------------

def execute_query(query, params=None, fetch=False):
    """
    Execute any SQL query using a single helper function.
    - query: SQL string
    - params: optional tuple for parameterized queries
    - fetch: if True → returns fetched rows
    """

    conn = get_connection()
    if not conn:
        print("❌ Database connection failed.")
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)

            if fetch:
                result = cur.fetchall()
                return result

            conn.commit()
            return True

    except Exception as e:
        print(f"❌ Error executing query: {e}")
        return None

    finally:
        conn.close()


# -----------------------------
# High-level helper functions
# -----------------------------

def get_all_restaurants():
    query = """
        SELECT restaurant_id, restaurant_name
        FROM dim_restaurant
        ORDER BY restaurant_id;
    """
    return execute_query(query, fetch=True)


def get_products_for_restaurant(restaurant_id):
    query = """
        SELECT product_id, product_name, price, category_id
        FROM dim_menu_item
        WHERE restaurant_id = %s;
    """
    return execute_query(query, params=(restaurant_id,), fetch=True)


def get_daily_sales(date):
    query = """
        SELECT product_id, units_sold, amount
        FROM fact_sales
        WHERE date = %s;
    """
    return execute_query(query, params=(date,), fetch=True)


def get_market_prices(date):
    query = """
        SELECT market_id, price
        FROM fact_market_prices
        WHERE date = %s;
    """
    return execute_query(query, params=(date,), fetch=True)
