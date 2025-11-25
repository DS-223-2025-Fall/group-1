import streamlit as st
from app.theme import apply_global_style

apply_global_style()

st.markdown('<div class="page-title">Pricing Optimization</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="muted">Welcome to the dashboard. Jump to forecasting to explore price scenarios with the updated inputs.</p>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1.2, 1])
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Get started", divider="gray")
    st.markdown("- Open the Forecasting page in the sidebar.")
    st.markdown("- Pick a location (e.g., Kentron) and menu item from the searchable list.")
    st.markdown("- Adjust age groups, type, and proportion before running a placeholder forecast.")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Quick links", divider="gray")
    st.page_link("pages/forecasting.py", label="Forecasting", icon="📈")
    st.page_link("pages/historical.py", label="Historical", icon="🗂️")
    st.page_link("pages/settings.py", label="Settings", icon="⚙️")
    st.markdown("</div>", unsafe_allow_html=True)
