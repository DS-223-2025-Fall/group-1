"""
Database utility functions for the API.

This module provides database access functions for the FastAPI backend,
using the same connection pattern as the ETL service.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add parent directory to path to import db_connect
sys.path.insert(0, str(Path(__file__).parent.parent / "etl" / "database"))

try:
    from db_connect import get_connection
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    # Fallback if db_connect not available
    get_connection = None


def execute_query(query: str, params: Optional[tuple] = None, fetch: bool = True) -> Optional[List[Dict[str, Any]]]:
    """
    Execute a SQL query and return results as list of dictionaries.
    
    Args:
        query: SQL query string with %s placeholders
        params: Optional tuple of parameters
        fetch: Whether to fetch results
        
    Returns:
        List of dictionaries (one per row) or None if error
    """
    if get_connection is None:
        return None
        
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                rows = cur.fetchall()
                return [dict(row) for row in rows]
            conn.commit()
            return []
    except Exception as e:
        print(f"❌ Database query error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_restaurants(
    location: Optional[str] = None,
    venue_type: Optional[str] = None,
    min_rating: Optional[float] = None
) -> List[Dict[str, Any]]:
    """Get restaurants with optional filters."""
    query = """
        SELECT 
            restaurant_id,
            name,
            location,
            type as venue_type,
            avg_customer_count,
            rating,
            owner_contact
        FROM dim_restaurant
        WHERE 1=1
    """
    params = []
    
    if location:
        query += " AND location = %s"
        params.append(location)
    if venue_type:
        query += " AND type = %s"
        params.append(venue_type)
    if min_rating is not None:
        query += " AND rating >= %s"
        params.append(min_rating)
    
    query += " ORDER BY restaurant_id"
    
    result = execute_query(query, tuple(params) if params else None)
    return result or []


def get_restaurant_by_id(restaurant_id: int) -> Optional[Dict[str, Any]]:
    """Get a single restaurant by ID."""
    query = """
        SELECT 
            restaurant_id,
            name,
            location,
            type as venue_type,
            avg_customer_count,
            rating,
            owner_contact
        FROM dim_restaurant
        WHERE restaurant_id = %s
    """
    result = execute_query(query, (restaurant_id,))
    return result[0] if result else None


def get_menu_items(
    restaurant_id: Optional[int] = None,
    category_id: Optional[int] = None,
    available: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> List[Dict[str, Any]]:
    """Get menu items with optional filters."""
    query = """
        SELECT 
            product_id,
            restaurant_id,
            product_name,
            category_id,
            base_price,
            cost,
            portion_size,
            available
        FROM dim_menu_item
        WHERE 1=1
    """
    params = []
    
    if restaurant_id:
        query += " AND restaurant_id = %s"
        params.append(restaurant_id)
    if category_id:
        query += " AND category_id = %s"
        params.append(category_id)
    if available is not None:
        query += " AND available = %s"
        params.append(available)
    if min_price is not None:
        query += " AND base_price >= %s"
        params.append(min_price)
    if max_price is not None:
        query += " AND base_price <= %s"
        params.append(max_price)
    
    query += " ORDER BY product_id"
    
    result = execute_query(query, tuple(params) if params else None)
    return result or []


def get_menu_item_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """Get a single menu item by ID."""
    query = """
        SELECT 
            product_id,
            restaurant_id,
            product_name,
            category_id,
            base_price,
            cost,
            portion_size,
            available
        FROM dim_menu_item
        WHERE product_id = %s
    """
    result = execute_query(query, (product_id,))
    return result[0] if result else None


def get_customers(
    age_group: Optional[str] = None,
    gender: Optional[str] = None,
    min_spending: Optional[float] = None
) -> List[Dict[str, Any]]:
    """Get customers with optional filters."""
    query = """
        SELECT 
            customer_id,
            gender,
            age_group,
            avg_spending,
            visit_frequency
        FROM dim_customer
        WHERE 1=1
    """
    params = []
    
    if age_group:
        query += " AND age_group = %s"
        params.append(age_group)
    if gender:
        query += " AND gender = %s"
        params.append(gender)
    if min_spending is not None:
        query += " AND avg_spending >= %s"
        params.append(min_spending)
    
    query += " ORDER BY customer_id LIMIT 500"
    
    result = execute_query(query, tuple(params) if params else None)
    return result or []


def get_categories() -> List[Dict[str, Any]]:
    """Get all categories."""
    query = """
        SELECT 
            category_id,
            category_name
        FROM dim_category
        ORDER BY category_id
    """
    result = execute_query(query)
    return result or []


def create_restaurant(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new restaurant."""
    query = """
        INSERT INTO dim_restaurant (name, location, type, avg_customer_count, rating, owner_contact)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING restaurant_id, name, location, type as venue_type, avg_customer_count, rating, owner_contact
    """
    params = (
        data["name"],
        data["location"],
        data["venue_type"],
        data["avg_customer_count"],
        data["rating"],
        data["owner_contact"]
    )
    result = execute_query(query, params)
    return result[0] if result else None


def save_prediction_snapshot(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Persist a predicted price snapshot for a Streamlit session.

    Args:
        data: Dictionary with session and feature columns.

    Returns:
        Inserted row dictionary or None on failure.
    """
    query = """
        INSERT INTO prediction_snapshots (
            session_id,
            product_name,
            location,
            venue_type,
            portion_size,
            age_group,
            predicted_price,
            confidence_low,
            confidence_high
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING snapshot_id, session_id, product_name, location, venue_type,
                  portion_size, age_group, predicted_price, confidence_low,
                  confidence_high, created_at
    """
    params = (
        data["session_id"],
        data["product_name"],
        data["location"],
        data["venue_type"],
        data["portion_size"],
        data["age_group"],
        data["predicted_price"],
        data["confidence_low"],
        data["confidence_high"],
    )
    result = execute_query(query, params)
    return result[0] if result else None


def get_prediction_snapshots(session_id: str) -> List[Dict[str, Any]]:
    """
    Fetch all prediction snapshots for a given session.

    Args:
        session_id: Streamlit session identifier.

    Returns:
        List of snapshot dictionaries.
    """
    query = """
        SELECT
            snapshot_id,
            session_id,
            product_name,
            location,
            venue_type,
            portion_size,
            age_group,
            predicted_price,
            confidence_low,
            confidence_high,
            created_at
        FROM prediction_snapshots
        WHERE session_id = %s
        ORDER BY created_at ASC
    """
    result = execute_query(query, (session_id,))
    return result or []


def delete_prediction_snapshots(session_id: str) -> None:
    """
    Remove all snapshots for the provided session.

    Args:
        session_id: Streamlit session identifier.
    """
    query = "DELETE FROM prediction_snapshots WHERE session_id = %s"
    execute_query(query, (session_id,), fetch=False)


def ensure_prediction_snapshot_table() -> bool:
    """
    Ensure the prediction_snapshots table exists (idempotent).

    Returns:
        True if the DDL ran successfully, False otherwise.
    """
    if get_connection is None:
        return False

    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_snapshots (
                    snapshot_id      SERIAL PRIMARY KEY,
                    session_id       UUID NOT NULL,
                    product_name     VARCHAR(255),
                    location         VARCHAR(255),
                    venue_type       VARCHAR(100),
                    portion_size     VARCHAR(50),
                    age_group        VARCHAR(50),
                    predicted_price  NUMERIC(10,2),
                    confidence_low   NUMERIC(10,2),
                    confidence_high  NUMERIC(10,2),
                    created_at       TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_prediction_snapshots_session
                ON prediction_snapshots (session_id);
                """
            )
        conn.commit()
        return True
    except Exception as exc:
        print(f"❌ Failed to ensure prediction_snapshots table: {exc}")
        conn.rollback()
        return False
    finally:
        conn.close()


def update_restaurant(restaurant_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing restaurant."""
    query = """
        UPDATE dim_restaurant
        SET name = %s, location = %s, type = %s, avg_customer_count = %s, rating = %s, owner_contact = %s
        WHERE restaurant_id = %s
        RETURNING restaurant_id, name, location, type as venue_type, avg_customer_count, rating, owner_contact
    """
    params = (
        data["name"],
        data["location"],
        data["venue_type"],
        data["avg_customer_count"],
        data["rating"],
        data["owner_contact"],
        restaurant_id
    )
    result = execute_query(query, params)
    return result[0] if result else None


def delete_restaurant(restaurant_id: int) -> bool:
    """Delete a restaurant."""
    query = "DELETE FROM dim_restaurant WHERE restaurant_id = %s"
    result = execute_query(query, (restaurant_id,), fetch=False)
    return result is not None


def create_menu_item(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new menu item."""
    query = """
        INSERT INTO dim_menu_item (restaurant_id, product_name, category_id, base_price, cost, portion_size, available)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING product_id, restaurant_id, product_name, category_id, base_price, cost, portion_size, available
    """
    params = (
        data["restaurant_id"],
        data["product_name"],
        data["category_id"],
        data["base_price"],
        data["cost"],
        data["portion_size"],
        data["available"]
    )
    result = execute_query(query, params)
    return result[0] if result else None


def update_menu_item(product_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing menu item."""
    query = """
        UPDATE dim_menu_item
        SET restaurant_id = %s, product_name = %s, category_id = %s, base_price = %s, cost = %s, portion_size = %s, available = %s
        WHERE product_id = %s
        RETURNING product_id, restaurant_id, product_name, category_id, base_price, cost, portion_size, available
    """
    params = (
        data["restaurant_id"],
        data["product_name"],
        data["category_id"],
        data["base_price"],
        data["cost"],
        data["portion_size"],
        data["available"],
        product_id
    )
    result = execute_query(query, params)
    return result[0] if result else None


def delete_menu_item(product_id: int) -> bool:
    """Delete a menu item."""
    query = "DELETE FROM dim_menu_item WHERE product_id = %s"
    result = execute_query(query, (product_id,), fetch=False)
    return result is not None


def test_connection() -> bool:
    """Test database connection."""
    if get_connection is None:
        return False
    conn = get_connection()
    if conn:
        conn.close()
        return True
    return False
