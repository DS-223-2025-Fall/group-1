import streamlit as st
from app.components.navigation import render_nav_row
from app.theme import apply_global_style

st.set_page_config(
    page_title="Comparison",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()
render_nav_row()

RESTAURANT_MENU = {
    "Mayrig": {"Chicken Caesar": 5800, "Cappuccino": 1800, "Margarita Pizza": 5200},
    "Wine Time": {"Cappuccino": 1900, "Quattro Formaggi": 5200, "Brownie": 2500},
    "Tavern Yerevan": {"Beef Steak": 7800, "Hummus Plate": 4300, "Club Sandwich": 4100},
    "Coffeestory": {"Latte": 2000, "Ricotta Croissant": 2500, "Macchiato": 1800},
}

all_menu_items = sorted({item for menu in RESTAURANT_MENU.values() for item in menu})

st.markdown('<div class="page-title">Comparison</div>', unsafe_allow_html=True)
st.caption("Choose a restaurant and compare your predicted price to their current menu price.")

left, right = st.columns([1.2, 1])
with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Set your comparison", divider="gray")
    restaurant = st.selectbox("Restaurant", list(RESTAURANT_MENU.keys()))
    menu_item = st.selectbox("Menu item", all_menu_items, index=all_menu_items.index("Cappuccino"))
    predicted_price = st.number_input(
        "Predicted price (AMD)",
        min_value=0.0,
        max_value=20000.0,
        value=4000.0,
        step=100.0,
    )
    actual_price = RESTAURANT_MENU.get(restaurant, {}).get(menu_item)
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Result", divider="gray")
    if actual_price is None:
        st.caption("No reference price for this item at the selected restaurant.")
    else:
        difference = predicted_price - actual_price
        delta_label = "above" if difference > 0 else "below" if difference < 0 else "aligned with"
        st.metric("Restaurant price", f"{actual_price:,.0f} AMD")
        st.metric("Your predicted price", f"{predicted_price:,.0f} AMD", delta=f"{difference:,.0f} AMD")
        st.caption(
            f"Your prediction is {abs(difference):,.0f} AMD {delta_label} the restaurant's price for {menu_item}."
        )
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

st.markdown(
    """
    <div class="pill">Tip: Use the Forecasting page to refine the prediction before comparing.</div>
    """,
    unsafe_allow_html=True,
)
