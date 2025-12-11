import base64
from pathlib import Path

import streamlit as st

FONT_STACK = "'Inter', 'Source Sans Pro', 'Segoe UI', sans-serif"

# Inside Docker this will be /app, and cafe.png is copied next to theme.py
APP_DIR = Path(__file__).resolve().parent
BACKGROUND_IMAGE = APP_DIR / "cafe.png"


def _background_data_url() -> str:
    """Return a base64 data URL for the shared background image."""
    try:
        encoded = base64.b64encode(BACKGROUND_IMAGE.read_bytes()).decode()
        return f"data:image/png;base64,{encoded}"
    except FileNotFoundError:
        # If something goes wrong, fail gracefully with no image
        st.warning(f"Background image not found at: {BACKGROUND_IMAGE}")
        return ""


BACKGROUND_URL = _background_data_url()


def apply_global_style():
    """Inject shared styling aligned with the warm evening Yerevan theme."""
    st.markdown(
        f"""
        <style>
        :root {{
            --ink: #10141d;
            --card: rgba(20, 22, 30, 0.92);
            --card-soft: rgba(15, 17, 24, 0.85);
            --muted: #c4c6d3;
            --cream: #f1e7d6;
            --border: rgba(255, 255, 255, 0.08);
        }}

        html, body, [class*="css"] {{
            font-family: {FONT_STACK};
            color: var(--cream);
        }}

        /* App background: softer gradient so the cafe photo is visible */
        .stApp {{
            background:
                linear-gradient(
                    180deg,
                    rgba(7, 7, 10, 0.40),
                    rgba(7, 7, 10, 0.70)
                ),
                url("{BACKGROUND_URL}") center/cover fixed;
            background-attachment: fixed;
        }}

        .stPageLink a,
        .stButton > button,
        .stDownloadButton > button,
        .stForm button {{
            border-radius: 18px !important;
            border: none !important;
            background: linear-gradient(135deg, #c4f1b4, #275241) !important;
            color: #fdf9ec !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            padding: 0.9rem 1.4rem !important;
            box-shadow: 0 18px 32px rgba(9, 24, 16, 0.55);
            transition: transform 0.15s ease, filter 0.15s ease;
        }}

        .stPageLink a:hover,
        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stForm button:hover {{
            filter: brightness(1.05);
            transform: translateY(-1px);
        }}

        .stPageLink a:focus-visible,
        .stButton > button:focus-visible,
        .stDownloadButton > button:focus-visible,
        .stForm button:focus-visible {{
            outline: 2px solid #fdf9ec;
            outline-offset: 2px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
