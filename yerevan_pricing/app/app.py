import sys
from pathlib import Path

# Ensure package imports work whether run via `streamlit run app/app.py`
# or executed directly from the repository root.
APP_DIR = Path(__file__).resolve().parent
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
    page_title="Yerevan Dynamic Pricing",
    layout="wide",
    initial_sidebar_state="collapsed",
)

@st.cache_data(ttl=60)
def fetch_stats():
    stats = {"restaurants": 0, "menu_items": 0, "categories": 0}
    try:
        restaurants = requests.get(f"{API_URL}/restaurants", timeout=5)
        if restaurants.status_code == 200:
            stats["restaurants"] = len(restaurants.json())
        
        menu_items = requests.get(f"{API_URL}/reference/menu-item-names", timeout=5)
        if menu_items.status_code == 200:
            stats["menu_items"] = len(menu_items.json())
        
        categories = requests.get(f"{API_URL}/categories", timeout=5)
        if categories.status_code == 200:
            stats["categories"] = len(categories.json())
    except:
        pass
    return stats


def main():
    apply_global_style()
    
    stats = fetch_stats()

    st.markdown('<div class="page-title">Yerevan Dynamic Pricing</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="card">
            <p class="lede">
            The Yerevan Dynamic Pricing App helps restaurants, cafes, and food businesses set smarter menu prices using real market data.
            Powered by menus from {stats['restaurants']}+ Yerevan restaurants, the application predicts optimal prices for any menu item and provides a clear comparison
            between your predicted price and the actual prices in the market. You can also forecast future price trends, allowing you to plan adjustments,
            stay competitive, and make data-driven pricing decisions with confidence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Jump to a page")
    render_nav_row()

    hero_left, hero_right = st.columns([1.2, 1])
    with hero_left:
        st.markdown(
            """
            <div class="card">
                <div class="pill">Start here</div>
                <h3 style="margin:8px 0 6px;">Plan the next price move</h3>
                <p style="margin:0;">Use forecasting to predict optimal menu prices and keep pace with Yerevan's market.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link("pages/forecasting.py", label="Get Started")
    with hero_right:
        st.markdown(
            """
            <div class="card">
                <div class="pill">Why it matters</div>
                <p style="margin:0;">Predicted prices meet real menu data so you can compare, adjust, and keep margins healthy.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("At a glance", divider="gray")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Restaurants tracked", f"{stats['restaurants']}+")
        st.caption("Coverage across central Yerevan.")
    with s2:
        st.metric("Menu items", f"{stats['menu_items']}")
        st.caption("Ready for prediction and comparison.")
    with s3:
        st.metric("Forecast horizon", "Up to 365 days")
        st.caption("Adjust in Forecasting.")


if __name__ == "__main__":
    main()
