import sys
from pathlib import Path

# Ensure package imports work whether run via `streamlit run app/app.py`
# or executed directly from the repository root.
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app.components.sidebar import render_sidebar
from app.theme import apply_global_style

st.set_page_config(page_title="Pricing UI", layout="wide")


def main():
    apply_global_style()
    render_sidebar()

    st.markdown('<div class="page-title">Pricing Workspace</div>', unsafe_allow_html=True)
    st.caption("Calm, neutral dashboard for forecasting, history, and setup using native Streamlit components.")

    hero_left, hero_right = st.columns([1.2, 1])
    with hero_left:
        st.markdown(
            """
            <div class="card">
                <div class="pill">Workspace overview</div>
                <h3 style="margin:8px 0 6px;">Plan the next price move</h3>
                <p style="margin:0;">Open Forecasting, adjust scenario inputs, and watch the preview update.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_right:
        st.markdown(
            """
            <div class="card">
                <div class="pill">Quick actions</div>
                <p style="margin:0;">Jump into a page or review the fast stats below.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Navigate", divider="gray")
    grid1, grid2, grid3 = st.columns(3)
    with grid1:
        st.page_link("pages/forecasting.py", label="Forecasting", icon="📈")
        st.caption("Scenario inputs and preview chart.")
    with grid2:
        st.page_link("pages/historical.py", label="Historical", icon="📁")
        st.caption("Historical placeholder until data sync.")
    with grid3:
        st.page_link("pages/settings.py", label="Settings", icon="⚙️")
        st.caption("Backend URL control.")

    st.divider()

    st.subheader("At a glance", divider="gray")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Locations loaded", "5")
        st.caption("Ajapnyak, Arabkir, Kentron, Malatia-Sebastia, Nor Nork")
    with s2:
        st.metric("Menu items", "18")
        st.caption("Cafe staples ready for testing.")
    with s3:
        st.metric("Default horizon", "30 days")
        st.caption("Adjust in Forecasting.")


if __name__ == "__main__":
    main()
