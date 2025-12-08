import streamlit as st


def render_nav_row():
    """Show top-level navigation buttons since the sidebar is hidden."""
    st.markdown('<div class="nav-row">', unsafe_allow_html=True)
    nav1, nav2, nav3, nav4 = st.columns(4)
    with nav1:
        st.page_link("app.py", label="Home")
    with nav2:
        st.page_link("pages/forecasting.py", label="Forecasting")
    with nav3:
        st.page_link("pages/historical.py", label="Historical")
    with nav4:
        st.page_link("pages/comparison.py", label="Comparison")
    st.markdown("</div>", unsafe_allow_html=True)
