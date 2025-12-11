"""
Pydantic schemas and Enums for the Yerevan Dynamic Pricing API.

This module contains all data models, request/response schemas, and validation enums
used throughout the API endpoints.

Author: Backend Team (NarekN7)
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


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
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier associated with this prediction"
    )
    snapshot_id: Optional[int] = Field(
        default=None,
        description="Identifier of the saved snapshot (if persisted)"
    )


class PredictionSnapshotResponse(BaseModel):
    """
    Response model representing stored prediction snapshots.
    """
    snapshot_id: int = Field(..., description="Snapshot identifier")
    session_id: str = Field(..., description="Session identifier")
    product_name: str = Field(..., description="Menu item name")
    location: str = Field(..., description="Yerevan district")
    venue_type: str = Field(..., description="Venue type used for prediction")
    portion_size: str = Field(..., description="Portion size category")
    age_group: str = Field(..., description="Target age group")
    predicted_price: float = Field(..., description="Predicted price in AMD")
    confidence_low: float = Field(..., description="Lower bound of confidence window")
    confidence_high: float = Field(..., description="Upper bound of confidence window")
    created_at: datetime = Field(..., description="Timestamp when prediction was saved")


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
# Analytics Visualization Models
# ==============================================================================


class PriceDistributionItem(BaseModel):
    """Single item in price distribution."""
    price_range: str = Field(..., description="Price range label (e.g., '1000-1500')")
    count: int = Field(..., description="Number of items in this range")
    percentage: float = Field(..., description="Percentage of total items")


class PriceDistributionResponse(BaseModel):
    """Response model for price distribution analytics."""
    menu_item: Optional[str] = Field(None, description="Menu item filter (if applied)")
    location: Optional[str] = Field(None, description="Location filter (if applied)")
    total_items: int = Field(..., description="Total number of items analyzed")
    distribution: List[PriceDistributionItem] = Field(..., description="Price distribution data")
    avg_price: float = Field(..., description="Average price")
    median_price: float = Field(..., description="Median price")
    std_dev: float = Field(..., description="Standard deviation")


class MarketComparisonItem(BaseModel):
    """Single item in market comparison."""
    restaurant_id: int = Field(..., description="Restaurant ID")
    restaurant_name: str = Field(..., description="Restaurant name")
    location: str = Field(..., description="Location")
    venue_type: str = Field(..., description="Venue type")
    price: float = Field(..., description="Price in AMD")
    cost: float = Field(..., description="Cost in AMD")
    margin: float = Field(..., description="Profit margin percentage")


class MarketComparisonResponse(BaseModel):
    """Response model for market price comparison."""
    product_name: str = Field(..., description="Product being compared")
    location: Optional[str] = Field(None, description="Location filter (if applied)")
    venue_type: Optional[str] = Field(None, description="Venue type filter (if applied)")
    comparisons: List[MarketComparisonItem] = Field(..., description="Market comparison data")
    market_avg_price: float = Field(..., description="Market average price")
    market_min_price: float = Field(..., description="Market minimum price")
    market_max_price: float = Field(..., description="Market maximum price")


class CategoryAnalyticsItem(BaseModel):
    """Single category in category analytics."""
    category_id: int = Field(..., description="Category ID")
    category_name: str = Field(..., description="Category name")
    item_count: int = Field(..., description="Number of items in category")
    avg_price: float = Field(..., description="Average price in category")
    min_price: float = Field(..., description="Minimum price in category")
    max_price: float = Field(..., description="Maximum price in category")
    total_revenue: float = Field(..., description="Estimated total revenue (if available)")


class CategoryAnalyticsResponse(BaseModel):
    """Response model for category analytics."""
    location: Optional[str] = Field(None, description="Location filter (if applied)")
    venue_type: Optional[str] = Field(None, description="Venue type filter (if applied)")
    categories: List[CategoryAnalyticsItem] = Field(..., description="Category analytics data")
    total_categories: int = Field(..., description="Total number of categories")


class RevenueAnalyticsItem(BaseModel):
    """Single item in revenue analytics."""
    restaurant_id: int = Field(..., description="Restaurant ID")
    restaurant_name: str = Field(..., description="Restaurant name")
    total_revenue: float = Field(..., description="Total estimated revenue")
    total_cost: float = Field(..., description="Total cost")
    profit: float = Field(..., description="Total profit")
    margin_percentage: float = Field(..., description="Profit margin percentage")
    item_count: int = Field(..., description="Number of menu items")


class RevenueAnalyticsResponse(BaseModel):
    """Response model for revenue and margin analytics."""
    location: Optional[str] = Field(None, description="Location filter (if applied)")
    venue_type: Optional[str] = Field(None, description="Venue type filter (if applied)")
    restaurants: List[RevenueAnalyticsItem] = Field(..., description="Revenue analytics by restaurant")
    total_revenue: float = Field(..., description="Total revenue across all restaurants")
    total_profit: float = Field(..., description="Total profit across all restaurants")
    avg_margin: float = Field(..., description="Average profit margin percentage")


class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series."""
    date: str = Field(..., description="Date (ISO format)")
    price: float = Field(..., description="Price at this date")
    volume: Optional[int] = Field(None, description="Sales volume (if available)")


class TimeSeriesResponse(BaseModel):
    """Response model for time series price data."""
    menu_item: str = Field(..., description="Menu item name")
    location: Optional[str] = Field(None, description="Location filter (if applied)")
    data_points: List[TimeSeriesDataPoint] = Field(..., description="Time series data points")
    start_date: str = Field(..., description="Start date of series")
    end_date: str = Field(..., description="End date of series")
