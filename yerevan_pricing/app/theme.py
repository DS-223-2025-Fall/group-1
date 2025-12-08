import base64
from pathlib import Path

import streamlit as st

FONT_STACK = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
APP_DIR = Path(__file__).resolve().parent
BACKGROUND_IMAGE = APP_DIR / "background photo_1.jpg"


def _background_data_url() -> str:
    """Return a base64 data URL for the shared background image."""
    try:
        encoded = base64.b64encode(BACKGROUND_IMAGE.read_bytes()).decode()
        return f"data:image/jpeg;base64,{encoded}"
    except FileNotFoundError:
        return ""


BACKGROUND_URL = _background_data_url()


def apply_global_style():
    """Inject shared styling: dark gradient, accent color, and cleaner containers."""
    st.markdown(
        f"""
        <style>
        :root {{
            --bg-primary: #050505;
            --bg-card: rgba(18, 20, 26, 0.94);
            --border-subtle: #1a1d27;
            --text-main: #f2f3f7;
            --text-muted: #b6b7c4;
            --accent: #7fb6f6;
            --accent-strong: #6aa1e6;
        }}
        html, body, [class*="css"] {{
            font-family: {FONT_STACK};
            background: transparent;
            color: var(--text-main);
        }}
        .stApp {{
            background: linear-gradient(180deg, rgba(5, 5, 5, 0.78), rgba(5, 5, 5, 0.86)), url("{BACKGROUND_URL}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .block-container {{
            padding-top: 2.6rem;
            padding-bottom: 2rem;
            max-width: 1180px;
            margin: 0 auto;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-main);
        }}
        p, label, span, .stMarkdown, .stCaption {{
            color: var(--text-muted);
        }}
        .card {{
            background: rgba(14, 16, 22, 0.88);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 22px;
            border-radius: 16px;
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.45);
            backdrop-filter: blur(4px);
        }}
        .page-title {{
            font-size: 30px;
            font-weight: 800;
            letter-spacing: 0.3px;
            color: var(--text-main);
            margin-bottom: 8px;
        }}
        .lede {{
            font-size: 17px;
            line-height: 1.6;
            color: #d8d9e0;
        }}
        /* Hide the default Streamlit sidebar/page picker */
        [data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="stSidebarHeader"] {{
            display: none !important;
        }}
        [data-testid="collapsedControl"] {{
            display: none !important;
        }}
        /* Top navigation buttons */
        .nav-row .stPageLink a {{
            display: inline-flex;
            width: 100%;
            justify-content: center;
            padding: 14px 12px;
            border-radius: 14px;
            background: linear-gradient(120deg, #8bbcfb, #cbe2ff);
            border: 1px solid #9cc5ff;
            box-shadow: 0 14px 30px rgba(0,0,0,0.25);
        }}
        .nav-row .stPageLink:hover a {{
            transform: translateY(-1px) scale(1.01);
        }}
        /* Buttons */
        .stButton button,
        .stForm button,
        .stForm button[type="submit"] {{
            background: linear-gradient(120deg, #8bbcfb, #cbe2ff) !important;
            color: #0a0a0a !important;
            border: 1px solid #9cc5ff !important;
            border-radius: 18px !important;
            padding: 0.9rem 1.2rem !important;
            font-weight: 800 !important;
            font-size: 22px !important;
            transition: all 0.15s ease !important;
            width: 100%;
            box-shadow: 0 14px 30px rgba(0,0,0,0.25);
        }}
        .stButton button *, .stForm button *, .stForm button[type="submit"] * {{
            color: #0a0a0a !important;
            font-weight: 800 !important;
        }}
        .stButton button:hover, .stForm button:hover, .stPageLink:hover {{
            background: linear-gradient(120deg, #c8ddff, var(--accent));
            transform: translateY(-1px) scale(1.01);
            border-color: #c8ddff;
        }}
        /* Page links styled as wide, friendly pills */
        .stPageLink {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            width: 100%;
            justify-content: center;
            font-size: 20px;
            font-weight: 800;
            text-decoration: none !important;
            box-shadow: 0 14px 30px rgba(0,0,0,0.25);
            color: #0a0a0a !important;
        }}
        .stPageLink a {{
            color: #0a0a0a !important;
            text-decoration: none !important;
            font-weight: 800 !important;
        }}
        .stPageLink:hover a {{
            color: #0a0a0a !important;
        }}
        .stPageLink span {{
            color: #0a0a0a !important;
            font-weight: 800 !important;
        }}
        .stPageLink * {{
            color: #0a0a0a !important;
            font-weight: 800 !important;
        }}
        /* Inputs */
        .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"], .stNumberInput input {{
            background-color: #121622;
            color: var(--text-main);
            border-radius: 12px;
            border: 1px solid var(--border-subtle);
        }}
        .stTextInput input {{
            background-color: #121622;
            color: var(--text-main);
            border-radius: 12px;
            border: 1px solid var(--border-subtle);
        }}
        /* Metrics */
        [data-testid="stMetricValue"] {{
            color: #cfe1ff;
            font-weight: 800;
        }}
        [data-testid="stMetricDelta"] {{
            color: #9ac9ff;
        }}
        /* Pills */
        .pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(127, 182, 246, 0.12);
            color: #cfe1ff;
            border: 1px solid rgba(127, 182, 246, 0.35);
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
