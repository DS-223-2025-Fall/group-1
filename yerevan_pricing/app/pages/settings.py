import streamlit as st
from app.theme import apply_global_style

apply_global_style()

st.markdown('<div class="page-title">Settings</div>', unsafe_allow_html=True)
st.caption("Configure how the UI connects to the backend.")

st.subheader("Backend", divider="gray")
st.text_input("Backend API URL", "http://localhost:8000")
st.caption("Placeholder only; saving is not wired up yet.")
st.markdown('<div class="pill">Edit URL when backend is live</div>', unsafe_allow_html=True)
