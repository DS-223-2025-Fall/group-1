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
    page_title="Home",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()
render_nav_row()

# Fetch stats from API
@st.cache_data(ttl=60)
def fetch_stats():
    stats = {
        "restaurants": 0,
        "menu_items": 0,
        "categories": 0,
        "locations": 0,
        "api_status": "offline"
    }
    try:
        # Health check
        health = requests.get(f"{API_URL}/health", timeout=5)
        if health.status_code == 200:
            stats["api_status"] = "online"
        
        # Restaurants count
        restaurants = requests.get(f"{API_URL}/restaurants", timeout=5)
        if restaurants.status_code == 200:
            stats["restaurants"] = len(restaurants.json())
        
        # Menu items count
        menu_items = requests.get(f"{API_URL}/menu-items", timeout=5)
        if menu_items.status_code == 200:
            stats["menu_items"] = len(menu_items.json())
        
        # Categories count
        categories = requests.get(f"{API_URL}/categories", timeout=5)
        if categories.status_code == 200:
            stats["categories"] = len(categories.json())
        
        # Locations count
        locations = requests.get(f"{API_URL}/reference/locations", timeout=5)
        if locations.status_code == 200:
            stats["locations"] = len(locations.json())
    except:
        pass
    return stats

stats = fetch_stats()

st.markdown('<div class="page-title">Home</div>', unsafe_allow_html=True)
st.caption("Welcome to the Yerevan Dynamic Pricing Dashboard")

# API Status
if stats["api_status"] == "online":
    st.success("✅ Backend API is online and connected")
else:
    st.error("❌ Backend API is offline")

# Stats row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Restaurants", stats["restaurants"])
with col2:
    st.metric("Menu Items", f"{stats['menu_items']:,}")
with col3:
    st.metric("Categories", stats["categories"])
with col4:
    st.metric("Locations", stats["locations"])

st.divider()

# Quick links
st.subheader("Quick Actions", divider="gray")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📊 Forecasting")
    st.caption("Predict optimal prices using ML")
    st.page_link("pages/forecasting.py", label="Go to Forecasting →")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📈 Historical")
    st.caption("View historical pricing data")
    st.page_link("pages/historical.py", label="Go to Historical →")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ⚖️ Comparison")
    st.caption("Compare predicted vs actual prices")
    st.page_link("pages/comparison.py", label="Go to Comparison →")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="pill">Tip: The ML model uses CatBoost trained on Yerevan restaurant data for accurate predictions.</div>
    """,
    unsafe_allow_html=True,
)
