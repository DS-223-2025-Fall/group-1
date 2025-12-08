# Yerevan Dynamic Pricing Platform

Welcome to the documentation portal for the DS223 Marketing Analytics project. The team built an end-to-end platform that predicts and forecasts menu item prices for Yerevan cafés and restaurants.

---

## 🎯 Problem

The food service industry in Yerevan faces significant challenges in **menu pricing optimization**:

- **Market Volatility:** Ingredient costs and market conditions fluctuate frequently, making static pricing strategies ineffective.
- **Competitive Pressure:** Restaurants struggle to set prices that are competitive yet profitable without real-time market intelligence.
- **Data Fragmentation:** Pricing decisions are often made without comprehensive analysis of historical sales, seasonal trends, and customer segments.
- **Manual Processes:** Traditional pricing methods are time-consuming and prone to human error, leading to lost revenue opportunities.

---

## 💡 Solution

Our **Yerevan Dynamic Pricing Platform** addresses these challenges through a comprehensive, data-driven approach:

### Architecture Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | PostgreSQL | Star schema with fact/dimension tables for sales and market data |
| **ETL Pipeline** | Python | Automated data extraction, transformation, and loading |
| **ML Models** | CatBoost | Price prediction and forecasting algorithms |
| **Backend API** | FastAPI | RESTful endpoints for predictions (`/predict-price`, `/forecast-price`) |
| **Frontend** | Streamlit | Interactive dashboards for visualization and analysis |
| **Deployment** | Docker Compose | Containerized microservices architecture |

### Key Features

- **📊 Price Prediction:** ML-powered predictions based on restaurant, category, season, and customer segment
- **📈 Forecasting:** Time-series forecasting for future price trends
- **🔍 Historical Analysis:** Explore historical pricing patterns and trends
- **📉 Market Comparison:** Compare prices across different markets and competitors
- **⚙️ Customizable Parameters:** Flexible filtering by restaurant, category, and time period

---

## ✅ Expected Outcomes

By implementing this platform, stakeholders can expect:

| Outcome | Description |
|---------|-------------|
| **Optimized Pricing** | Data-driven price recommendations that maximize revenue while maintaining competitiveness |
| **Reduced Manual Effort** | Automated analysis replaces time-consuming manual pricing reviews |
| **Better Decision Making** | Real-time insights enable faster, more informed pricing decisions |
| **Increased Profitability** | Dynamic pricing strategies that adapt to market conditions |
| **Competitive Advantage** | Stay ahead of competitors with predictive analytics |

### Success Metrics

- 🎯 **Model Accuracy:** CatBoost model achieves reliable price predictions
- ⚡ **API Response Time:** Sub-second predictions via FastAPI endpoints
- 📱 **User Adoption:** Intuitive Streamlit interface for non-technical users
- 🔄 **Scalability:** Containerized architecture supports growth

---

## 🚀 Getting Started

1. Clone the repository and install project dependencies specified within each service directory.
2. Review the ERD located in `docs/erd/ERD.pdf` to understand database relationships.
3. Explore the analytics code under `yerevan_pricing/analytics` to inspect the CatBoost pipeline and prediction scripts.
4. Run the FastAPI backend, then open the Streamlit UI to interact with live predictions.

```bash
# Quick start with Docker
cd yerevan_pricing
docker-compose up --build
```

---

## 📚 Documentation Sections

| Section | Description |
|---------|-------------|
| [Demo](demo.md) | Live demonstration and usage examples |
| [ETL](etl.md) | Data pipeline documentation |
| [API](api.md) | FastAPI endpoints and specifications |
| [APP](app.md) | Streamlit frontend guide |
| [API Models](api_models.md) | ML model details and parameters |
