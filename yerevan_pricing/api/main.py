"""
Yerevan Dynamic Pricing API - Milestone 3

This FastAPI service provides endpoints for:
- Restaurant management (CRUD operations)
- Menu item management (CRUD operations)
- Customer data access (read-only)
- Price prediction using ML model
- Price forecasting

Author: Backend Team (NarekN7)
Version: 1.0.0
"""

from __future__ import annotations

import os
import pickle
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.responses import RedirectResponse

# Import all schemas and enums from schema.py
from schema import (
    LocationEnum,
    VenueTypeEnum,
    AgeGroupEnum,
    PortionSizeEnum,
    RestaurantCreate,
    RestaurantUpdate,
    MenuItemCreate,
    MenuItemUpdate,
    PricePredictionRequest,
    Restaurant,
    MenuItem,
    Customer,
    PricePredictionResponse,
    ForecastResponse,
    HealthResponse,
    CategoryResponse,
    PriceDistributionResponse,
    PriceDistributionItem,
    PredictionSnapshotResponse,
    MarketComparisonResponse,
    MarketComparisonItem,
    CategoryAnalyticsResponse,
    CategoryAnalyticsItem,
    RevenueAnalyticsResponse,
    RevenueAnalyticsItem,
    TimeSeriesResponse,
    TimeSeriesDataPoint,
)

# ==============================================================================
# Configuration
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"  # Mounted from etl/database/data
CATBOOST_MODEL_PATH = BASE_DIR / "model" / "catboost_model.cbm"  # CatBoost model (preferred)
RF_MODEL_PATH = BASE_DIR / "model" / "random_forest_model.pkl"  # Kept for reference, not used

# Database connection settings (from environment or defaults)
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pricing_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")

# ==============================================================================
# Logging Configuration
# ==============================================================================

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==============================================================================
# Data Loading and ML Model
# ==============================================================================

# Try to import database utilities
try:
    from db_utils import (
        get_restaurants as db_get_restaurants,
        get_restaurant_by_id as db_get_restaurant_by_id,
        get_menu_items as db_get_menu_items,
        get_menu_item_by_id as db_get_menu_item_by_id,
        get_customers as db_get_customers,
        get_categories as db_get_categories,
        create_restaurant as db_create_restaurant,
        update_restaurant as db_update_restaurant,
        delete_restaurant as db_delete_restaurant,
        create_menu_item as db_create_menu_item,
        update_menu_item as db_update_menu_item,
        delete_menu_item as db_delete_menu_item,
        ensure_prediction_snapshot_table as db_ensure_prediction_snapshot_table,
        save_prediction_snapshot as db_save_prediction_snapshot,
        get_prediction_snapshots as db_get_prediction_snapshots,
        delete_prediction_snapshots as db_delete_prediction_snapshots,
        test_connection as db_test_connection,
    )
    DB_AVAILABLE = True
    logger.info("Database utilities imported successfully")
except ImportError as e:
    logger.warning(f"Database utilities not available, using CSV fallback: {e}")
    DB_AVAILABLE = False
    db_get_restaurants = None
    db_get_restaurant_by_id = None
    db_get_menu_items = None
    db_get_menu_item_by_id = None
    db_get_customers = None
    db_get_categories = None
    db_create_restaurant = None
    db_update_restaurant = None
    db_delete_restaurant = None
    db_create_menu_item = None
    db_update_menu_item = None
    db_delete_menu_item = None
    db_ensure_prediction_snapshot_table = None
    db_save_prediction_snapshot = None
    db_get_prediction_snapshots = None
    db_delete_prediction_snapshots = None
    db_test_connection = None


def _load_csv(filename: str) -> List[dict]:
    """
    Load data from a CSV file in the data directory (fallback when DB unavailable).
    
    Args:
        filename: Name of the CSV file to load
        
    Returns:
        List of dictionaries representing CSV rows
    """
    path = DATA_DIR / filename
    if not path.exists():
        return []
    import csv
    with path.open(encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader)


def _bootstrap_restaurants() -> List[dict]:
    """Load restaurant data from CSV into memory store."""
    rows = _load_csv("dim_restaurant.csv")
    restaurants = []
    for row in rows:
        restaurants.append({
                "restaurant_id": int(row["restaurant_id"]),
                "name": row["name"],
                "location": row["location"],
                "venue_type": row["type"],
                "avg_customer_count": int(row["avg_customer_count"]),
                "rating": float(row["rating"]),
                "owner_contact": row["owner_contact"],
        })
    return restaurants


def _bootstrap_menu_items() -> List[dict]:
    """Load menu item data from CSV into memory store."""
    rows = _load_csv("dim_menu_item.csv")
    items = []
    for row in rows:
        items.append({
                "product_id": int(row["product_id"]),
                "restaurant_id": int(row["restaurant_id"]),
                "product_name": row["product_name"],
                "category_id": int(row["category_id"]),
                "base_price": float(row["base_price"]),
                "cost": float(row["cost"]),
                "portion_size": row["portion_size"],
                "available": row["available"].lower() == "true",
        })
    return items


def _bootstrap_customers() -> List[dict]:
    """Load customer data from CSV into memory store."""
    rows = _load_csv("dim_customer.csv")
    customers = []
    for row in rows[:500]:  # Limit for performance
        customers.append({
                "customer_id": int(row["customer_id"]),
                "gender": row["gender"],
                "age_group": row["age_group"],
                "avg_spending": float(row["avg_spending"]),
                "visit_frequency": int(row["visit_frequency"]),
        })
    return customers


def _bootstrap_categories() -> List[dict]:
    """Load category data from CSV into memory store."""
    rows = _load_csv("dim_category.csv")
    categories = []
    for row in rows:
        categories.append({
            "category_id": int(row["category_id"]),
            "category_name": row["category_name"],
        })
    return categories


# Initialize data stores (will be populated from database or CSV)
restaurants_store = []
menu_items_store = []
customers_store = []
categories_store = []
prediction_snapshots_store = []

# Try to load from database first, fallback to CSV
if DB_AVAILABLE and db_test_connection():
    logger.info("Loading data from database...")
    try:
        if db_ensure_prediction_snapshot_table:
            if db_ensure_prediction_snapshot_table():
                logger.info("prediction_snapshots table available")
            else:
                logger.warning("prediction_snapshots table check failed; using in-memory fallback if insert fails")
        restaurants_store = db_get_restaurants() or []
        menu_items_store = db_get_menu_items() or []
        customers_store = db_get_customers() or []
        categories_store = db_get_categories() or []
        logger.info(f"Loaded {len(restaurants_store)} restaurants, {len(menu_items_store)} menu items from database")
        
        # If database is empty, fallback to CSV
        if len(restaurants_store) == 0 or len(menu_items_store) == 0:
            logger.warning("Database appears empty, falling back to CSV data")
            restaurants_store = _bootstrap_restaurants()
            menu_items_store = _bootstrap_menu_items()
            customers_store = _bootstrap_customers()
            categories_store = _bootstrap_categories()
            logger.info(f"Loaded {len(restaurants_store)} restaurants, {len(menu_items_store)} menu items from CSV")
    except Exception as e:
        logger.warning(f"Failed to load from database, using CSV fallback: {e}")
        restaurants_store = _bootstrap_restaurants()
        menu_items_store = _bootstrap_menu_items()
        customers_store = _bootstrap_customers()
        categories_store = _bootstrap_categories()
else:
    logger.info("Using CSV data (database not available)")
    restaurants_store = _bootstrap_restaurants()
    menu_items_store = _bootstrap_menu_items()
    customers_store = _bootstrap_customers()
    categories_store = _bootstrap_categories()

# Load ML model (lazy loading)
_ml_model = None


def get_ml_model():
    """
    Load and cache the CatBoost model for price prediction.
    
    Uses only CatBoost model - no fallback to Random Forest.
    
    Returns:
        CatBoostRegressor model instance
        
    Raises:
        HTTPException: If CatBoost model is not available or fails to load
    """
    global _ml_model
    if _ml_model is None:
        import logging
        logger = logging.getLogger(__name__)
        
        # Load CatBoost model only
        logger.info(f"Loading CatBoost model from: {CATBOOST_MODEL_PATH}")
        
        if not CATBOOST_MODEL_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail=f"CatBoost model file not found at: {CATBOOST_MODEL_PATH}"
            )
        
        # Check if file is a Git LFS pointer (too small to be a real model)
        file_size = CATBOOST_MODEL_PATH.stat().st_size
        if file_size < 10000:  # Real CatBoost models are much larger
            logger.error(f"Model file appears to be a Git LFS pointer (size: {file_size} bytes). Need to pull actual file.")
            raise HTTPException(
                status_code=503,
                detail=f"Model file is a Git LFS pointer. Please run: git lfs pull (or ensure model file is properly downloaded)"
            )
        
        try:
            from catboost import CatBoostRegressor
        except ImportError as e:
            raise HTTPException(
                status_code=503,
                detail=f"CatBoost library not installed: {str(e)}"
            )
        
        try:
            model = CatBoostRegressor()
            model.load_model(str(CATBOOST_MODEL_PATH))
            _ml_model = model
            logger.info("CatBoost model loaded successfully!")
            return _ml_model
        except Exception as e:
            logger.error(f"Failed to load CatBoost model: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=503,
                detail=f"Failed to load CatBoost model: {str(e)}. Model file may be corrupted or incomplete."
            )
    
    return _ml_model


# ==============================================================================
# Helper Functions
# ==============================================================================


def _next_id(store: List[dict], key: str) -> int:
    """Generate next available ID for a data store."""
    if not store:
        return 1
    return max(item[key] for item in store) + 1


def _get_record_or_404(store: List[dict], key: str, value: int) -> dict:
    """
    Find a record by ID or raise 404.
    
    Args:
        store: Data store to search
        key: Key field name
        value: Value to find
        
    Returns:
        Found record
        
    Raises:
        HTTPException: If record not found
    """
    for record in store:
        if record[key] == value:
            return record
    raise HTTPException(status_code=404, detail=f"{key}={value} not found")


def _record_prediction_snapshot(session_id: Optional[str], payload: dict) -> Optional[dict]:
    """
    Persist a prediction snapshot either in Postgres or in-memory fallback.

    Args:
        session_id: Streamlit session identifier.
        payload: Snapshot fields excluding identifiers.

    Returns:
        Snapshot dictionary or None when session_id missing.
    """
    if not session_id:
        return None

    snapshot_payload = {
        "session_id": session_id,
        **payload,
    }

    if DB_AVAILABLE and db_save_prediction_snapshot:
        try:
            saved = db_save_prediction_snapshot(snapshot_payload)
            if saved:
                return saved
        except Exception as exc:
            logger.warning(f"Failed to persist prediction snapshot to DB: {exc}")

    snapshot_payload["snapshot_id"] = _next_id(prediction_snapshots_store, "snapshot_id")
    snapshot_payload["created_at"] = datetime.now(timezone.utc)
    prediction_snapshots_store.append(snapshot_payload)
    return snapshot_payload


def _get_prediction_snapshots_for_session(session_id: str) -> List[dict]:
    """
    Retrieve all snapshots for a session from DB or fallback store.
    """
    if not session_id:
        return []

    if DB_AVAILABLE and db_get_prediction_snapshots:
        try:
            records = db_get_prediction_snapshots(session_id)
            if records is not None:
                return records
        except Exception as exc:
            logger.warning(f"Failed to load prediction snapshots from DB: {exc}")

    return [
        snap for snap in prediction_snapshots_store
        if snap.get("session_id") == session_id
    ]


def _clear_prediction_snapshots_for_session(session_id: str) -> None:
    """
    Delete all snapshots for the provided session identifier.
    """
    if not session_id:
        return

    if DB_AVAILABLE and db_delete_prediction_snapshots:
        try:
            db_delete_prediction_snapshots(session_id)
            return
        except Exception as exc:
            logger.warning(f"Failed to delete prediction snapshots from DB: {exc}")

    global prediction_snapshots_store
    prediction_snapshots_store = [
        snap for snap in prediction_snapshots_store
        if snap.get("session_id") != session_id
    ]


# ==============================================================================
# FastAPI Application
# ==============================================================================

app = FastAPI(
    title="Yerevan Dynamic Pricing API",
    description="""
## Dynamic Pricing API for Yerevan Cafés & Restaurants

This API provides endpoints for managing restaurant data, menu items, 
and generating price predictions using machine learning.

### Features
- **Restaurant Management**: Full CRUD operations for restaurant data
- **Menu Items**: Manage menu items with pricing information
- **Price Prediction**: ML-powered optimal price recommendations
- **Analytics**: Forecasting and analytics endpoints

### Authentication
Currently no authentication required (development phase).

### Rate Limits
No rate limits enforced in development.
    """,
    version="1.0.0",
    contact={
        "name": "Backend Team",
        "email": "backend@yerevan-pricing.dev",
    },
    license_info={
        "name": "MIT",
    },
)


# ==============================================================================
# Root Redirect
# ==============================================================================


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root to Swagger documentation."""
    return RedirectResponse(url="/docs")


# ==============================================================================
# Health & Status Endpoints
# ==============================================================================


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns the current health status of the API service."
)
def healthcheck() -> HealthResponse:
    """
    Check API health status.
    
    Returns service status, version, and database connectivity.
    """
    db_status = "disconnected"
    if DB_AVAILABLE and db_test_connection():
        db_status = "connected"
    elif DB_AVAILABLE:
        db_status = "unavailable"
    
    return HealthResponse(
        status="ok",
        version="1.0.0",
        database=db_status
    )


# ==============================================================================
# Restaurant Endpoints
# ==============================================================================


@app.get(
    "/restaurants",
    response_model=List[Restaurant],
    tags=["Restaurants"],
    summary="List all restaurants",
    description="Retrieve a list of all restaurants with optional filtering."
)
def list_restaurants(
    location: Optional[str] = Query(None, description="Filter by location"),
    venue_type: Optional[str] = Query(None, description="Filter by venue type"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter")
) -> List[Restaurant]:
    """
    Get all restaurants with optional filters.
    
    Args:
        location: Filter by district (optional)
        venue_type: Filter by venue type (optional)
        min_rating: Filter by minimum rating (optional)
        
    Returns:
        List of restaurants matching criteria
    """
    # Try database first, fallback to in-memory store
    if DB_AVAILABLE:
        try:
            results = db_get_restaurants(location=location, venue_type=venue_type, min_rating=min_rating)
            if results:
                return results
        except Exception as e:
            logger.warning(f"Database query failed, using in-memory store: {e}")
    
    # Fallback to in-memory store
    results = restaurants_store
    
    if location:
        results = [r for r in results if r["location"].lower() == location.lower()]
    if venue_type:
        results = [r for r in results if r["venue_type"].lower() == venue_type.lower()]
    if min_rating is not None:
        results = [r for r in results if r["rating"] >= min_rating]
    
    return deepcopy(results)


@app.get(
    "/restaurants/{restaurant_id}",
    response_model=Restaurant,
    tags=["Restaurants"],
    summary="Get restaurant by ID",
    description="Retrieve a specific restaurant by its unique identifier."
)
def get_restaurant(restaurant_id: int) -> Restaurant:
    """
    Get a single restaurant by ID.
    
    Args:
        restaurant_id: Unique restaurant identifier
        
    Returns:
        Restaurant data
        
    Raises:
        HTTPException: 404 if restaurant not found
    """
    # Try database first
    if DB_AVAILABLE:
        try:
            record = db_get_restaurant_by_id(restaurant_id)
            if record:
                return record
        except Exception as e:
            logger.warning(f"Database query failed, using in-memory store: {e}")
    
    # Fallback to in-memory store
    record = _get_record_or_404(restaurants_store, "restaurant_id", restaurant_id)
    return deepcopy(record)


@app.post(
    "/restaurants",
    response_model=Restaurant,
    status_code=201,
    tags=["Restaurants"],
    summary="Create new restaurant",
    description="Add a new restaurant to the system."
)
def create_restaurant(payload: RestaurantCreate) -> Restaurant:
    """
    Create a new restaurant.
    
    Args:
        payload: Restaurant data
        
    Returns:
        Created restaurant with assigned ID
    """
    # Try database first
    if DB_AVAILABLE and db_create_restaurant:
        try:
            record = db_create_restaurant(payload.model_dump())
            if record:
                # Update in-memory store for consistency
                restaurants_store.append(record)
                return record
        except Exception as e:
            logger.warning(f"Database insert failed, using in-memory store: {e}")
    
    # Fallback to in-memory store
    new_record = payload.model_dump()
    new_record["restaurant_id"] = _next_id(restaurants_store, "restaurant_id")
    restaurants_store.append(new_record)
    return deepcopy(new_record)


@app.put(
    "/restaurants/{restaurant_id}",
    response_model=Restaurant,
    tags=["Restaurants"],
    summary="Update restaurant",
    description="Update an existing restaurant's information."
)
def update_restaurant(restaurant_id: int, payload: RestaurantUpdate) -> Restaurant:
    """
    Update an existing restaurant.
    
    Args:
        restaurant_id: Restaurant to update
        payload: New restaurant data
        
    Returns:
        Updated restaurant
        
    Raises:
        HTTPException: 404 if restaurant not found
    """
    # Try database first
    if DB_AVAILABLE and db_update_restaurant:
        try:
            record = db_update_restaurant(restaurant_id, payload.model_dump())
            if record:
                # Update in-memory store for consistency
                for i, r in enumerate(restaurants_store):
                    if r["restaurant_id"] == restaurant_id:
                        restaurants_store[i] = record
                        break
                return record
        except Exception as e:
            logger.warning(f"Database update failed, using in-memory store: {e}")
    
    # Fallback to in-memory store
    record = _get_record_or_404(restaurants_store, "restaurant_id", restaurant_id)
    record.update(payload.model_dump())
    return deepcopy(record)


@app.delete(
    "/restaurants/{restaurant_id}",
    status_code=204,
    response_class=Response,
    tags=["Restaurants"],
    summary="Delete restaurant",
    description="Remove a restaurant from the system."
)
def delete_restaurant(restaurant_id: int) -> Response:
    """
    Delete a restaurant.
    
    Args:
        restaurant_id: Restaurant to delete
        
    Returns:
        Empty response with 204 status
        
    Raises:
        HTTPException: 404 if restaurant not found
    """
    # Verify restaurant exists first
    _get_record_or_404(restaurants_store, "restaurant_id", restaurant_id)
    
    # Try database first
    if DB_AVAILABLE and db_delete_restaurant:
        try:
            if db_delete_restaurant(restaurant_id):
                # Remove from in-memory store
                restaurants_store[:] = [r for r in restaurants_store if r["restaurant_id"] != restaurant_id]
                return Response(status_code=204)
        except Exception as e:
            logger.warning(f"Database delete failed, using in-memory store: {e}")
    
    # Fallback to in-memory store
    record = _get_record_or_404(restaurants_store, "restaurant_id", restaurant_id)
    restaurants_store.remove(record)
    return Response(status_code=204)


# ==============================================================================
# Menu Item Endpoints
# ==============================================================================


@app.get(
    "/menu-items",
    response_model=List[MenuItem],
    tags=["Menu Items"],
    summary="List menu items",
    description="Retrieve menu items with optional filtering."
)
def list_menu_items(
    restaurant_id: Optional[int] = Query(None, description="Filter by restaurant"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    available: Optional[bool] = Query(None, description="Filter by availability"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter")
) -> List[MenuItem]:
    """
    Get menu items with optional filters.
    
    Args:
        restaurant_id: Filter by restaurant (optional)
        category_id: Filter by category (optional)
        available: Filter by availability (optional)
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)
        
    Returns:
        List of menu items matching criteria
    """
    # Try database first
    if DB_AVAILABLE:
        try:
            results = db_get_menu_items(
                restaurant_id=restaurant_id,
                category_id=category_id,
                available=available,
                min_price=min_price,
                max_price=max_price
            )
            # Only use database results if they exist and are not empty
            if results is not None and len(results) > 0:
                return results
        except Exception as e:
            logger.warning(f"Database query failed, using in-memory store: {e}")
    
    # Fallback to in-memory store
    items = menu_items_store
    
    if restaurant_id is not None:
        items = [i for i in items if i["restaurant_id"] == restaurant_id]
    if category_id is not None:
        items = [i for i in items if i["category_id"] == category_id]
    if available is not None:
        items = [i for i in items if i["available"] == available]
    if min_price is not None:
        items = [i for i in items if i["base_price"] >= min_price]
    if max_price is not None:
        items = [i for i in items if i["base_price"] <= max_price]
    
    return deepcopy(items)


@app.get(
    "/menu-items/{product_id}",
    response_model=MenuItem,
    tags=["Menu Items"],
    summary="Get menu item by ID",
    description="Retrieve a specific menu item by its product ID."
)
def get_menu_item(product_id: int) -> MenuItem:
    """
    Get a single menu item by ID.
    
    Args:
        product_id: Unique product identifier
        
    Returns:
        Menu item data
        
    Raises:
        HTTPException: 404 if item not found
    """
    record = _get_record_or_404(menu_items_store, "product_id", product_id)
    return deepcopy(record)


@app.post(
    "/menu-items",
    response_model=MenuItem,
    status_code=201,
    tags=["Menu Items"],
    summary="Create menu item",
    description="Add a new menu item to a restaurant."
)
def create_menu_item(payload: MenuItemCreate) -> MenuItem:
    """
    Create a new menu item.
    
    Args:
        payload: Menu item data
        
    Returns:
        Created menu item with assigned ID
    """
    new_record = payload.model_dump()
    new_record["product_id"] = _next_id(menu_items_store, "product_id")
    menu_items_store.append(new_record)
    return deepcopy(new_record)


@app.put(
    "/menu-items/{product_id}",
    response_model=MenuItem,
    tags=["Menu Items"],
    summary="Update menu item",
    description="Update an existing menu item's information."
)
def update_menu_item(product_id: int, payload: MenuItemUpdate) -> MenuItem:
    """
    Update an existing menu item.
    
    Args:
        product_id: Product to update
        payload: New menu item data
        
    Returns:
        Updated menu item
        
    Raises:
        HTTPException: 404 if item not found
    """
    record = _get_record_or_404(menu_items_store, "product_id", product_id)
    record.update(payload.model_dump())
    return deepcopy(record)


@app.delete(
    "/menu-items/{product_id}",
    status_code=204,
    response_class=Response,
    tags=["Menu Items"],
    summary="Delete menu item",
    description="Remove a menu item from the system."
)
def delete_menu_item(product_id: int) -> Response:
    """
    Delete a menu item.
    
    Args:
        product_id: Product to delete
        
    Returns:
        Empty response with 204 status
        
    Raises:
        HTTPException: 404 if item not found
    """
    record = _get_record_or_404(menu_items_store, "product_id", product_id)
    menu_items_store.remove(record)
    return Response(status_code=204)


# ==============================================================================
# Customer Endpoints (Read-only)
# ==============================================================================


@app.get(
    "/customers",
    response_model=List[Customer],
    tags=["Customers"],
    summary="List customers",
    description="Retrieve customer segment data (anonymized)."
)
def list_customers(
    age_group: Optional[str] = Query(None, description="Filter by age group"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    min_spending: Optional[float] = Query(None, ge=0, description="Minimum average spending")
) -> List[Customer]:
    """
    Get customer data with optional filters.
    
    Args:
        age_group: Filter by age group (optional)
        gender: Filter by gender (optional)
        min_spending: Minimum spending filter (optional)
        
    Returns:
        List of customers matching criteria
    """
    results = customers_store
    
    if age_group:
        results = [c for c in results if c["age_group"] == age_group]
    if gender:
        results = [c for c in results if c["gender"].lower() == gender.lower()]
    if min_spending is not None:
        results = [c for c in results if c["avg_spending"] >= min_spending]
    
    return deepcopy(results)


@app.get(
    "/customers/{customer_id}",
    response_model=Customer,
    tags=["Customers"],
    summary="Get customer by ID",
    description="Retrieve a specific customer's segment data."
)
def get_customer(customer_id: int) -> Customer:
    """
    Get a single customer by ID.
    
    Args:
        customer_id: Unique customer identifier
        
    Returns:
        Customer data
        
    Raises:
        HTTPException: 404 if customer not found
    """
    record = _get_record_or_404(customers_store, "customer_id", customer_id)
    return deepcopy(record)


# ==============================================================================
# Categories Endpoint
# ==============================================================================


@app.get(
    "/categories",
    response_model=List[CategoryResponse],
    tags=["Categories"],
    summary="List categories",
    description="Retrieve all menu item categories."
)
def list_categories() -> List[CategoryResponse]:
    """
    Get all menu categories.
    
    Returns:
        List of all categories
    """
    return deepcopy(categories_store)


# ==============================================================================
# Price Prediction Endpoint
# ==============================================================================


@app.get(
    "/predict-price",
    response_model=PricePredictionResponse,
    tags=["Analytics"],
    summary="Predict optimal price",
    description="""
    Use the trained ML model to predict the optimal price for a menu item.
    
    The model considers:
    - Product type
    - Location in Yerevan
    - Venue type
    - Portion size
    - Target customer age group
    """
)
def predict_price(
    product_name: str = Query(..., description="Menu item name"),
    location: str = Query(..., description="Location in Yerevan"),
    venue_type: str = Query(..., description="Type of venue"),
    portion_size: str = Query("medium", description="Portion size (small/medium/large)"),
    age_group: str = Query("25-34", description="Target age group"),
    session_id: Optional[str] = Query(
        None,
        description="Optional session identifier used to save the prediction snapshot"
    )
) -> PricePredictionResponse:
    """
    Predict optimal price using CatBoost ML model.
    
    The model expects 8 features: location, type, age_group, category_id,
    portion_bucket, portion_numeric, base_price, cost.
    
    Product metadata (category_id, base_price, cost, portion_numeric) is 
    looked up from the menu items data based on product_name.
    
    Args:
        product_name: Name of the menu item
        location: District in Yerevan
        venue_type: Type of establishment
        portion_size: Size category (small/medium/large)
        age_group: Target customer segment
        
    Returns:
        Predicted price and input features
        
    Raises:
        HTTPException: 503 if CatBoost model not available, 404 if product not found
    """
    try:
        clean_session_id = session_id.strip() if session_id else None
        model = get_ml_model()
        
        # Look up product metadata from menu items
        matching_items = [
            item for item in menu_items_store
            if item.get("product_name", "").lower() == product_name.lower()
        ]
        
        if matching_items:
            product_meta = matching_items[0]
            category_id = str(product_meta.get("category_id", "1"))
            base_price = float(product_meta.get("base_price", 2000))
            cost = float(product_meta.get("cost", 1000))
            # Parse portion_size to numeric (e.g., "250g" -> 250)
            portion_str = str(product_meta.get("portion_size", "250"))
            import re
            portion_match = re.search(r"(\d+\.?\d*)", portion_str)
            portion_numeric = float(portion_match.group(1)) if portion_match else 250.0
        else:
            # Use defaults if product not found
            category_id = "1"
            base_price = 2000.0
            cost = 1000.0
            portion_numeric = 250.0
        
        # Prepare input data - columns must match training data exactly
        # CatBoost model expects: location, type, age_group, category_id, portion_bucket,
        #                         portion_numeric, base_price, cost
        input_data = pd.DataFrame({
            "location": [location],
            "type": [venue_type],
            "age_group": [age_group],
            "category_id": [category_id],
            "portion_bucket": [portion_size.lower()],
            "portion_numeric": [portion_numeric],
            "base_price": [base_price],
            "cost": [cost],
        })
        
        # CatBoost handles categorical features natively
        predicted_price = float(model.predict(input_data)[0])
        predicted_price_rounded = round(predicted_price, 2)
        confidence_low = round(predicted_price * 0.9, 2)
        confidence_high = round(predicted_price * 1.1, 2)
        confidence_note = "Prediction based on CatBoost model (RMSE: 196.74) trained on Yerevan market data"
        snapshot = _record_prediction_snapshot(
            clean_session_id,
            {
                "product_name": product_name,
                "location": location,
                "venue_type": venue_type,
                "portion_size": portion_size,
                "age_group": age_group,
                "predicted_price": predicted_price_rounded,
                "confidence_low": confidence_low,
                "confidence_high": confidence_high,
            },
        )

        return PricePredictionResponse(
            predicted_price=predicted_price_rounded,
            product_name=product_name,
            location=location,
            venue_type=venue_type,
            portion_size=portion_size,
            age_group=age_group,
            confidence_note=confidence_note,
            session_id=clean_session_id,
            snapshot_id=snapshot.get("snapshot_id") if snapshot else None
        )
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="ML model not available"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


# ==============================================================================
# Prediction Snapshot Endpoints
# ==============================================================================


@app.get(
    "/prediction-snapshots",
    response_model=List[PredictionSnapshotResponse],
    tags=["Analytics"],
    summary="List saved prediction snapshots",
    description="Return all saved predictions for the provided session identifier."
)
def list_prediction_snapshots(
    session_id: str = Query(..., description="Session identifier associated with saved predictions")
) -> List[PredictionSnapshotResponse]:
    """
    Retrieve saved predictions for a Streamlit session.
    """
    clean_session_id = session_id.strip()
    if not clean_session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    return _get_prediction_snapshots_for_session(clean_session_id)


@app.delete(
    "/prediction-snapshots",
    status_code=204,
    tags=["Analytics"],
    summary="Clear saved prediction snapshots",
    description="Remove all saved predictions for a session once they are downloaded."
)
def clear_prediction_snapshots(
    session_id: str = Query(..., description="Session identifier to delete")
) -> Response:
    """
    Delete all prediction snapshots associated with a session.
    """
    clean_session_id = session_id.strip()
    if not clean_session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    _clear_prediction_snapshots_for_session(clean_session_id)
    return Response(status_code=204)


# ==============================================================================
# Analytics Endpoints
# ==============================================================================


@app.get(
    "/analytics/forecast",
    response_model=ForecastResponse,
    tags=["Analytics"],
    summary="Get price forecast",
    description="Get predicted future price trends for a menu item."
)
def get_price_forecast(
    menu_item: str = Query("Cappuccino", description="Menu item to forecast"),
    horizon_days: int = Query(30, ge=1, le=365, description="Forecast horizon in days")
) -> ForecastResponse:
    """
    Get price forecast for a menu item.
    
    Args:
        menu_item: Name of the menu item
        horizon_days: Number of days to forecast
        
    Returns:
        Price forecast data
    """
    # Calculate base price from existing data
    matching_items = [
        i for i in menu_items_store 
        if i["product_name"].lower() == menu_item.lower()
    ]
    
    if matching_items:
        avg_price = sum(i["base_price"] for i in matching_items) / len(matching_items)
        # Apply a small trend adjustment based on horizon
        trend_factor = 1 + (horizon_days * 0.0005)  # 0.05% per day
        recommended_price = avg_price * trend_factor
    else:
        recommended_price = 1900
    
    # Determine trend direction
    if horizon_days <= 7:
        trend = "stable"
    elif horizon_days <= 30:
        trend = "slight_increase"
    else:
        trend = "moderate_increase"
    
    return ForecastResponse(
        menu_item=menu_item,
        recommended_price=round(recommended_price, 2),
        confidence=max(0.5, 0.95 - (horizon_days * 0.001)),
        horizon_days=horizon_days,
        trend=trend
    )


@app.get(
    "/analytics/price-distribution",
    response_model=PriceDistributionResponse,
    tags=["Analytics"],
    summary="Get price distribution",
    description="Get price distribution statistics for menu items with optional filters."
)
def get_price_distribution(
    menu_item: Optional[str] = Query(None, description="Filter by menu item name"),
    location: Optional[str] = Query(None, description="Filter by location")
) -> PriceDistributionResponse:
    """
    Get price distribution analytics.
    
    Args:
        menu_item: Optional menu item filter
        location: Optional location filter
        
    Returns:
        Price distribution data with statistics
        
    Raises:
        HTTPException: 500 if processing fails
    """
    try:
        logger.info(f"Price distribution request: menu_item={menu_item}, location={location}")
        
        # Filter menu items
        filtered_items = menu_items_store
        if menu_item:
            filtered_items = [i for i in filtered_items if i["product_name"].lower() == menu_item.lower()]
        if location:
            # Get restaurant IDs for this location
            location_restaurant_ids = {
                r["restaurant_id"] for r in restaurants_store 
                if r["location"].lower() == location.lower()
            }
            filtered_items = [i for i in filtered_items if i["restaurant_id"] in location_restaurant_ids]
        
        if not filtered_items:
            logger.warning(f"No items found for price distribution: menu_item={menu_item}, location={location}")
            return PriceDistributionResponse(
                menu_item=menu_item,
                location=location,
                total_items=0,
                distribution=[],
                avg_price=0.0,
                median_price=0.0,
                std_dev=0.0
            )
        
        prices = [i["base_price"] for i in filtered_items]
        prices_sorted = sorted(prices)
        
        # Calculate statistics
        avg_price = sum(prices) / len(prices)
        median_price = prices_sorted[len(prices_sorted) // 2] if prices_sorted else 0.0
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        
        # Create price distribution buckets
        min_price = min(prices)
        max_price = max(prices)
        bucket_size = max(500, (max_price - min_price) / 10)  # At least 10 buckets, min 500 AMD per bucket
        
        distribution_dict = {}
        for price in prices:
            bucket_start = int((price // bucket_size) * bucket_size)
            bucket_end = bucket_start + int(bucket_size)
            bucket_key = f"{bucket_start}-{bucket_end}"
            distribution_dict[bucket_key] = distribution_dict.get(bucket_key, 0) + 1
        
        distribution = [
            PriceDistributionItem(
                price_range=range_key,
                count=count,
                percentage=round((count / len(prices)) * 100, 2)
            )
            for range_key, count in sorted(distribution_dict.items(), key=lambda x: int(x[0].split('-')[0]))
        ]
        
        logger.info(f"Price distribution calculated: {len(filtered_items)} items, {len(distribution)} buckets")
        
        return PriceDistributionResponse(
            menu_item=menu_item,
            location=location,
            total_items=len(filtered_items),
            distribution=distribution,
            avg_price=round(avg_price, 2),
            median_price=round(median_price, 2),
            std_dev=round(std_dev, 2)
        )
    except Exception as e:
        logger.error(f"Error calculating price distribution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate price distribution: {str(e)}"
        )


@app.get(
    "/analytics/market-comparison",
    response_model=MarketComparisonResponse,
    tags=["Analytics"],
    summary="Compare market prices",
    description="Compare prices for a specific menu item across different restaurants and locations."
)
def get_market_comparison(
    product_name: str = Query(..., description="Menu item name to compare"),
    location: Optional[str] = Query(None, description="Filter by location"),
    venue_type: Optional[str] = Query(None, description="Filter by venue type")
) -> MarketComparisonResponse:
    """
    Get market price comparison for a menu item.
    
    Args:
        product_name: Name of the menu item to compare
        location: Optional location filter
        venue_type: Optional venue type filter
        
    Returns:
        Market comparison data with prices across restaurants
        
    Raises:
        HTTPException: 500 if processing fails
    """
    try:
        logger.info(f"Market comparison request: product_name={product_name}, location={location}, venue_type={venue_type}")
        
        # Find all menu items with this product name
        matching_items = [
            i for i in menu_items_store 
            if i["product_name"].lower() == product_name.lower()
        ]
        
        # Apply filters
        if location:
            location_restaurant_ids = {
                r["restaurant_id"] for r in restaurants_store 
                if r["location"].lower() == location.lower()
            }
            matching_items = [i for i in matching_items if i["restaurant_id"] in location_restaurant_ids]
        
        if venue_type:
            venue_restaurant_ids = {
                r["restaurant_id"] for r in restaurants_store 
                if r["venue_type"].lower() == venue_type.lower()
            }
            matching_items = [i for i in matching_items if i["restaurant_id"] in venue_restaurant_ids]
        
        if not matching_items:
            logger.warning(f"No items found for market comparison: product_name={product_name}")
            return MarketComparisonResponse(
                product_name=product_name,
                location=location,
                venue_type=venue_type,
                comparisons=[],
                market_avg_price=0.0,
                market_min_price=0.0,
                market_max_price=0.0
            )
        
        # Build restaurant lookup
        restaurant_dict = {r["restaurant_id"]: r for r in restaurants_store}
        
        # Build comparison items
        comparisons = []
        for item in matching_items:
            restaurant = restaurant_dict.get(item["restaurant_id"], {})
            price = item["base_price"]
            cost = item.get("cost", 0)
            margin = ((price - cost) / price * 100) if price > 0 else 0.0
            
            comparisons.append(MarketComparisonItem(
                restaurant_id=item["restaurant_id"],
                restaurant_name=restaurant.get("name", f"Restaurant {item['restaurant_id']}"),
                location=restaurant.get("location", "Unknown"),
                venue_type=restaurant.get("venue_type", "Unknown"),
                price=round(price, 2),
                cost=round(cost, 2),
                margin=round(margin, 2)
            ))
        
        prices = [c.price for c in comparisons]
        market_avg_price = sum(prices) / len(prices) if prices else 0.0
        market_min_price = min(prices) if prices else 0.0
        market_max_price = max(prices) if prices else 0.0
        
        logger.info(f"Market comparison calculated: {len(comparisons)} restaurants found")
        
        return MarketComparisonResponse(
            product_name=product_name,
            location=location,
            venue_type=venue_type,
            comparisons=comparisons,
            market_avg_price=round(market_avg_price, 2),
            market_min_price=round(market_min_price, 2),
            market_max_price=round(market_max_price, 2)
        )
    except Exception as e:
        logger.error(f"Error calculating market comparison: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate market comparison: {str(e)}"
        )


@app.get(
    "/analytics/categories",
    response_model=CategoryAnalyticsResponse,
    tags=["Analytics"],
    summary="Get category analytics",
    description="Get analytics aggregated by menu category."
)
def get_category_analytics(
    location: Optional[str] = Query(None, description="Filter by location"),
    venue_type: Optional[str] = Query(None, description="Filter by venue type")
) -> CategoryAnalyticsResponse:
    """
    Get category-level analytics.
    
    Args:
        location: Optional location filter
        venue_type: Optional venue type filter
        
    Returns:
        Analytics aggregated by category
        
    Raises:
        HTTPException: 500 if processing fails
    """
    try:
        logger.info(f"Category analytics request: location={location}, venue_type={venue_type}")
        
        # Filter menu items
        filtered_items = menu_items_store
        if location:
            location_restaurant_ids = {
                r["restaurant_id"] for r in restaurants_store 
                if r["location"].lower() == location.lower()
            }
            filtered_items = [i for i in filtered_items if i["restaurant_id"] in location_restaurant_ids]
        
        if venue_type:
            venue_restaurant_ids = {
                r["restaurant_id"] for r in restaurants_store 
                if r["venue_type"].lower() == venue_type.lower()
            }
            filtered_items = [i for i in filtered_items if i["restaurant_id"] in venue_restaurant_ids]
        
        # Group by category
        category_dict = {}
        for item in filtered_items:
            cat_id = item["category_id"]
            if cat_id not in category_dict:
                category_dict[cat_id] = {
                    "category_id": cat_id,
                    "category_name": f"Category {cat_id}",  # Would need category lookup in real implementation
                    "prices": [],
                    "items": []
                }
            category_dict[cat_id]["prices"].append(item["base_price"])
            category_dict[cat_id]["items"].append(item)
        
        # Build response
        categories = []
        for cat_id, cat_data in category_dict.items():
            prices = cat_data["prices"]
            categories.append(CategoryAnalyticsItem(
                category_id=cat_id,
                category_name=cat_data["category_name"],
                item_count=len(cat_data["items"]),
                avg_price=round(sum(prices) / len(prices), 2) if prices else 0.0,
                min_price=round(min(prices), 2) if prices else 0.0,
                max_price=round(max(prices), 2) if prices else 0.0,
                total_revenue=round(sum(prices) * 100, 2)  # Estimated (would need actual sales data)
            ))
        
        logger.info(f"Category analytics calculated: {len(categories)} categories found")
        
        return CategoryAnalyticsResponse(
            location=location,
            venue_type=venue_type,
            categories=sorted(categories, key=lambda x: x.item_count, reverse=True),
            total_categories=len(categories)
        )
    except Exception as e:
        logger.error(f"Error calculating category analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate category analytics: {str(e)}"
        )


@app.get(
    "/analytics/revenue",
    response_model=RevenueAnalyticsResponse,
    tags=["Analytics"],
    summary="Get revenue analytics",
    description="Get revenue and profit margin analytics by restaurant."
)
def get_revenue_analytics(
    location: Optional[str] = Query(None, description="Filter by location"),
    venue_type: Optional[str] = Query(None, description="Filter by venue type")
) -> RevenueAnalyticsResponse:
    """
    Get revenue and margin analytics.
    
    Args:
        location: Optional location filter
        venue_type: Optional venue type filter
        
    Returns:
        Revenue analytics by restaurant
        
    Raises:
        HTTPException: 500 if processing fails
    """
    try:
        logger.info(f"Revenue analytics request: location={location}, venue_type={venue_type}")
        
        # Filter restaurants
        filtered_restaurants = restaurants_store
        if location:
            filtered_restaurants = [
                r for r in filtered_restaurants 
                if r["location"].lower() == location.lower()
            ]
        if venue_type:
            filtered_restaurants = [
                r for r in filtered_restaurants 
                if r["venue_type"].lower() == venue_type.lower()
            ]
        
        # Calculate revenue per restaurant
        restaurant_dict = {r["restaurant_id"]: r for r in filtered_restaurants}
        restaurant_items = {}
        
        for item in menu_items_store:
            restaurant_id = item["restaurant_id"]
            if restaurant_id in restaurant_dict:
                if restaurant_id not in restaurant_items:
                    restaurant_items[restaurant_id] = {"items": [], "revenue": 0.0, "cost": 0.0}
                restaurant_items[restaurant_id]["items"].append(item)
                # Estimate revenue (price * avg daily sales * 30 days)
                avg_daily_sales = restaurant_dict[restaurant_id].get("avg_customer_count", 50)
                estimated_monthly_sales = avg_daily_sales * 0.3  # 30% order this item
                restaurant_items[restaurant_id]["revenue"] += item["base_price"] * estimated_monthly_sales * 30
                restaurant_items[restaurant_id]["cost"] += item.get("cost", 0) * estimated_monthly_sales * 30
        
        # Build response
        restaurants = []
        total_revenue = 0.0
        total_profit = 0.0
        
        for restaurant_id, data in restaurant_items.items():
            restaurant = restaurant_dict[restaurant_id]
            revenue = data["revenue"]
            cost = data["cost"]
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0.0
            
            restaurants.append(RevenueAnalyticsItem(
                restaurant_id=restaurant_id,
                restaurant_name=restaurant.get("name", f"Restaurant {restaurant_id}"),
                total_revenue=round(revenue, 2),
                total_cost=round(cost, 2),
                profit=round(profit, 2),
                margin_percentage=round(margin, 2),
                item_count=len(data["items"])
            ))
            
            total_revenue += revenue
            total_profit += profit
        
        avg_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0
        
        logger.info(f"Revenue analytics calculated: {len(restaurants)} restaurants, total_revenue={total_revenue}")
        
        return RevenueAnalyticsResponse(
            location=location,
            venue_type=venue_type,
            restaurants=sorted(restaurants, key=lambda x: x.total_revenue, reverse=True),
            total_revenue=round(total_revenue, 2),
            total_profit=round(total_profit, 2),
            avg_margin=round(avg_margin, 2)
        )
    except Exception as e:
        logger.error(f"Error calculating revenue analytics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate revenue analytics: {str(e)}"
        )


@app.get(
    "/analytics/time-series",
    response_model=TimeSeriesResponse,
    tags=["Analytics"],
    summary="Get time series price data",
    description="Get historical price data as time series for trend visualization."
)
def get_time_series(
    menu_item: str = Query(..., description="Menu item name"),
    location: Optional[str] = Query(None, description="Filter by location"),
    days: int = Query(30, ge=7, le=365, description="Number of days to retrieve")
) -> TimeSeriesResponse:
    """
    Get time series price data for a menu item.
    
    Note: This is a simplified implementation. In production, this would query
    actual historical price data from the database with timestamps.
    
    Args:
        menu_item: Menu item name
        location: Optional location filter
        days: Number of days to retrieve
        
    Returns:
        Time series data points
        
    Raises:
        HTTPException: 500 if processing fails
    """
    try:
        logger.info(f"Time series request: menu_item={menu_item}, location={location}, days={days}")
        
        from datetime import datetime, timedelta
        
        # Find matching items
        matching_items = [
            i for i in menu_items_store 
            if i["product_name"].lower() == menu_item.lower()
        ]
        
        if location:
            location_restaurant_ids = {
                r["restaurant_id"] for r in restaurants_store 
                if r["location"].lower() == location.lower()
            }
            matching_items = [i for i in matching_items if i["restaurant_id"] in location_restaurant_ids]
        
        if not matching_items:
            # Return empty series
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            logger.warning(f"No items found for time series: menu_item={menu_item}, location={location}")
            return TimeSeriesResponse(
                menu_item=menu_item,
                location=location,
                data_points=[],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
        
        # Calculate average price
        avg_price = sum(i["base_price"] for i in matching_items) / len(matching_items)
        
        # Generate synthetic time series (in production, this would come from actual historical data)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        data_points = []
        current_date = start_date
        base_price = avg_price
        import random
        
        while current_date <= end_date:
            # Simulate price variation (±5%)
            variation = random.uniform(-0.05, 0.05)
            price = base_price * (1 + variation)
            
            data_points.append(TimeSeriesDataPoint(
                date=current_date.isoformat(),
                price=round(price, 2),
                volume=random.randint(10, 50) if random.random() > 0.7 else None
            ))
            
            current_date += timedelta(days=1)
        
        logger.info(f"Time series generated: {len(data_points)} data points")
        
        return TimeSeriesResponse(
            menu_item=menu_item,
            location=location,
            data_points=data_points,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
    except Exception as e:
        logger.error(f"Error generating time series: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate time series: {str(e)}"
        )


# ==============================================================================
# Reference Data Endpoints
# ==============================================================================


@app.get(
    "/reference/locations",
    response_model=List[str],
    tags=["Reference"],
    summary="List valid locations",
    description="Get list of valid Yerevan districts for filtering."
)
def get_locations() -> List[str]:
    """Get all valid location values."""
    return ["Ajapnyak", "Arabkir", "Kentron", "Malatia-Sebastia", "Nor Nork"]


@app.get(
    "/reference/venue-types",
    response_model=List[str],
    tags=["Reference"],
    summary="List venue types",
    description="Get list of valid venue types."
)
def get_venue_types() -> List[str]:
    """Get all valid venue type values."""
    return list(set(r["venue_type"] for r in restaurants_store))


@app.get(
    "/reference/menu-item-names",
    response_model=List[str],
    tags=["Reference"],
    summary="List menu item names",
    description="Get list of all unique menu item names."
)
def get_menu_item_names() -> List[str]:
    """Get all unique menu item names."""
    return sorted(list(set(i["product_name"] for i in menu_items_store)))
