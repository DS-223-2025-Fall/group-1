import streamlit as st
from app.theme import apply_global_style

apply_global_style()

st.markdown('<div class="page-title">Historical Data</div>', unsafe_allow_html=True)
st.caption("Placeholder view until pricing performance data is wired up.")

col1, col2 = st.columns([1.2, 1])
with col1:
    st.subheader("Snapshot", divider="gray")
    st.metric("Suggested price (historical)", "--")
    st.metric("Volatility", "--")
    st.metric("Last sync", "—")

with col2:
    st.subheader("Notes", divider="gray")
    st.caption("Hook this page to the analytics API to populate historical pricing trends.")
    st.markdown('<div class="pill">Awaiting data source</div>', unsafe_allow_html=True)
