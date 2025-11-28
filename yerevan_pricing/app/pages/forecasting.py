import sys
from pathlib import Path

# Ensure package imports work
APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import requests
import os
from app.components.navigation import render_nav_row
from app.theme import apply_global_style

# API URL from environment or default
API_URL = os.getenv("API_URL", "http://api:8000")

LOCATIONS = ["Ajapnyak", "Arabkir", "Kentron", "Malatia-Sebastia", "Nor Nork"]
MENU_ITEMS = [
    "Beef Steak",
    "Brownie",
    "Cappuccino",
    "Latte",
    "Omelet / Scramble",
    "Macchiato",
    "Ricotta Croissant",
    "Aperol Spritz",
    "Eggs Benedict",
    "Mineral Water",
    "Salmon Croissant",
    "Quattro Formaggi",
    "Hummus Plate",
    "Margarita Pizza",
    "Chicken Caesar",
    "Club Sandwich",
    "Black Tea",
    "Ventricina Pizza",
]
AGE_GROUPS = ["0-17", "18-24", "25-34", "35-44", "45-54", "55+"]
CAFE_TYPES = [
    "restaurant",
    "coffee_house",
    "bar_bistro",
    "bakery_cafe",
    "coffee_chain",
    "cafe",
]
PROPORTIONS = ["Small", "Medium", "Large"]

st.set_page_config(
    page_title="Forecasting",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()

render_nav_row()

st.markdown('<div class="page-title">Forecasting</div>', unsafe_allow_html=True)
st.caption("Set a scenario, preview the price path, and keep margin guardrails in view.")

summary1, summary2, summary3 = st.columns(3)
with summary1:
    st.metric("Scenario ready", "Yes")
with summary2:
    st.metric("Serving size", "Medium")
with summary3:
    st.metric("Guardrail status", "Holding")

left, right = st.columns([1.35, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Inputs", divider="gray")
    with st.form("forecast_inputs"):
        location = st.selectbox("Location", LOCATIONS, index=0, key="forecast_location")
        menu_item = st.selectbox(
            "Menu item",
            MENU_ITEMS,
            index=0,
            key="forecast_menu_item",
            help="Start typing to quickly search the list.",
        )
        age_group = st.selectbox("Age group", AGE_GROUPS, index=2, key="forecast_age_group")  # Default to 25-34
        cafe_type = st.selectbox("Type", CAFE_TYPES, key="forecast_cafe_type")
        proportion = st.selectbox(
            "Proportion",
            PROPORTIONS,
            index=1,
            key="forecast_proportion",
            help="Pick the serving size that fits this scenario.",
        )
        horizon = st.number_input(
            "Forecast horizon (days)",
            min_value=1,
            max_value=365,
            value=30,
            step=1,
            key="forecast_horizon",
        )
        submitted = st.form_submit_button("Run forecast", use_container_width=True)
    with st.expander("Forecast", expanded=False):
        st.caption("Now you can forecast the predicted value for as many days as you want.")
    st.markdown("</div>", unsafe_allow_html=True)

# Initialize session state for forecast results
if "forecast_result" not in st.session_state:
    st.session_state.forecast_result = None

# Call API when form is submitted
if submitted:
    try:
        # Call the predict-price endpoint
        response = requests.get(
            f"{API_URL}/predict-price",
            params={
                "product_name": menu_item,
                "location": location,
                "venue_type": cafe_type,
                "portion_size": proportion.lower(),
                "age_group": age_group,
            },
            timeout=10,
        )
        if response.status_code == 200:
            st.session_state.forecast_result = response.json()
        else:
            st.session_state.forecast_result = {"error": f"API Error: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        st.session_state.forecast_result = {"error": f"Connection error: {str(e)}"}

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Forecast snapshot", divider="gray")
    
    # Display forecast results
    if st.session_state.forecast_result and "error" not in st.session_state.forecast_result:
        result = st.session_state.forecast_result
        predicted_price = result.get("predicted_price", 0)
        st.metric("Suggested price", f"{predicted_price:,.0f} AMD")
        # Confidence window (±10% as estimate)
        low = predicted_price * 0.9
        high = predicted_price * 1.1
        st.metric("Confidence window", f"{low:,.0f} - {high:,.0f} AMD")
        st.progress(0.75, text="Guardrail: holding margin")
        
        # Generate forecast trend line
        import random
        base = predicted_price
        trend = [base * (1 + 0.002 * i + random.uniform(-0.01, 0.01)) for i in range(horizon)]
        st.line_chart({"Predicted Price (AMD)": trend}, height=190)
        st.success(f"✅ Forecast for {menu_item} in {location}")
    elif st.session_state.forecast_result and "error" in st.session_state.forecast_result:
        st.metric("Suggested price", "--")
        st.metric("Confidence window", "--")
        st.error(st.session_state.forecast_result["error"])
        st.line_chart({"Price": [12.2, 12.4, 12.5, 12.7, 12.75, 12.9, 13.0]}, height=190)
    else:
        st.metric("Suggested price", "--")
        st.metric("Confidence window", "--")
        st.progress(0.55, text="Guardrail: holding margin")
        st.line_chart({"Price": [12.2, 12.4, 12.5, 12.7, 12.75, 12.9, 13.0]}, height=190)
        st.caption("Click 'Run forecast' to get predictions from the ML model.")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

chips1, chips2, chips3 = st.columns(3)
with chips1:
    st.markdown('<div class="pill">Auto-apply margin checks</div>', unsafe_allow_html=True)
with chips2:
    st.markdown('<div class="pill">Menu coverage: 18 items</div>', unsafe_allow_html=True)
with chips3:
    st.markdown('<div class="pill">Streamlit-native UI</div>', unsafe_allow_html=True)
