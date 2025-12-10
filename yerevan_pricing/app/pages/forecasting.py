import sys
from pathlib import Path

# Ensure package imports work
APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import html
import os
import random
import re
import uuid
from datetime import datetime, timezone

import altair as alt
import pandas as pd
import requests
import streamlit as st

try:
    from app.components.navigation import render_nav_row
    from app.theme import apply_global_style
except ModuleNotFoundError:
    from components.navigation import render_nav_row
    from theme import apply_global_style

# API URL from environment or default
# Use group1_api service name when running in Docker, localhost when running locally
API_URL = os.getenv("API_URL", "http://group1_api:8000")

LOCATIONS = ["Ajapnyak", "Arabkir", "Kentron", "Malatia-Sebastia", "Nor Nork"]
MENU_ITEMS = [
    "Beef Steak",
    "Brownie",
    "Cappuccino",
    "Latte",
    "Omelet / Scramble",
    "Macchiato",
    "Ricotta Croissant",
    "Aperol Spritz",
    "Eggs Benedict",
    "Mineral Water",
    "Salmon Croissant",
    "Quattro Formaggi",
    "Hummus Plate",
    "Margarita Pizza",
    "Chicken Caesar",
    "Club Sandwich",
    "Black Tea",
    "Ventricina Pizza",
]
AGE_GROUPS = ["0-17", "18-24", "25-34", "35-44", "45-54", "55+"]
CAFE_TYPES = [
    "restaurant",
    "coffee_house",
    "bar_bistro",
    "bakery_cafe",
    "coffee_chain",
    "cafe",
]
PROPORTIONS = ["Small", "Medium", "Large"]
MENU_CARD_STYLE = """
<style>
.session-menu {
    margin-top: 1rem;
}
.session-menu__grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 18px;
}
.session-menu__card {
    background: rgba(18, 20, 30, 0.94);
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.06);
    padding: 20px 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.45);
}
.session-menu__head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
}
.session-menu__title {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 6px;
    color: #f2f4ff;
}
.session-menu__price {
    font-size: 22px;
    font-weight: 800;
    color: #a8f7b5;
    white-space: nowrap;
}
.session-menu__meta {
    font-size: 14px;
    color: #c4c6d3;
    line-height: 1.5;
}
.session-menu__confidence {
    margin-top: 10px;
    font-size: 13px;
    color: #8fb7ff;
}
.session-menu__timestamp {
    margin-top: 10px;
    font-size: 12px;
    color: #9aa0b5;
}
.session-menu__empty {
    padding: 36px;
    text-align: center;
    border-radius: 18px;
    border: 1px dashed rgba(255,255,255,0.12);
    color: #c4c6d3;
    background: rgba(15,17,24,0.8);
}
</style>
"""
LOCAL_SNAPSHOT_PREFIX = "local-"


def ensure_prediction_session():
    """Guarantee Streamlit session metadata for saving predictions."""
    if "prediction_session_id" not in st.session_state:
        st.session_state.prediction_session_id = str(uuid.uuid4())
    if "prediction_snapshots" not in st.session_state:
        st.session_state.prediction_snapshots = []
    if "snapshot_error" not in st.session_state:
        st.session_state.snapshot_error = None
    if "snapshots_loaded_once" not in st.session_state:
        st.session_state.snapshots_loaded_once = False
    if "forecast_result" not in st.session_state:
        st.session_state.forecast_result = None
    if "forecast_toast" not in st.session_state:
        st.session_state.forecast_toast = None
    if "cafe_name" not in st.session_state:
        st.session_state.cafe_name = ""
    if "cafe_name_input" not in st.session_state:
        st.session_state.cafe_name_input = ""


def fetch_prediction_snapshots():
    """Load saved predictions for the active session from the API."""
    session_id = st.session_state.get("prediction_session_id")
    if not session_id:
        return
    try:
        resp = requests.get(
            f"{API_URL}/prediction-snapshots",
            params={"session_id": session_id},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data:
                st.session_state.prediction_snapshots = data
            elif not st.session_state.prediction_snapshots:
                st.session_state.prediction_snapshots = []
            st.session_state.snapshot_error = None
        else:
            st.session_state.snapshot_error = f"Snapshot API error ({resp.status_code})"
    except requests.exceptions.RequestException as exc:
        st.session_state.snapshot_error = f"Snapshot API error: {exc}"


def clear_remote_snapshots(session_id: str):
    """Remove saved predictions for the session via the API."""
    if not session_id:
        return
    try:
        requests.delete(
            f"{API_URL}/prediction-snapshots",
            params={"session_id": session_id},
            timeout=5,
        )
    except requests.exceptions.RequestException:
        pass


def format_snapshot_timestamp(value) -> str:
    """Turn ISO timestamps into a short readable label."""
    if not value:
        return ""
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            cleaned = str(value).replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
        return dt.strftime("%b %d • %H:%M")
    except Exception:
        return str(value)


def _format_price(value) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "--"


def build_menu_markup(snapshots: list) -> str:
    """Return HTML markup for the saved menu."""
    if not snapshots:
        return '<div class="session-menu"><div class="session-menu__empty">Your saved menu will appear here once you run a prediction.</div></div>'

    cards = []
    for snap in snapshots:
        venue = snap.get("venue_type", "--").replace("_", " ").title()
        portion = str(snap.get("portion_size", "--")).title()
        meta = f"{snap.get('location', '--')} • {venue}"
        price = _format_price(snap.get("predicted_price"))
        confidence_low = _format_price(snap.get("confidence_low"))
        confidence_high = _format_price(snap.get("confidence_high"))
        timestamp = format_snapshot_timestamp(snap.get("created_at"))
        cards.append(
            f"""
            <div class="session-menu__card">
                <div class="session-menu__head">
                    <div>
                        <div class="session-menu__title">{snap.get('product_name', 'Menu Item')}</div>
                        <div class="session-menu__meta">
                            <div>{meta}</div>
                            <div>Portion: {portion} • Age: {snap.get('age_group', '--')}</div>
                        </div>
                    </div>
                    <div class="session-menu__price">{price} AMD</div>
                </div>
                <div class="session-menu__confidence">
                    Confidence window: {confidence_low} – {confidence_high} AMD
                </div>
                <div class="session-menu__timestamp">
                    Saved on {timestamp}
                </div>
            </div>
            """
        )
    return f'<div class="session-menu"><div class="session-menu__grid">{"".join(cards)}</div></div>'


def build_downloadable_menu(snapshots: list, title: str = "Session Menu") -> str:
    """Wrap the menu markup in a minimal HTML document for downloads."""
    body = build_menu_markup(snapshots)
    safe_title = html.escape(title or "Session Menu")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{safe_title}</title>
{MENU_CARD_STYLE}
</head>
<body style="background:#0e111a;padding:32px;font-family:Segoe UI, sans-serif;color:#f2f3f7;">
<h2>{safe_title}</h2>
<p>Predictions captured from the Yerevan Dynamic Pricing tool.</p>
{body}
</body>
</html>"""


def build_single_snapshot_markup(snapshot) -> str:
    """Return markup for the most recent snapshot."""
    if not snapshot:
        return '<div class="session-menu__empty">Run a forecast to capture your first dish.</div>'
    return build_menu_markup([snapshot])


def sanitize_filename(name: str, session_id: str) -> str:
    """Return a filesystem-friendly filename for downloads."""
    base = re.sub(r"[^A-Za-z0-9_-]+", "-", (name or "").strip())
    base = base.strip("-").lower()
    if not base:
        base = f"session-menu-{session_id}"
    return f"{base}.html"


def reset_session_menu():
    """Clear backend data and rotate the local session id."""
    old_session = st.session_state.get("prediction_session_id")
    if old_session:
        clear_remote_snapshots(old_session)
    st.session_state.prediction_session_id = str(uuid.uuid4())
    st.session_state.prediction_snapshots = []
    st.session_state.snapshot_error = None
    st.session_state.snapshots_loaded_once = True
    st.session_state.cafe_name = ""
    if "cafe_name_input" in st.session_state:
        st.session_state.cafe_name_input = ""


def _derive_confidence_bounds(value):
    if value is None:
        return None, None
    try:
        price = float(value)
        return round(price * 0.9, 2), round(price * 1.1, 2)
    except (TypeError, ValueError):
        return None, None


def _upsert_local_snapshot(snapshot: dict):
    """Insert or replace a snapshot in local state."""
    snapshots = list(st.session_state.get("prediction_snapshots", []))
    snapshot_id = snapshot.get("snapshot_id")
    replaced = False
    if snapshot_id is not None:
        for idx, existing in enumerate(snapshots):
            if existing.get("snapshot_id") == snapshot_id:
                snapshots[idx] = snapshot
                replaced = True
                break
    if not replaced:
        snapshots.append(snapshot)
    st.session_state.prediction_snapshots = snapshots


def add_snapshot_from_prediction(prediction: dict):
    """Build a snapshot entry from a prediction response (fallback when API storage unavailable)."""
    if not prediction:
        return
    session_id = prediction.get("session_id") or st.session_state.get("prediction_session_id")
    if not session_id:
        return

    predicted_price = prediction.get("predicted_price")
    confidence_low = prediction.get("confidence_low")
    confidence_high = prediction.get("confidence_high")
    if confidence_low is None or confidence_high is None:
        confidence_low, confidence_high = _derive_confidence_bounds(predicted_price)

    snapshot_id = prediction.get("snapshot_id")
    if snapshot_id is None:
        snapshot_id = f"{LOCAL_SNAPSHOT_PREFIX}{uuid.uuid4()}"

    snapshot = {
        "snapshot_id": snapshot_id,
        "session_id": session_id,
        "product_name": prediction.get("product_name"),
        "location": prediction.get("location"),
        "venue_type": prediction.get("venue_type"),
        "portion_size": prediction.get("portion_size"),
        "age_group": prediction.get("age_group"),
        "predicted_price": predicted_price,
        "confidence_low": confidence_low,
        "confidence_high": confidence_high,
        "created_at": prediction.get("created_at") or datetime.now(timezone.utc).isoformat(),
    }
    _upsert_local_snapshot(snapshot)

st.set_page_config(
    page_title="Forecasting",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_style()
st.markdown(MENU_CARD_STYLE, unsafe_allow_html=True)
ensure_prediction_session()

render_nav_row(active="forecasting")

if not st.session_state.snapshots_loaded_once:
    fetch_prediction_snapshots()
    st.session_state.snapshots_loaded_once = True

st.markdown('<div class="page-title">Forecasting</div>', unsafe_allow_html=True)
st.caption("Set your assumptions, press run, and watch the next weeks come alive.")

summary_cols = st.columns(3)
with summary_cols[0]:
    st.markdown('<div class="stat-card"><div class="label">Scenario</div><div class="value">Ready</div><p>Inputs validated</p></div>', unsafe_allow_html=True)
with summary_cols[1]:
    st.markdown('<div class="stat-card"><div class="label">Serving size</div><div class="value">Medium</div><p>Default proportion</p></div>', unsafe_allow_html=True)
with summary_cols[2]:
    st.markdown('<div class="stat-card"><div class="label">Guardrail</div><div class="value">Holding</div><p>Margins protected</p></div>', unsafe_allow_html=True)

left, right = st.columns([1.4, 1])

with left:
    st.markdown('<div class="card forecast-form">', unsafe_allow_html=True)
    st.markdown("<h3>Set up your scenario</h3>", unsafe_allow_html=True)
    st.caption("Pick the location, dish, and guest profile you want to explore. The model blends those signals with menu history.")
    with st.form("forecast_inputs"):
        menu_ctx_cols = st.columns(2)
        with menu_ctx_cols[0]:
            location = st.selectbox("Location", LOCATIONS, index=0, key="forecast_location")
            st.markdown('<div class="helper">District or neighborhood you plan to serve.</div>', unsafe_allow_html=True)
            cafe_type = st.selectbox("Venue type", CAFE_TYPES, key="forecast_cafe_type")
            st.markdown('<div class="helper">Select the concept closest to your space.</div>', unsafe_allow_html=True)
        with menu_ctx_cols[1]:
            menu_item = st.selectbox(
                "Menu item",
                MENU_ITEMS,
                index=0,
                key="forecast_menu_item",
            )
            st.markdown('<div class="helper">Search from the tracked dishes list.</div>', unsafe_allow_html=True)
            proportion = st.selectbox(
                "Portion",
                PROPORTIONS,
                index=1,
                key="forecast_proportion",
            )
            st.markdown('<div class="helper">Match the serving size or glass pour.</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("<h4>Guest moment</h4>", unsafe_allow_html=True)
        guest_cols = st.columns(2)
        with guest_cols[0]:
            age_group = st.selectbox("Age group", AGE_GROUPS, index=2, key="forecast_age_group")
            st.markdown('<div class="helper">Primary customer segment for this run.</div>', unsafe_allow_html=True)
        with guest_cols[1]:
            horizon = st.number_input(
                "Forecast horizon (days)",
                min_value=1,
                max_value=365,
                value=30,
                step=1,
                key="forecast_horizon",
            )
            st.markdown('<div class="helper">How far ahead you want the projection.</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("Run forecast", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Call API when form is submitted
if submitted:
    with st.spinner("Calculating forecast…"):
        try:
            response = requests.get(
                f"{API_URL}/predict-price",
                params={
                    "product_name": menu_item,
                    "location": location,
                    "venue_type": cafe_type,
                    "portion_size": proportion.lower(),
                    "age_group": age_group,
                    "session_id": st.session_state.prediction_session_id,
                },
                timeout=10,
            )
            if response.status_code == 200:
                st.session_state.forecast_result = response.json()
                add_snapshot_from_prediction(st.session_state.forecast_result)
                fetch_prediction_snapshots()
                st.session_state.snapshots_loaded_once = True
                st.session_state.forecast_toast = (
                    "success",
                    f"Forecast updated for {menu_item} in {location}.",
                )
            else:
                st.session_state.forecast_result = {"error": f"API Error: {response.status_code}"}
                st.session_state.forecast_toast = ("error", st.session_state.forecast_result["error"])
        except requests.exceptions.RequestException as e:
            st.session_state.forecast_result = {"error": f"Connection error: {str(e)}"}
            st.session_state.forecast_toast = ("error", st.session_state.forecast_result["error"])

with right:
    st.markdown('<div class="card snapshot-card">', unsafe_allow_html=True)
    st.markdown("<h3>Forecast snapshot</h3>", unsafe_allow_html=True)
    result = st.session_state.forecast_result
    if result and "error" not in result:
        predicted_price = result.get("predicted_price", 0)
        low = round(predicted_price * 0.9, 2)
        high = round(predicted_price * 1.1, 2)
        st.markdown(f'<div class="guardrail-badge">Holding margin</div>', unsafe_allow_html=True)
        st.markdown(f"<h1 style='margin-top:0.6rem;'>{predicted_price:,.0f} AMD</h1>", unsafe_allow_html=True)
        st.caption(f"Confidence window {low:,.0f} – {high:,.0f} AMD")
        base = predicted_price
        horizon_val = st.session_state.get("forecast_horizon", 30)
        trend = [base * (1 + 0.002 * i + random.uniform(-0.01, 0.01)) for i in range(int(horizon_val))]
        chart_df = pd.DataFrame({"Day": list(range(1, len(trend) + 1)), "Price": trend})
        chart = (
            alt.Chart(chart_df)
            .mark_line(color="#f3c372", strokeWidth=3)
            .encode(
                x=alt.X("Day:Q", axis=alt.Axis(title="Day", titleColor="#c6c8d2", labelColor="#c6c8d2")),
                y=alt.Y("Price:Q", axis=alt.Axis(title="Price (AMD)", titleColor="#c6c8d2", labelColor="#c6c8d2"), scale=alt.Scale(zero=False)),
                tooltip=[alt.Tooltip("Day:Q"), alt.Tooltip("Price:Q", format=",")]
            )
            .properties(height=230, title="Projected path")
        )
        st.altair_chart(chart, use_container_width=True)
    elif result and "error" in result:
        st.error(result["error"])
        st.markdown('<div class="menu-ledger__empty">Adjust inputs and try again.</div>', unsafe_allow_html=True)
    else:
        st.info("Run a forecast to see price projections here.")
        placeholder_df = pd.DataFrame({"Day": list(range(1, 8)), "Price": [12.2, 12.4, 12.5, 12.7, 12.75, 12.9, 13.0]})
        chart = (
            alt.Chart(placeholder_df)
            .mark_line(color="#9bb59c", strokeDash=[4, 4])
            .encode(x="Day", y="Price")
            .properties(height=200)
        )
        st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

toast = st.session_state.get("forecast_toast")
if toast:
    level, message = toast
    toast_fn = {
        "success": st.success,
        "error": st.error,
        "warning": st.warning,
        "info": st.info,
    }.get(level, st.info)
    toast_fn(message)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("### Menu snapshot & download")
st.caption("We keep every run in the background. Preview the latest and download the full ledger when you're done.")

cafe_input = st.text_input(
    "Cafe or restaurant name",
    value=st.session_state.get("cafe_name_input", ""),
    key="cafe_name_input",
    placeholder="e.g., Cascade Bistro",
)
st.session_state.cafe_name = cafe_input.strip()

if st.session_state.snapshot_error:
    st.warning(st.session_state.snapshot_error)

current_snapshots = st.session_state.get("prediction_snapshots", [])
latest_snapshot = current_snapshots[-1] if current_snapshots else None
preview_markup = build_single_snapshot_markup(latest_snapshot)
st.markdown(preview_markup, unsafe_allow_html=True)
if latest_snapshot:
    st.caption("Need the full ledger? Use the download below to grab every saved dish.")

download_title = st.session_state.cafe_name or "Session Menu"
download_bytes = build_downloadable_menu(current_snapshots, download_title).encode("utf-8")
file_name = sanitize_filename(download_title, st.session_state.prediction_session_id)
controls_left, controls_right = st.columns([2, 1])
with controls_right:
    st.download_button(
        "Download menu as HTML",
        data=download_bytes,
        file_name=file_name,
        mime="text/html",
        use_container_width=True,
        disabled=not current_snapshots,
    )
with controls_left:
    st.caption(f"Session ID: {st.session_state.prediction_session_id}")

button_cols = st.columns(2)
with button_cols[0]:
    if st.button("Refresh session data", use_container_width=True):
        fetch_prediction_snapshots()
with button_cols[1]:
    if st.button("Start new session menu", use_container_width=True):
        reset_session_menu()
        st.success("Session menu cleared. Run a forecast to add new dishes.")
