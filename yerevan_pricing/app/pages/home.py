import sys
from pathlib import Path

# Ensure package imports work
APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import streamlit as st

try:
    from app.components.navigation import render_nav_row
    from app.theme import apply_global_style
    from app.app import fetch_stats, render_home_content
except ModuleNotFoundError:
    from components.navigation import render_nav_row
    from theme import apply_global_style
    from app import fetch_stats, render_home_content

st.set_page_config(
    page_title="Home",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()
render_nav_row(active="home")
stats = fetch_stats()
render_home_content(stats)
