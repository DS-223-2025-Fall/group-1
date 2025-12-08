# Streamlit App

The customer-facing dashboard lives in `yerevan_pricing/app` and wraps the FastAPI endpoints to provide prediction and forecasting experiences for PM demos.

## Components

- `app.py` – Streamlit entry point registering global layout and routing to page modules.
- `pages/` – multi-page experience (prediction, forecasting, analytics, onboarding).
- `components/` – reusable widgets for forms, metric cards, and charts.
- `theme.py` – shared colors/spacing that implement the dark green palette promised to PM.
- `background photo_1.jpg` – hero image displayed on landing sections.
- `requirements.txt` – Streamlit + plotting dependencies mirrored in Dockerfile.

## Running Locally

```bash
cd yerevan_pricing/app
streamlit run app.py --server.port 8501
```

Ensure the FastAPI backend is available on the expected host/port. Adjust environment variables in `app.py` if you proxy requests through docker-compose or tunnels.

## Integration Points

1. Prediction forms call `/predict-price` and expect payloads defined in `yerevan_pricing/api/main.py`.
2. Forecasting visualizations consume `/forecast-price` responses and render confidence intervals.
3. Historical cards rely on the analytics endpoint once it is wired to real database queries.

## UX To-Dos

- Add loading states + skeletons to the form submissions.
- Surface CatBoost confidence notes directly within the price recommendation cards.
- Document Streamlit session state usage inside this page for future contributors.
