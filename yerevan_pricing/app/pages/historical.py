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
    page_title="Historical",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()
render_nav_row()

st.markdown('<div class="page-title">Historical Data</div>', unsafe_allow_html=True)
st.caption("View historical pricing data and market trends.")

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
def fetch_historical(restaurant_id):
    try:
        response = requests.get(f"{API_URL}/analytics/historical", params={"restaurant_id": restaurant_id}, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

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

restaurants = fetch_restaurants()
restaurant_names = {r["restaurant_id"]: r["name"] for r in restaurants}

# Sidebar filters
with st.sidebar:
    st.subheader("Filters")
    selected_restaurant = st.selectbox(
        "Restaurant",
        options=list(restaurant_names.keys()),
        format_func=lambda x: restaurant_names.get(x, f"Restaurant {x}"),
        index=0 if restaurant_names else None
    )

# Main content
col1, col2 = st.columns([1.2, 1])

historical_data = fetch_historical(selected_restaurant) if selected_restaurant else None

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Historical Snapshot", divider="gray")
    
    if historical_data:
        st.metric("Average Price", f"{historical_data.get('avg_price', 0):,.0f} AMD")
        st.metric("Price Range", f"{historical_data.get('min_price', 0):,.0f} - {historical_data.get('max_price', 0):,.0f} AMD")
        st.metric("Units Sold", f"{historical_data.get('units_sold', 0):,}")
        st.metric("Menu Item", historical_data.get('menu_item', 'N/A'))
        st.metric("Location", historical_data.get('location', 'N/A'))
    else:
        st.metric("Average Price", "--")
        st.metric("Price Range", "--")
        st.metric("Units Sold", "--")
        st.info("Select a restaurant to view historical data")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Menu Items", divider="gray")
    
    menu_items = fetch_menu_items(selected_restaurant)
    if menu_items:
        # Show top 10 items by price
        import pandas as pd
        df = pd.DataFrame(menu_items[:20])
        if not df.empty and 'product_name' in df.columns and 'base_price' in df.columns:
            st.dataframe(
                df[['product_name', 'base_price', 'available']].rename(columns={
                    'product_name': 'Item',
                    'base_price': 'Price (AMD)',
                    'available': 'Available'
                }),
                use_container_width=True,
                hide_index=True
            )
            st.caption(f"Showing {len(df)} of {len(menu_items)} items")
        else:
            st.info("No menu data available")
    else:
        st.info("No menu items found for this restaurant")
    st.markdown("</div>", unsafe_allow_html=True)

# Price distribution chart
st.subheader("Price Distribution", divider="gray")
if menu_items:
    import pandas as pd
    df = pd.DataFrame(menu_items)
    if 'base_price' in df.columns:
        st.bar_chart(df.groupby('product_name')['base_price'].mean().head(15))
