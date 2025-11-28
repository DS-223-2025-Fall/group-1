from db_connect import get_connection


# -----------------------------
# Basic DB Helper Functions
# -----------------------------

def execute_query(query, params=None, fetch=False):
    """
    Run a SQL statement against the pricing warehouse using a fresh connection.

    Args:
        query (str): Parameterized SQL string (``%s`` placeholders).
        params (tuple | None): Optional values that will be bound to the query.
        fetch (bool): When ``True`` the rows returned by the statement are
            collected and returned to the caller.

    Returns:
        list[tuple] | bool | None: Query results when ``fetch`` is enabled,
        ``True`` if the statement executed and committed successfully, or
        ``None`` when execution fails (error is logged to stdout).
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
    """
    Retrieve the canonical list of restaurants.

    Returns:
        list[tuple] | None: Rows of ``(restaurant_id, restaurant_name)`` or
        ``None`` if the underlying query fails.
    """
    query = """
        SELECT restaurant_id, restaurant_name
        FROM dim_restaurant
        ORDER BY restaurant_id;
    """
    return execute_query(query, fetch=True)


def get_products_for_restaurant(restaurant_id):
    """
    Fetch the menu catalog for a given restaurant.

    Args:
        restaurant_id (int): Identifier from ``dim_restaurant``.

    Returns:
        list[tuple] | None: Tuples of ``(product_id, product_name, price,
        category_id)`` when the query succeeds.
    """
    query = """
        SELECT product_id, product_name, price, category_id
        FROM dim_menu_item
        WHERE restaurant_id = %s;
    """
    return execute_query(query, params=(restaurant_id,), fetch=True)


def get_daily_sales(date):
    """
    Pull aggregated sales numbers for a specific day.

    Args:
        date (datetime.date | str): Calendar date recognized by Postgres.

    Returns:
        list[tuple] | None: Each tuple contains ``(product_id, units_sold,
        amount)`` for the requested day.
    """
    query = """
        SELECT product_id, units_sold, amount
        FROM fact_sales
        WHERE date = %s;
    """
    return execute_query(query, params=(date,), fetch=True)


def get_market_prices(date):
    """
    Access the external market price feed for benchmarking.

    Args:
        date (datetime.date | str): Calendar date recognized by Postgres.

    Returns:
        list[tuple] | None: Tuples of ``(market_id, price)`` for the provided
        date, or ``None`` if the query fails.
    """
    query = """
        SELECT market_id, price
        FROM fact_market_prices
        WHERE date = %s;
    """
    return execute_query(query, params=(date,), fetch=True)
