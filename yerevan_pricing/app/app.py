import sys
from pathlib import Path

# Ensure package imports work whether run via `streamlit run app/app.py`
# or executed directly from the repository root.
APP_DIR = Path(__file__).resolve().parent


def _detect_project_root(start: Path) -> Path:
    """Return the directory that contains shared assets like /images."""
    candidates = [start, start.parent, start.parent.parent]
    for candidate in candidates:
        if (candidate / "images").exists():
            return candidate
    return start


PROJECT_ROOT = _detect_project_root(APP_DIR)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st
import requests
import os

try:
    from app.components.navigation import render_nav_row
    from app.theme import apply_global_style
except ModuleNotFoundError:
    from components.navigation import render_nav_row
    from theme import apply_global_style

API_URL = os.getenv("API_URL", "http://group1_api:8000")
IMAGES_DIR = PROJECT_ROOT / "images"

HOME_PAGE_STYLE = """
<style>
/* Home-specific layout and cards; global colors come from theme.py */
.home-hero {
    padding: 2.8rem;
    border-radius: 32px;
    background: rgba(18,19,27,0.78);  /* was 0.92 */
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 28px 70px rgba(0,0,0,0.45);
}

/* Eyebrow + title */
.hero-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.2em;
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
    color: rgba(255,255,255,0.7);
}
.hero-title {
    font-family: 'YerevanDisplay', 'Georgia', serif;
    font-size: 52px;
    margin: 0 0 0.6rem 0;
    color: #f4e7d3;
}
.hero-subtitle {
    font-size: 1.1rem;
    line-height: 1.6;
    color: rgba(244,231,211,0.9);
    max-width: 680px;
}

/* Hero CTA layout */
.hero-cta {
    margin-top: 1.4rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem;
}
.hero-cta > div,
.hero-cta .hero-anchor-wrapper {
    flex: 1 1 220px;
}

/* Anchor wrapper for the view coverage link */
.hero-anchor-wrapper {
    display: inline-flex;
}
.hero-anchor-wrapper a {
    width: 100%;
    text-align: center;
    justify-content: center;
}

/* Section cards */
.section {
    background: rgba(15,17,24,0.70);  /* was 0.9 */
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.05);
    padding: 2rem;
    margin-top: 2rem;
}
.section h2 {
    margin-top: 0;
    color: #f4e7d3;
}

/* Grids */
.steps-grid, .audience-grid, .stat-row, .preview-grid {
    display: grid;
    gap: 1rem;
}
.steps-grid {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.step-card, .audience-card {
    background: rgba(18,20,30,0.78);   /* was 0.95 */
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    padding: 1.2rem 1.4rem;
}
.step-card h3, .audience-card h3 {
    margin-bottom: 0.4rem;
    font-size: 1.05rem;
}

/* Stats row */
.stat-row {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}
.stat-card {
    background: rgba(12,14,20,0.72);   /* was 0.9 */
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.07);
    padding: 1.2rem;
}
.stat-card .value {
    font-size: 2rem;
    font-weight: 700;
    color: #f4e7d3;
}
.stat-card .label {
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    color: rgba(255,255,255,0.7);
}

/* (Optional) preview cards if you add screenshots later */
.preview-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}
.preview-card {
    background: rgba(12,14,20,0.72);   /* was 0.9 */
    border-radius: 18px;
    padding: 0.8rem;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 18px 35px rgba(0,0,0,0.4);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.preview-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 25px 45px rgba(0,0,0,0.5);
}
.preview-card img {
    border-radius: 12px;
}
.preview-card p {
    margin: 0.6rem 0 0 0;
    font-size: 0.9rem;
    color: rgba(244,231,211,0.9);
}

/* About box */
.about-card {
    background: rgba(12,14,20,0.70);   /* was 0.85 */
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    padding: 1.2rem 1.5rem;
    font-size: 0.95rem;
    color: rgba(244,231,211,0.9);
}

@media (max-width: 768px) {
    .home-hero {
        padding: 1.8rem;
    }
}
</style>
"""


@st.cache_data(ttl=60)
def fetch_stats():
    stats = {"restaurants": 0, "menu_items": 0, "categories": 0}
    try:
        restaurants = requests.get(f"{API_URL}/restaurants", timeout=5)
        if restaurants.status_code == 200:
            stats["restaurants"] = len(restaurants.json())
        
        menu_items = requests.get(f"{API_URL}/reference/menu-item-names", timeout=5)
        if menu_items.status_code == 200:
            stats["menu_items"] = len(menu_items.json())
        
        categories = requests.get(f"{API_URL}/categories", timeout=5)
        if categories.status_code == 200:
            stats["categories"] = len(categories.json())
    except:
        pass
    return stats


def render_home_content(stats: dict) -> None:
    """Primary hero and supporting layout for the landing experience."""
    st.markdown(HOME_PAGE_STYLE, unsafe_allow_html=True)
    st.markdown(
        """
        <section class="home-hero">
            <div class="hero-eyebrow">Pricing intelligence for Yerevan</div>
            <div class="hero-title">Yerevan Dynamic Pricing</div>
            <p class="hero-subtitle">
            Predict, forecast, and compare menu prices for every Yerevan café and restaurant
            using market data, historical trends, and customer segments.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="hero-cta">', unsafe_allow_html=True)
    btn_cols = st.columns(3)
    with btn_cols[0]:
        st.page_link("pages/forecasting.py", label="Start forecasting →")
    with btn_cols[1]:
        st.page_link("pages/comparison.py", label="Compare with market")
    with btn_cols[2]:
        st.markdown('<a class="hero-anchor" href="#coverage">View menu coverage</a>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("Use real Yerevan market data to set confident menu prices.")

    # How it works
    st.markdown(
        """
        <section class="section">
            <h2>How it works</h2>
            <div class="steps-grid">
                <div class="step-card">
                    <h3>1. Connect menu & context</h3>
                    <p>Pick the menu item, district, venue type, portion, and age group to feed the /predict-price model.</p>
                </div>
                <div class="step-card">
                    <h3>2. Get ML price & forecast</h3>
                    <p>Receive a CatBoost recommendation plus a price path via /forecast-price for up to 365 days.</p>
                </div>
                <div class="step-card">
                    <h3>3. Compare & export decisions</h3>
                    <p>Contrast with market menus, capture snapshots, and download a session ledger for your cafe.</p>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # At a glance stats
    st.markdown('<a id="coverage"></a>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <section class="section">
            <h2>At a glance</h2>
            <div class="stat-row">
                <div class="stat-card">
                    <div class="label">Restaurants tracked</div>
                    <div class="value">{stats['restaurants']}+</div>
                    <p>Coverage across central Yerevan.</p>
                </div>
                <div class="stat-card">
                    <div class="label">Menu items</div>
                    <div class="value">{stats['menu_items']}</div>
                    <p>Ready for prediction and comparison.</p>
                </div>
                <div class="stat-card">
                    <div class="label">Forecast horizon</div>
                    <div class="value">Up to 365 days</div>
                    <p>Adjust the time window inside Forecasting.</p>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Who is this for
    st.markdown(
        """
        <section class="section">
            <h2>Who uses Yerevan Dynamic Pricing?</h2>
            <div class="audience-grid">
                <div class="audience-card">
                    <h3>Restaurant owners</h3>
                    <p>Set fair prices that protect margins while staying aligned with neighborhood expectations.</p>
                </div>
                <div class="audience-card">
                    <h3>Café managers</h3>
                    <p>Adjust espresso, brunch, or pastry menus when customer segments shift.</p>
                </div>
                <div class="audience-card">
                    <h3>Chains & marketing teams</h3>
                    <p>Compare multiple locations, plan promotions, and share downloadable menu ledgers.</p>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # About section
    st.markdown(
        """
        <section class="section">
            <h2>About the project</h2>
            <div class="about-card">
                DS223 Marketing Analytics project built with PostgreSQL, ETL, CatBoost, FastAPI, Streamlit, and Docker.
                Designed to help Yerevan’s cafés and restaurants experiment with data-driven pricing before they print tomorrow’s menu.
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="Yerevan Dynamic Pricing",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_global_style()
    render_nav_row(active="home")
    stats = fetch_stats()
    render_home_content(stats)


if __name__ == "__main__":
    main()
