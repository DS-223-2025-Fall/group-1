import streamlit as st


def render_nav_row(active: str = "home") -> None:
    """
    Show the shared navigation bar and highlight the active page.

    Args:
        active: one of {"home", "forecasting", "comparison"}.
    """
    nav_items = [
        ("home", "app.py", "Home"),
        ("forecasting", "pages/forecasting.py", "Forecasting"),
        ("comparison", "pages/comparison.py", "Comparison"),
    ]
    st.markdown('<div class="nav-bar">', unsafe_allow_html=True)
    cols = st.columns(len(nav_items))
    for col, (key, target, label) in zip(cols, nav_items):
        with col:
            st.markdown(
                f'<div class="nav-pill {"active" if key == active else ""}">',
                unsafe_allow_html=True,
            )
            st.page_link(target, label=label)
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
