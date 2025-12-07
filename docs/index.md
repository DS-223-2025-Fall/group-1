# Yerevan Dynamic Pricing Platform

Welcome to the documentation portal for the DS223 Milestone 3 project. The team built an end-to-end platform that predicts and forecasts menu item prices for Yerevan cafés and restaurants.

## Project Scope

- **Objective:** Deliver a production-ready workflow that ingests data, trains a CatBoost model, exposes API endpoints, and serves results through a Streamlit UI.
- **Stakeholders:** Product manager, database, backend, frontend, and data science contributors collaborating in parallel feature branches.

## Architecture Snapshot

1. **Database**  
   Finalized ERD and table definitions to support restaurant and menu datasets.
2. **Data Science**  
   Cleaned data, trained the CatBoost regression model, and exported pricing + forecasting artifacts.
3. **Backend (FastAPI)**  
   Implemented `/predict-price` and `/forecast-price` endpoints that wrap the model outputs.
4. **Frontend (Streamlit)**  
   Provides dark-green themed dashboards for prediction and forecasting flows.

## Getting Started

1. Clone the repository and install project dependencies specified within each service directory.
2. Review the ERD located in `docs/erd/ERD.pdf` to understand database relationships.
3. Explore the analytics code under `yerevan_pricing/analytics` to inspect the CatBoost pipeline and prediction scripts.
4. Run the FastAPI backend, then open the Streamlit UI to interact with live predictions.

## Next Steps

- Extend the docs site with service-specific guides (ETL, API contracts, UI walkthroughs).
- Add usage examples for `/predict-price` and `/forecast-price` responses.
- Include deployment instructions (Docker Compose, hosting targets) once finalized.
