import streamlit as st

FONT_STACK = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"


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
            background: #050505;
            color: var(--text-main);
        }}
        .stApp {{
            background: transparent;
        }}
        .block-container {{
            padding-top: 2.2rem;
            padding-bottom: 2rem;
            max-width: 1120px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-main);
        }}
        p, label, span, .stMarkdown, .stCaption {{
            color: var(--text-muted);
        }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
            backdrop-filter: blur(4px);
        }}
        .page-title {{
            font-size: 30px;
            font-weight: 800;
            letter-spacing: 0.3px;
            color: var(--text-main);
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
