# Yerevan Dynamic Pricing API Specification

**Version:** 1.0.0  
**Base URL:** `http://localhost:8008` (Docker) or `http://localhost:8000` (local)  
**Format:** JSON  
**Authentication:** None required (development phase)

---

## Overview

This API provides endpoints for the Yerevan Dynamic Pricing system, enabling:
- Restaurant and menu item management
- Customer data access
- ML-powered price prediction
- Historical analytics and forecasting

---

## Endpoints Summary

### Health & Status
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |

### Restaurants
| Method | Path | Description |
|--------|------|-------------|
| GET | `/restaurants` | List all restaurants |
| GET | `/restaurants/{id}` | Get restaurant by ID |
| POST | `/restaurants` | Create new restaurant |
| PUT | `/restaurants/{id}` | Update restaurant |
| DELETE | `/restaurants/{id}` | Delete restaurant |

### Menu Items
| Method | Path | Description |
|--------|------|-------------|
| GET | `/menu-items` | List menu items |
| GET | `/menu-items/{id}` | Get menu item by ID |
| POST | `/menu-items` | Create menu item |
| PUT | `/menu-items/{id}` | Update menu item |
| DELETE | `/menu-items/{id}` | Delete menu item |

### Customers
| Method | Path | Description |
|--------|------|-------------|
| GET | `/customers` | List customers |
| GET | `/customers/{id}` | Get customer by ID |

### Categories
| Method | Path | Description |
|--------|------|-------------|
| GET | `/categories` | List all categories |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| POST | `/predict-price` | ML price prediction |
| GET | `/analytics/historical` | Historical data |
| GET | `/analytics/forecast` | Price forecast |

### Reference Data
| Method | Path | Description |
|--------|------|-------------|
| GET | `/reference/locations` | Valid locations |
| GET | `/reference/venue-types` | Valid venue types |
| GET | `/reference/menu-item-names` | Menu item names |

---

## Detailed Endpoint Documentation

### Health Check

#### `GET /health`

Returns the current health status of the API.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected"
}
```

---

### Restaurants

#### `GET /restaurants`

List all restaurants with optional filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `location` | string | Filter by district |
| `venue_type` | string | Filter by venue type |
| `min_rating` | float | Minimum rating (0-5) |

**Response:**
```json
[
  {
    "restaurant_id": 1,
    "name": "Gallia",
    "location": "Kentron",
    "venue_type": "restaurant",
    "avg_customer_count": 162,
    "rating": 4.16,
    "owner_contact": "+374-81-210268"
  }
]
```

#### `GET /restaurants/{restaurant_id}`

Get a specific restaurant by ID.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `restaurant_id` | integer | Restaurant ID |

**Response:** Single restaurant object

**Errors:**
- `404`: Restaurant not found

#### `POST /restaurants`

Create a new restaurant.

**Request Body:**
```json
{
  "name": "Cafe Central",
  "location": "Kentron",
  "venue_type": "cafe",
  "avg_customer_count": 150,
  "rating": 4.5,
  "owner_contact": "+374-10-123456"
}
```

**Response:** Created restaurant with assigned ID (status 201)

#### `PUT /restaurants/{restaurant_id}`

Update an existing restaurant.

**Request Body:** Same as POST

**Response:** Updated restaurant object

#### `DELETE /restaurants/{restaurant_id}`

Delete a restaurant.

**Response:** Empty (status 204)

---

### Menu Items

#### `GET /menu-items`

List menu items with optional filtering.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `restaurant_id` | integer | Filter by restaurant |
| `category_id` | integer | Filter by category |
| `available` | boolean | Filter by availability |
| `min_price` | float | Minimum price |
| `max_price` | float | Maximum price |

**Response:**
```json
[
  {
    "product_id": 1,
    "restaurant_id": 1,
    "product_name": "Cappuccino",
    "category_id": 1,
    "base_price": 1500.0,
    "cost": 600.0,
    "portion_size": "250ml",
    "available": true
  }
]
```

#### `POST /menu-items`

Create a new menu item.

**Request Body:**
```json
{
  "restaurant_id": 1,
  "product_name": "Latte",
  "category_id": 1,
  "base_price": 1800,
  "cost": 700,
  "portion_size": "300ml",
  "available": true
}
```

---

### Price Prediction

#### `POST /predict-price`

Use the ML model to predict optimal pricing.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_name` | string | Yes | Menu item name |
| `location` | string | Yes | Yerevan district |
| `venue_type` | string | Yes | Type of venue |
| `portion_size` | string | No | small/medium/large (default: medium) |
| `age_group` | string | No | Target age group (default: 25-34) |

**Valid Values:**

*Locations:* Ajapnyak, Arabkir, Kentron, Malatia-Sebastia, Nor Nork

*Venue Types:* restaurant, coffee_house, bar_bistro, bakery_cafe, cafe, etc.

*Age Groups:* 0-17, 18-24, 25-34, 35-44, 45-54, 55+

*Portion Sizes:* small, medium, large

**Response:**
```json
{
  "predicted_price": 1850.50,
  "product_name": "Cappuccino",
  "location": "Kentron",
  "venue_type": "coffee_house",
  "portion_size": "medium",
  "age_group": "25-34",
  "confidence_note": "Prediction based on Random Forest model trained on Yerevan market data"
}
```

---

### Historical Analytics

#### `GET /analytics/historical`

Get historical pricing data for a menu item.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `menu_item` | string | Cappuccino | Item to analyze |
| `location` | string | Kentron | Location filter |

**Response:**
```json
{
  "menu_item": "Cappuccino",
  "location": "Kentron",
  "avg_price": 1650.00,
  "min_price": 1400.00,
  "max_price": 1900.00,
  "units_sold": 1200,
  "market": "Kentron",
  "season": "Winter"
}
```

---

### Price Forecast

#### `GET /analytics/forecast`

Get price forecast for future planning.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `menu_item` | string | Cappuccino | Item to forecast |
| `horizon_days` | integer | 30 | Days ahead (1-365) |

**Response:**
```json
{
  "menu_item": "Cappuccino",
  "recommended_price": 1720.00,
  "confidence": 0.85,
  "horizon_days": 30,
  "trend": "slight_increase"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

**Common Status Codes:**
- `200`: Success
- `201`: Created
- `204`: No Content (successful delete)
- `400`: Bad Request
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error
- `503`: Service Unavailable (ML model not loaded)

---

## Pydantic Models

### RestaurantCreate
```python
class RestaurantCreate(BaseModel):
    name: str                    # Restaurant name (1-255 chars)
    location: str                # District in Yerevan
    venue_type: str              # Type of establishment
    avg_customer_count: int      # Daily customers (≥0)
    rating: float                # Rating (0-5)
    owner_contact: str           # Contact phone
```

### MenuItemCreate
```python
class MenuItemCreate(BaseModel):
    restaurant_id: int           # Parent restaurant (≥1)
    product_name: str            # Product name (1-255 chars)
    category_id: int             # Category ID (≥1)
    base_price: float            # Price in AMD (≥0)
    cost: float                  # Cost in AMD (≥0)
    portion_size: str            # Size description
    available: bool = True       # Availability
```

### PricePredictionResponse
```python
class PricePredictionResponse(BaseModel):
    predicted_price: float       # Predicted price in AMD
    product_name: str            # Input product name
    location: str                # Input location
    venue_type: str              # Input venue type
    portion_size: str            # Input portion size
    age_group: str               # Input age group
    confidence_note: str         # Model info
```

---

## Interactive Documentation

When the API is running, access:
- **Swagger UI:** `http://localhost:8008/docs`
- **ReDoc:** `http://localhost:8008/redoc`
- **OpenAPI JSON:** `http://localhost:8008/openapi.json`
