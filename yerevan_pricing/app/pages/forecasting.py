import streamlit as st
from app.components.navigation import render_nav_row
from app.theme import apply_global_style

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
AGE_GROUPS = ["0-17", "18-24", "35-44", "55+"]
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
        st.selectbox("Location", LOCATIONS, index=0, key="forecast_location")
        st.selectbox(
            "Menu item",
            MENU_ITEMS,
            index=0,
            key="forecast_menu_item",
            help="Start typing to quickly search the list.",
        )
        st.selectbox("Age group", AGE_GROUPS, key="forecast_age_group")
        st.selectbox("Type", CAFE_TYPES, key="forecast_cafe_type")
        st.selectbox(
            "Proportion",
            PROPORTIONS,
            index=1,
            key="forecast_proportion",
            help="Pick the serving size that fits this scenario.",
        )
        st.number_input(
            "Forecast horizon (days)",
            min_value=1,
            max_value=365,
            value=30,
            step=1,
            key="forecast_horizon",
        )
        st.form_submit_button("Run forecast", use_container_width=True, key="run_forecast_btn")
    with st.expander("Forecast", expanded=False):
        st.caption("Now you can forecast the predicted value for as many days as you want.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Forecast snapshot", divider="gray")
    st.metric("Suggested price", "--")
    st.metric("Confidence window", "--")
    st.progress(0.55, text="Guardrail: holding margin")
    st.line_chart({"Price": [12.2, 12.4, 12.5, 12.7, 12.75, 12.9, 13.0]}, height=190)
    st.caption("Visuals are placeholders until the forecasting service is connected.")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

chips1, chips2, chips3 = st.columns(3)
with chips1:
    st.markdown('<div class="pill">Auto-apply margin checks</div>', unsafe_allow_html=True)
with chips2:
    st.markdown('<div class="pill">Menu coverage: 18 items</div>', unsafe_allow_html=True)
with chips3:
    st.markdown('<div class="pill">Streamlit-native UI</div>', unsafe_allow_html=True)
