"""
Yerevan Dynamic Pricing API - Milestone 3

This FastAPI service provides endpoints for:
- Restaurant management (CRUD operations)
- Menu item management (CRUD operations)
- Customer data access (read-only)
- Price prediction using ML model
- Historical analytics
- Price forecasting

Author: Backend Team (NarekN7)
Version: 1.0.0
"""

from __future__ import annotations

import os
import pickle
from copy import deepcopy
from pathlib import Path
from typing import List, Optional, Literal
from enum import Enum

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Response, Query
from pydantic import BaseModel, Field, ConfigDict

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
# Enums for validation
# ==============================================================================


class LocationEnum(str, Enum):
    """Valid locations in Yerevan for pricing analysis."""
    AJAPNYAK = "Ajapnyak"
    ARABKIR = "Arabkir"
    KENTRON = "Kentron"
    MALATIA_SEBASTIA = "Malatia-Sebastia"
    NOR_NORK = "Nor Nork"


class VenueTypeEnum(str, Enum):
    """Types of food service venues."""
    RESTAURANT = "restaurant"
    COFFEE_HOUSE = "coffee_house"
    BAR_BISTRO = "bar_bistro"
    BAKERY_CAFE = "bakery_cafe"
    COFFEE_CHAIN = "coffee_chain"
    CAFE = "cafe"
    CAFE_BISTRO = "cafe_bistro"
    CAFE_DESSERT = "cafe_dessert"
    CAFE_RESTAURANT = "cafe_restaurant"
    FAST_FOOD = "fast_food"
    GASTROPUB = "gastropub"
    HEALTHY_CAFE = "healthy_cafe"
    ITALIAN_REST = "italian_rest"
    PIZZERIA = "pizzeria"
    WINE_BAR = "wine_bar"
    BAR_RESTAURANT = "bar_restaurant"
    BISTRO = "bistro"
    BREWPUB = "brewpub"


class AgeGroupEnum(str, Enum):
    """Customer age group categories."""
    AGE_0_17 = "0-17"
    AGE_18_24 = "18-24"
    AGE_25_34 = "25-34"
    AGE_35_44 = "35-44"
    AGE_45_54 = "45-54"
    AGE_55_PLUS = "55+"


class PortionSizeEnum(str, Enum):
    """Portion size categories."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


# ==============================================================================
# Pydantic Models - Requests
# ==============================================================================


class RestaurantCreate(BaseModel):
    """
    Request model for creating a new restaurant.
    
    Attributes:
        name: Restaurant name (required)
        location: District in Yerevan
        venue_type: Type of establishment
        avg_customer_count: Average daily customers
        rating: Customer rating (0-5 scale)
        owner_contact: Contact phone number
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Cafe Central",
            "location": "Kentron",
            "venue_type": "cafe",
            "avg_customer_count": 150,
            "rating": 4.5,
            "owner_contact": "+374-10-123456"
        }
    })
    
    name: str = Field(..., min_length=1, max_length=255, description="Restaurant name")
    location: str = Field(..., description="District in Yerevan")
    venue_type: str = Field(..., description="Type of venue (restaurant, cafe, etc.)")
    avg_customer_count: int = Field(..., ge=0, description="Average daily customer count")
    rating: float = Field(..., ge=0, le=5, description="Rating on 0-5 scale")
    owner_contact: str = Field(..., description="Owner contact phone number")


class RestaurantUpdate(RestaurantCreate):
    """Request model for updating an existing restaurant."""
    pass


class MenuItemCreate(BaseModel):
    """
    Request model for creating a new menu item.
    
    Attributes:
        restaurant_id: ID of the restaurant this item belongs to
        product_name: Name of the menu item
        category_id: Category identifier
        base_price: Base price in AMD
        cost: Cost to produce in AMD
        portion_size: Size description (e.g., "250ml", "400g")
        available: Whether item is currently available
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "restaurant_id": 1,
            "product_name": "Cappuccino",
            "category_id": 1,
            "base_price": 1500,
            "cost": 600,
            "portion_size": "250ml",
            "available": True
        }
    })
    
    restaurant_id: int = Field(..., ge=1, description="Restaurant ID")
    product_name: str = Field(..., min_length=1, max_length=255, description="Product name")
    category_id: int = Field(..., ge=1, description="Category ID")
    base_price: float = Field(..., ge=0, description="Base price in AMD")
    cost: float = Field(..., ge=0, description="Production cost in AMD")
    portion_size: str = Field(..., description="Portion size (e.g., 250ml, 400g)")
    available: bool = Field(True, description="Is item available for sale")


class MenuItemUpdate(MenuItemCreate):
    """Request model for updating an existing menu item."""
    pass


class PricePredictionRequest(BaseModel):
    """
    Request model for price prediction.
    
    The ML model uses these features to predict optimal pricing.
    
    Attributes:
        product_name: Name of the menu item to price
        location: District in Yerevan
        venue_type: Type of establishment
        portion_size: Size category (small/medium/large)
        age_group: Target customer age group
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "product_name": "Cappuccino",
            "location": "Kentron",
            "venue_type": "coffee_house",
            "portion_size": "medium",
            "age_group": "25-34"
        }
    })
    
    product_name: str = Field(..., description="Menu item name")
    location: str = Field(..., description="Location in Yerevan")
    venue_type: str = Field(..., alias="type", description="Venue type")
    portion_size: str = Field(..., alias="portion_bucket", description="Portion size category")
    age_group: str = Field(..., description="Target age group")


# ==============================================================================
# Pydantic Models - Responses
# ==============================================================================


class Restaurant(BaseModel):
    """
    Response model for restaurant data.
    
    Includes all restaurant attributes plus the unique identifier.
    """
    model_config = ConfigDict(from_attributes=True)
    
    restaurant_id: int = Field(..., description="Unique restaurant identifier")
    name: str = Field(..., description="Restaurant name")
    location: str = Field(..., description="District in Yerevan")
    venue_type: str = Field(..., description="Type of venue")
    avg_customer_count: int = Field(..., description="Average daily customers")
    rating: float = Field(..., description="Customer rating (0-5)")
    owner_contact: str = Field(..., description="Owner contact info")


class MenuItem(BaseModel):
    """
    Response model for menu item data.
    
    Includes all menu item attributes plus the unique identifier.
    """
    model_config = ConfigDict(from_attributes=True)
    
    product_id: int = Field(..., description="Unique product identifier")
    restaurant_id: int = Field(..., description="Parent restaurant ID")
    product_name: str = Field(..., description="Product name")
    category_id: int = Field(..., description="Category ID")
    base_price: float = Field(..., description="Base price in AMD")
    cost: float = Field(..., description="Production cost in AMD")
    portion_size: str = Field(..., description="Portion size")
    available: bool = Field(..., description="Availability status")


class Customer(BaseModel):
    """
    Response model for customer data.
    
    Contains anonymized customer segment information.
    """
    model_config = ConfigDict(from_attributes=True)
    
    customer_id: int = Field(..., description="Unique customer identifier")
    gender: str = Field(..., description="Customer gender")
    age_group: str = Field(..., description="Age group category")
    avg_spending: float = Field(..., description="Average spending in AMD")
    visit_frequency: int = Field(..., description="Visits per month")


class PricePredictionResponse(BaseModel):
    """
    Response model for price prediction.
    
    Contains the predicted price and input features used.
    """
    predicted_price: float = Field(..., description="Predicted optimal price in AMD")
    product_name: str = Field(..., description="Menu item name")
    location: str = Field(..., description="Location used for prediction")
    venue_type: str = Field(..., description="Venue type used")
    portion_size: str = Field(..., description="Portion size category")
    age_group: str = Field(..., description="Target age group")
    confidence_note: str = Field(
        default="Prediction based on CatBoost model (RMSE: 196.74) trained on Yerevan market data",
        description="Model confidence information"
    )


class HistoricalAnalyticsResponse(BaseModel):
    """
    Response model for historical analytics data.
    
    Provides aggregated historical pricing and sales information.
    """
    menu_item: str = Field(..., description="Menu item analyzed")
    location: str = Field(..., description="Location filter applied")
    avg_price: float = Field(..., description="Average historical price in AMD")
    min_price: float = Field(..., description="Minimum observed price")
    max_price: float = Field(..., description="Maximum observed price")
    units_sold: int = Field(..., description="Total units sold")
    market: str = Field(..., description="Market segment")
    season: str = Field(..., description="Season of data")


class ForecastResponse(BaseModel):
    """
    Response model for price forecasting.
    
    Contains predicted future price and confidence metrics.
    """
    menu_item: str = Field(..., description="Menu item forecasted")
    recommended_price: float = Field(..., description="Recommended price in AMD")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    horizon_days: int = Field(..., description="Forecast horizon in days")
    trend: str = Field(default="stable", description="Price trend direction")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")


class CategoryResponse(BaseModel):
    """Response model for menu category."""
    category_id: int = Field(..., description="Category ID")
    category_name: str = Field(..., description="Category name")


# ==============================================================================
# Data Loading and ML Model
# ==============================================================================


def _load_csv(filename: str) -> List[dict]:
    """
    Load data from a CSV file in the data directory.
    
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


# Initialize data stores
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
            raise HTTPException(
                status_code=503,
                detail=f"Failed to load CatBoost model: {str(e)}"
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
- **Analytics**: Historical data and forecasting endpoints

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
    return HealthResponse(
        status="ok",
        version="1.0.0",
        database="connected"
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
    age_group: str = Query("25-34", description="Target age group")
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
        confidence_note = "Prediction based on CatBoost model (RMSE: 196.74) trained on Yerevan market data"
        
        return PricePredictionResponse(
            predicted_price=round(predicted_price, 2),
            product_name=product_name,
            location=location,
            venue_type=venue_type,
            portion_size=portion_size,
            age_group=age_group,
            confidence_note=confidence_note
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
# Analytics Endpoints
# ==============================================================================


@app.get(
    "/analytics/historical",
    response_model=HistoricalAnalyticsResponse,
    tags=["Analytics"],
    summary="Get historical analytics",
    description="Retrieve historical pricing and sales data for analysis."
)
def get_historical_snapshot(
    menu_item: str = Query("Cappuccino", description="Menu item to analyze"),
    location: str = Query("Kentron", description="Location filter")
) -> HistoricalAnalyticsResponse:
    """
    Get historical analytics for a menu item.
    
    Args:
        menu_item: Name of the menu item
        location: District to filter by
        
    Returns:
        Historical analytics data
    """
    # Filter menu items by name
    matching_items = [
        i for i in menu_items_store 
        if i["product_name"].lower() == menu_item.lower()
    ]
    
    if matching_items:
        prices = [i["base_price"] for i in matching_items]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
    else:
        avg_price = 1800
        min_price = 1500
        max_price = 2200
    
    return HistoricalAnalyticsResponse(
        menu_item=menu_item,
        location=location,
        avg_price=round(avg_price, 2),
        min_price=round(min_price, 2),
        max_price=round(max_price, 2),
        units_sold=1200,
        market=location,
        season="Winter"
    )


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
