# API Models

The FastAPI service defines Pydantic schemas in `yerevan_pricing/api/main.py`. Use these models for client validation and documentation.

## Request Models

| Model | Fields | Purpose |
| --- | --- | --- |
| `RestaurantCreate` / `RestaurantUpdate` | `name`, `location`, `venue_type`, `avg_customer_count`, `rating`, `owner_contact` | Create or update restaurant metadata. |
| `MenuItemCreate` / `MenuItemUpdate` | `restaurant_id`, `product_name`, `category_id`, `base_price`, `cost`, `portion_size`, `available` | Manage menu items tied to restaurants. |
| `PricePredictionRequest` | `product_name`, `location`, `venue_type`, `portion_size`, `age_group` | Input payload for `/predict-price`. |

All request models include embedded examples via `ConfigDict.json_schema_extra` for quick reference when building clients.

## Response Models

| Model | Fields | Purpose |
| --- | --- | --- |
| `Restaurant` | includes `restaurant_id` plus `RestaurantCreate` fields | Payload for restaurant CRUD operations. |
| `MenuItem` | includes `product_id` plus `MenuItemCreate` fields | Returned after menu item CRUD calls. |
| `Customer` | `customer_id`, `gender`, `age_group`, `avg_spending`, `visit_frequency` | `/customers` endpoint payload. |
| `PricePredictionResponse` | `predicted_price`, product context fields, `confidence_note` | Response from `/predict-price`. |
| `HistoricalAnalyticsResponse` | `menu_item`, `location`, `avg_price`, `min_price`, `max_price`, `units_sold`, `market`, `season` | Returned by `/analytics/historical`. |
| `ForecastResponse` | `menu_item`, `recommended_price`, `confidence`, `horizon_days`, `trend` | Response from `/forecast-price`. |
| `HealthResponse` | `status`, `version`, `database` | `/health` output. |
| `CategoryResponse` | `category_id`, `category_name` | Response for category lookups. |

## Enums

`main.py` also exposes enums that help keep inputs consistent:

- `LocationEnum` – curated list of Yerevan districts.
- `VenueTypeEnum` – normalized venue names (restaurant, cafe, gastropub, etc.).
- `AgeGroupEnum` – bucketed customer ages (`0-17`, `18-24`, ...).
- `PortionSizeEnum` – portion categories (`small`, `medium`, `large`).

Use these enums in clients to power dropdowns and validation logic, especially within the Streamlit app forms.
