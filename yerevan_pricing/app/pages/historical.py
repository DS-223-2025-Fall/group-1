import streamlit as st
from app.components.navigation import render_nav_row
from app.theme import apply_global_style

st.set_page_config(
    page_title="Historical",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()
render_nav_row()

st.markdown('<div class="page-title">Historical Data</div>', unsafe_allow_html=True)
st.caption("Placeholder view until pricing performance data is wired up.")

col1, col2 = st.columns([1.2, 1])
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Snapshot", divider="gray")
    st.metric("Suggested price (historical)", "--")
    st.metric("Volatility", "--")
    st.metric("Last sync", "Waiting for data")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Notes", divider="gray")
    st.caption("Hook this page to the analytics API to populate historical pricing trends.")
    st.markdown('<div class="pill">Awaiting data source</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
