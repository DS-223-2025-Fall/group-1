import streamlit as st
from app.theme import apply_global_style


def render_sidebar():
    apply_global_style()
    st.sidebar.title("Pricing UI")
    st.sidebar.markdown(
        "Use the page selector above to jump to Forecasting, Historical, or Settings."
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("Filters will be added when APIs are wired up.")
