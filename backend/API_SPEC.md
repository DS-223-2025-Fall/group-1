## Backend API Specification (Milestone 2 Draft)

This document summarizes the endpoints agreed for Milestone 2. They are intentionally simple so the frontend and PM can validate flows before real database integration.

### General Notes
- **Base URL**: `http://localhost:8000`
- **Format**: JSON only
- **Auth**: Not enforced during Milestone 2 dummy phase
- **Errors**: `{"detail": "message"}` with relevant HTTP status

### Health
| Method | Path    | Description                |
|--------|---------|----------------------------|
| GET    | /health | Returns `{ "status": "ok" }` |

### Restaurants
| Method | Path                     | Description                         |
|--------|--------------------------|-------------------------------------|
| GET    | /restaurants             | List restaurants (filters optional) |
| GET    | /restaurants/{id}        | Retrieve single restaurant          |
| POST   | /restaurants             | Create new restaurant (dummy store) |
| PUT    | /restaurants/{id}        | Update restaurant                   |
| DELETE | /restaurants/{id}        | Remove restaurant                   |

**Restaurant payload**
```json
{
  "name": "Gallia",
  "location": "Kentron",
  "type": "restaurant",
  "avg_customer_count": 162,
  "rating": 4.16,
  "owner_contact": "+374-81-210268"
}
```

### Menu Items
| Method | Path                    | Description                         |
|--------|-------------------------|-------------------------------------|
| GET    | /menu-items             | List menu items                     |
| GET    | /menu-items/{id}        | Retrieve menu item                  |
| POST   | /menu-items             | Create menu item (dummy)            |
| PUT    | /menu-items/{id}        | Update menu item                    |
| DELETE | /menu-items/{id}        | Remove menu item                    |

**Menu item payload**
```json
{
  "restaurant_id": 1,
  "product_name": "Chicken Sandwich",
  "category_id": 11,
  "base_price": 3800,
  "cost": 1900,
  "portion_size": "200g",
  "available": true
}
```

### Customers (read-only initial pass)
| Method | Path          | Description          |
|--------|---------------|----------------------|
| GET    | /customers    | List customers       |
| GET    | /customers/{id} | Retrieve customer |

### Analytics placeholders
| Method | Path                   | Description                                      |
|--------|------------------------|--------------------------------------------------|
| GET    | /analytics/historical  | Returns stubbed metrics for historical analysis |
| GET    | /analytics/forecast    | Returns stubbed forecast output                 |

**Historical sample response**
```json
{
  "menu_item": "Americano",
  "avg_price": 1800,
  "units_sold": 1200,
  "market": "Kentron",
  "season": "Winter"
}
```

**Forecast sample response**
```json
{
  "menu_item": "Americano",
  "recommended_price": 1900,
  "confidence": 0.78,
  "horizon_days": 30
}
```
