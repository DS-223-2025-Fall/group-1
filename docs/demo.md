# Demo

This page provides a walkthrough of the Yerevan Dynamic Pricing Platform capabilities.

---

## 🎬 Platform Overview

The platform consists of several integrated components working together to deliver dynamic pricing insights.

### Running the Demo

To run the complete platform locally:

```bash
cd yerevan_pricing
docker-compose up --build
```

This will start:

- **PostgreSQL Database** - Port 5432
- **FastAPI Backend** - Port 8008
- **Streamlit Frontend** - Port 8501
- **PgAdmin** - Port 5050

---

## 📊 Dashboard Features

### Home Page
The main dashboard provides an overview of the pricing platform with key metrics and navigation.

### Price Prediction
Enter restaurant details, menu category, and other parameters to receive ML-powered price predictions.

**Example Parameters:**

| Parameter | Example Value |
|-----------|---------------|
| Product Name | Cappuccino |
| Location | Kentron |
| Venue Type | coffee_house |
| Portion Size | medium |
| Age Group | 25-34 |

### Price Forecasting
View future price trends based on historical data and seasonal patterns.

### Historical Analysis
Explore past pricing data with interactive charts and filters:

- Filter by date range
- Group by restaurant, category, or market
- Export data for further analysis

### Market Comparison
Compare prices across different markets and identify competitive positioning opportunities.

---

## 🔌 API Demo

### Predict Price Endpoint

```bash
curl -X GET "http://localhost:8008/predict-price?product_name=Cappuccino&location=Kentron&venue_type=coffee_house&portion_size=medium&age_group=25-34"
```

**Response:**
```json
{
  "predicted_price": 1850.50,
  "product_name": "Cappuccino",
  "location": "Kentron",
  "venue_type": "coffee_house",
  "portion_size": "medium",
  "age_group": "25-34",
  "confidence_note": "Prediction based on CatBoost model trained on Yerevan market data"
}
```

### Forecast Endpoint

```bash
curl -X GET "http://localhost:8008/analytics/forecast?menu_item=Cappuccino&horizon_days=30"
```

**Response:**
```json
{
  "menu_item": "Cappuccino",
  "recommended_price": 1920.00,
  "confidence": 0.92,
  "horizon_days": 30,
  "trend": "slight_increase"
}
```

### Historical Analytics Endpoint

```bash
curl -X GET "http://localhost:8008/analytics/historical?menu_item=Cappuccino&location=Kentron"
```

---

## 🗄️ Data Model

The platform uses a star schema with the following tables:

### Dimension Tables
| Table | Description |
|-------|-------------|
| `dim_restaurant` | Restaurant information |
| `dim_category` | Menu categories |
| `dim_menu_item` | Individual menu items |
| `dim_customer` | Customer segments |
| `dim_season` | Seasonal attributes |
| `dim_market` | Market information |
| `dim_time` | Time dimension |

### Fact Tables
| Table | Description |
|-------|-------------|
| `fact_sales` | Sales transactions |
| `fact_market_prices` | Market price records |

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection failed | Ensure PostgreSQL container is running |
| API returns 500 error | Check model files exist in `api/model/` |
| Streamlit not loading | Verify port 8501 is not in use |

For more detailed documentation, see:

- [ETL Pipeline](etl.md)
- [API Specification](api.md)
- [Application Guide](app.md)
