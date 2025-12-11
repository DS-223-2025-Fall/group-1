import sys
from pathlib import Path

# Ensure package imports work
APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st
import requests
import os

try:
    from app.components.navigation import render_nav_row
    from app.theme import apply_global_style
except ModuleNotFoundError:
    from components.navigation import render_nav_row
    from theme import apply_global_style

API_URL = os.getenv("API_URL", "http://group1_api:8000")

st.set_page_config(
    page_title="Comparison",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()
render_nav_row(active="comparison")

# Fetch data from API
@st.cache_data(ttl=60)
def fetch_restaurants():
    try:
        response = requests.get(f"{API_URL}/restaurants", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

@st.cache_data(ttl=60)
def fetch_menu_items(restaurant_id=None):
    try:
        params = {"restaurant_id": restaurant_id} if restaurant_id else {}
        response = requests.get(f"{API_URL}/menu-items", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

@st.cache_data(ttl=60)
def fetch_locations():
    try:
        response = requests.get(f"{API_URL}/reference/locations", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return ["Kentron", "Arabkir", "Ajapnyak"]

@st.cache_data(ttl=60)
def fetch_venue_types():
    try:
        response = requests.get(f"{API_URL}/reference/venue-types", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return ["restaurant", "coffee_house", "cafe"]

def get_prediction(product_name, location, venue_type, portion_size, age_group):
    try:
        response = requests.get(
            f"{API_URL}/predict-price",
            params={
                "product_name": product_name,
                "location": location,
                "venue_type": venue_type,
                "portion_size": portion_size,
                "age_group": age_group,
            },
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

restaurants = fetch_restaurants()
restaurant_dict = {r["restaurant_id"]: r for r in restaurants}
locations = fetch_locations()
venue_types = fetch_venue_types()

st.markdown('<div class="page-title">Comparison</div>', unsafe_allow_html=True)
st.caption("Line up a restaurant’s current price with the model’s recommendation and get a friendly nudge on what to do next.")

left, right = st.columns([1.15, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Select a menu entry", divider="gray")
    selected_restaurant_id = st.selectbox(
        "Restaurant",
        options=[r["restaurant_id"] for r in restaurants],
        format_func=lambda x: restaurant_dict.get(x, {}).get("name", f"Restaurant {x}") if restaurants else "",
        index=0 if restaurants else None,
    )

    menu_items = fetch_menu_items(selected_restaurant_id)
    menu_dict = {m["product_id"]: m for m in menu_items}

    selected_menu_item_id = st.selectbox(
        "Menu item",
        options=[m["product_id"] for m in menu_items] if menu_items else [],
        format_func=lambda x: menu_dict.get(x, {}).get("product_name", f"Item {x}"),
        index=0 if menu_items else None,
    )
    st.caption("Pick the dish you want to sanity-check against the predicted range.")

    if st.button("Get ML prediction", use_container_width=True):
        if selected_menu_item_id and selected_restaurant_id:
            menu_item = menu_dict.get(selected_menu_item_id, {})
            restaurant = restaurant_dict.get(selected_restaurant_id, {})
            prediction = get_prediction(
                product_name=menu_item.get("product_name", "Cappuccino"),
                location=restaurant.get("location", "Kentron"),
                venue_type=restaurant.get("venue_type", "restaurant"),
                portion_size="medium",
                age_group="25-34",
            )
            if prediction:
                st.session_state.comparison_prediction = prediction
                st.session_state.comparison_actual = menu_item.get("base_price", 0)
                st.session_state.comparison_item = menu_item.get("product_name", "")
                st.session_state.comparison_restaurant = restaurant.get("name", "")
            else:
                st.error("Failed to get prediction from ML model.")
        else:
            st.warning("Please choose both a restaurant and a menu item.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Comparison panel", divider="gray")
    prediction = st.session_state.get("comparison_prediction")
    if prediction:
        predicted_price = prediction.get("predicted_price", 0)
        actual_price = st.session_state.comparison_actual
        item_name = st.session_state.comparison_item
        restaurant_name = st.session_state.comparison_restaurant
        difference = predicted_price - actual_price
        badge_color = "rgba(155,181,156,0.25)" if difference >= 0 else "rgba(200,107,74,0.25)"
        badge_text = (
            f"Under by {abs(difference):,.0f} AMD"
            if difference >= 0
            else f"Over by {abs(difference):,.0f} AMD"
        )
        comp_cols = st.columns(2)
        with comp_cols[0]:
            st.markdown(
                f"""
                <div class="stat-card card-compact">
                    <div class="label">Current price</div>
                    <div class="value">{actual_price:,.0f} AMD</div>
                    <p>{restaurant_name}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with comp_cols[1]:
            st.markdown(
                f"""
                <div class="stat-card card-compact">
                    <div class="label">Predicted price</div>
                    <div class="value">{predicted_price:,.0f} AMD</div>
                    <p>Model suggestion</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="pill" style="background:{badge_color};border:none;margin-top:0.6rem;">{badge_text}</div>',
            unsafe_allow_html=True,
        )
        if difference > 0:
            st.info(
                f"{item_name} at {restaurant_name} is priced {abs(difference):,.0f} AMD below the recommended range. Consider nudging it upward if demand holds."
            )
        elif difference < 0:
            st.warning(
                f"{item_name} at {restaurant_name} is {abs(difference):,.0f} AMD above the suggested price. Drop slightly if you need volume."
            )
        else:
            st.success(f"{item_name} at {restaurant_name} already sits inside the recommended window.")
    else:
        st.info("Select a dish and run the comparison to see model guidance.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("Market price overview")
search_query = st.text_input("Filter menu items", placeholder="Search by name")
table_items = menu_items or []
if search_query:
    table_items = [item for item in table_items if search_query.lower() in item.get("product_name", "").lower()]

if table_items:
    import pandas as pd

    df = pd.DataFrame(table_items)
    table = df[["product_name", "base_price", "cost", "available"]].rename(
        columns={
            "product_name": "Item",
            "base_price": "Price (AMD)",
            "cost": "Cost (AMD)",
            "available": "Available",
        }
    )
    st.dataframe(table, use_container_width=True, hide_index=True)
else:
    st.caption("No menu items available for this selection yet.")

st.markdown(
    """
    <div class="tip-card">
        <strong>Tip.</strong> Use Forecasting to pressure-test multiple portions or age groups, then return here to see how a single dish stacks up against the wider market.
    </div>
    """,
    unsafe_allow_html=True,
)
