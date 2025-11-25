import streamlit as st
from app.components.navigation import render_nav_row
from app.theme import apply_global_style

st.set_page_config(
    page_title="Home",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()
render_nav_row()

st.markdown('<div class="page-title">Home</div>', unsafe_allow_html=True)
st.caption("Use the buttons above to move between Home, Forecasting, Historical, and Comparison.")

st.markdown(
    """
    <div class="card">
        <div class="pill">Tip</div>
        <p style="margin:8px 0 0;">The primary home page lives at app.py. Use this page if you land here directly.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
