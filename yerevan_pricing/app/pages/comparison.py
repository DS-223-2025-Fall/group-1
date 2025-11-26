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

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(
    page_title="Comparison",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()
render_nav_row()

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
st.caption("Compare ML-predicted prices with actual restaurant menu prices.")

left, right = st.columns([1.2, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Select for Comparison", divider="gray")
    
    # Restaurant selection
    selected_restaurant_id = st.selectbox(
        "Restaurant",
        options=[r["restaurant_id"] for r in restaurants],
        format_func=lambda x: restaurant_dict.get(x, {}).get("name", f"Restaurant {x}"),
        index=0 if restaurants else None
    )
    
    # Get menu items for selected restaurant
    menu_items = fetch_menu_items(selected_restaurant_id)
    menu_dict = {m["product_id"]: m for m in menu_items}
    
    selected_menu_item_id = st.selectbox(
        "Menu Item",
        options=[m["product_id"] for m in menu_items] if menu_items else [],
        format_func=lambda x: menu_dict.get(x, {}).get("product_name", f"Item {x}"),
        index=0 if menu_items else None
    )
    
    # Get prediction button
    if st.button("Get ML Prediction", type="primary", use_container_width=True):
        if selected_menu_item_id and selected_restaurant_id:
            menu_item = menu_dict.get(selected_menu_item_id, {})
            restaurant = restaurant_dict.get(selected_restaurant_id, {})
            
            prediction = get_prediction(
                product_name=menu_item.get("product_name", "Cappuccino"),
                location=restaurant.get("location", "Kentron"),
                venue_type=restaurant.get("venue_type", "restaurant"),
                portion_size="medium",
                age_group="25-34"
            )
            
            if prediction:
                st.session_state.comparison_prediction = prediction
                st.session_state.comparison_actual = menu_item.get("base_price", 0)
                st.session_state.comparison_item = menu_item.get("product_name", "")
                st.session_state.comparison_restaurant = restaurant.get("name", "")
            else:
                st.error("Failed to get prediction from ML model")
    
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Comparison Result", divider="gray")
    
    if "comparison_prediction" in st.session_state and st.session_state.comparison_prediction:
        predicted_price = st.session_state.comparison_prediction.get("predicted_price", 0)
        actual_price = st.session_state.comparison_actual
        item_name = st.session_state.comparison_item
        restaurant_name = st.session_state.comparison_restaurant
        
        difference = predicted_price - actual_price
        pct_diff = (difference / actual_price * 100) if actual_price > 0 else 0
        
        st.metric("Restaurant Price", f"{actual_price:,.0f} AMD")
        st.metric(
            "ML Predicted Price", 
            f"{predicted_price:,.0f} AMD",
            delta=f"{difference:+,.0f} AMD ({pct_diff:+.1f}%)"
        )
        
        if difference > 0:
            st.warning(f"⚠️ ML suggests {item_name} at {restaurant_name} could be priced {abs(difference):,.0f} AMD higher")
        elif difference < 0:
            st.info(f"ℹ️ ML suggests {item_name} at {restaurant_name} is priced {abs(difference):,.0f} AMD above optimal")
        else:
            st.success(f"✅ {item_name} at {restaurant_name} is optimally priced!")
    else:
        st.metric("Restaurant Price", "--")
        st.metric("ML Predicted Price", "--")
        st.caption("Click 'Get ML Prediction' to compare prices")
    
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# Show market comparison table
st.subheader("Market Price Overview", divider="gray")
if menu_items:
    import pandas as pd
    df = pd.DataFrame(menu_items[:15])
    if not df.empty and 'product_name' in df.columns:
        st.dataframe(
            df[['product_name', 'base_price', 'cost', 'available']].rename(columns={
                'product_name': 'Item',
                'base_price': 'Price (AMD)',
                'cost': 'Cost (AMD)',
                'available': 'Available'
            }),
            use_container_width=True,
            hide_index=True
        )

st.markdown(
    """
    <div class="pill">Tip: Use the Forecasting page to explore different scenarios before comparing.</div>
    """,
    unsafe_allow_html=True,
)
