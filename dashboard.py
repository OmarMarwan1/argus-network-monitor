"""
ARGUS — Network Operations Dashboard (Streamlit)

"""

from datetime import datetime

import pandas as pd
import requests
import streamlit as st

API_URL = "https://argus-network-monitor.onrender.com"

refresh_seconds = 10

C = {
    "bg": "#070B10",
    "surface": "#0E141C",
    "surface_alt": "#131B26",
    "border": "#1F2B3A",
    "text": "#F0F4F8",
    "muted": "#8494A7",
    "accent": "#3B82F6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "critical": "#EF4444",
    "cpu": "#3B82F6",
    "memory": "#06B6D4",
    "temperature": "#F97316",
    "latency": "#F59E0B",
    "packet_loss": "#EF4444",
}

st.set_page_config(
    page_title="ARGUS — Network Operations",
    page_icon="◈",
    layout="wide",
)


# --- Global styling ---------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: {C["text"]};
}}

/* Hide Streamlit dev chrome while preserving sidebar toggle button */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stHeader"] {{ background: transparent; }}

/* Main app background with subtle radial ambient glow */
.stApp {{
    background-color: {C["bg"]};
    background-image:
        radial-gradient(circle at 15% 0%, rgba(59, 130, 246, 0.06) 0%, transparent 45%),
        radial-gradient(circle at 85% 10%, rgba(16, 185, 129, 0.04) 0%, transparent 40%);
}}

.block-container {{
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1440px;
}}

/* --- Sidebar styling --- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {C["surface"]} 0%, {C["bg"]} 100%);
    border-right: 1px solid {C["border"]};
}}

[data-testid="stSidebar"] .block-container {{
    padding-top: 1.5rem !important;
}}

/* Brand header card in sidebar */
.brand-card {{
    background: {C["surface_alt"]};
    border: 1px solid {C["border"]};
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 22px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}}
.brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}}
.brand-mark {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 7px;
    background: rgba(59, 130, 246, 0.15);
    border: 1px solid rgba(59, 130, 246, 0.35);
    font-size: 15px;
    color: {C["accent"]};
}}
.brand-name {{
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 1.2px;
    color: {C["text"]};
}}
.brand-tag {{
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: {C["muted"]};
    padding-left: 38px;
}}

.nav-section-label {{
    font-size: 10.5px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: {C["muted"]};
    margin: 4px 0 8px 4px;
}}

/* Style Sidebar Radio as modern navigation pills */
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] {{
    gap: 6px;
}}
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 9px 12px !important;
    margin: 0 !important;
    transition: all 0.15s ease;
    cursor: pointer;
    width: 100%;
}}
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label:hover {{
    background: {C["surface_alt"]};
    border-color: {C["border"]};
}}
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {{
    background: rgba(59, 130, 246, 0.12);
    border-color: rgba(59, 130, 246, 0.4);
    box-shadow: inset 3px 0 0 {C["accent"]};
}}
[data-testid="stSidebar"] [data-testid="stRadio"] label p {{
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: {C["text"]} !important;
}}

/* Live telemetry pill */
.live-pill {{
    display: flex;
    align-items: center;
    gap: 8px;
    background: {C["surface_alt"]};
    border: 1px solid {C["border"]};
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 11.5px;
    color: {C["muted"]};
    font-family: 'IBM Plex Mono', monospace;
}}
.live-dot {{
    height: 8px;
    width: 8px;
    border-radius: 50%;
    background: {C["success"]};
    display: inline-block;
    flex-shrink: 0;
    animation: pulse 2s infinite;
}}
@keyframes pulse {{
    0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.55); }}
    70% {{ box-shadow: 0 0 0 7px rgba(16, 185, 129, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
}}

/* --- Page Header --- */
.page-header {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-bottom: 16px;
    margin-bottom: 22px;
    border-bottom: 1px solid {C["border"]};
}}
.page-eyebrow {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: {C["accent"]};
}}
.page-title {{
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.3px;
    color: {C["text"]};
    margin: 0;
    line-height: 1.25;
}}
.page-sub {{
    font-size: 13.5px;
    color: {C["muted"]};
    margin: 0;
}}

/* --- KPI Metric Cards --- */
[data-testid="stMetric"] {{
    background: linear-gradient(180deg, {C["surface_alt"]} 0%, {C["surface"]} 100%);
    border: 1px solid {C["border"]};
    border-top: 2px solid rgba(59, 130, 246, 0.45);
    border-radius: 10px;
    padding: 16px 18px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.22);
    transition: transform 0.15s ease, border-color 0.15s ease;
}}
[data-testid="stMetric"]:hover {{
    border-color: rgba(59, 130, 246, 0.5);
}}
[data-testid="stMetricLabel"] {{
    color: {C["muted"]} !important;
    font-size: 11.5px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.7px !important;
}}
[data-testid="stMetricValue"] {{
    font-family: 'IBM Plex Mono', monospace !important;
    color: {C["text"]} !important;
    font-size: 26px !important;
    font-weight: 600 !important;
    margin-top: 4px !important;
}}

/* --- Bordered Panel Containers (st.container(border=True)) --- */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {C["surface"]} !important;
    border: 1px solid {C["border"]} !important;
    border-radius: 10px !important;
    padding: 18px 20px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}}

/* Legacy .panel class support for self-contained HTML blocks */
.panel {{
    background: {C["surface"]};
    border: 1px solid {C["border"]};
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}}
.panel-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid {C["border"]};
}}
.panel-title {{
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.2px;
    color: {C["text"]};
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.panel-subtitle {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: {C["muted"]};
    background: {C["surface_alt"]};
    border: 1px solid {C["border"]};
    padding: 2px 8px;
    border-radius: 999px;
}}

/* --- Status & Severity Badges --- */
.badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-family: 'IBM Plex Mono', monospace;
}}

/* --- Incident / Alert Item Cards --- */
.alert-item {{
    background: {C["surface_alt"]};
    border: 1px solid {C["border"]};
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    transition: border-color 0.15s ease;
}}
.alert-item:hover {{
    border-color: rgba(255, 255, 255, 0.16);
}}
.alert-item-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 4px;
}}
.alert-device {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12.5px;
    font-weight: 600;
    color: {C["text"]};
}}
.alert-desc {{
    font-size: 12.5px;
    color: {C["muted"]};
    line-height: 1.4;
}}

/* Empty state styling */
.empty-state {{
    background: {C["surface_alt"]};
    border: 1px dashed {C["border"]};
    border-radius: 8px;
    padding: 24px 18px;
    text-align: center;
    color: {C["muted"]};
    font-size: 13px;
}}

/* Expander & Inputs */
[data-testid="stExpander"] {{
    background: {C["surface"]} !important;
    border: 1px solid {C["border"]} !important;
    border-radius: 10px !important;
}}
[data-testid="stDataFrame"] {{
    border-radius: 8px;
    overflow: hidden;
}}

hr {{
    border-color: {C["border"]};
    margin: 1.25rem 0;
}}
</style>
""", unsafe_allow_html=True)


# --- Helper: call the API (answers are cached briefly so we don't spam it) --
@st.cache_data(ttl=5)
def get_data(path):
    response = requests.get(f"{API_URL}{path}", timeout=5)
    response.raise_for_status()
    return response.json()


def badge(value, kind="status"):
    """Returns an HTML pill colored by status/severity/risk level."""
    palette = {
        "online": C["success"],
        "offline": C["critical"],
        "high": C["critical"],
        "medium": C["warning"],
        "low": C["muted"],
    }
    color = palette.get(str(value).lower(), C["muted"])
    return (
        f'<span class="badge" style="background:{color}1F; color:{color}; '
        f'border:1px solid {color}4D;">{value}</span>'
    )


def style_df(df, color_cols):
    """Colors the given columns of a dataframe to match our badge palette,
    using Styler so it still works with st.dataframe's sort/search/download."""
    palette = {
        "online": C["success"],
        "offline": C["critical"],
        "high": C["critical"],
        "medium": C["warning"],
        "low": C["muted"],
    }

    def colorize(val):
        c = palette.get(str(val).lower())
        return f"color: {c}; font-weight: 600;" if c else ""

    styler = df.style
    for col in color_cols:
        if col in df.columns:
            try:
                styler = styler.map(colorize, subset=[col])
            except AttributeError:          # older pandas
                styler = styler.applymap(colorize, subset=[col])
    return styler


# --- Sidebar ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand-card">'
        '<div class="brand"><span class="brand-mark">◈</span>'
        '<span class="brand-name">ARGUS</span></div>'
        '<div class="brand-tag">Network Operations</div>'
        '</div>'
        '<div class="nav-section-label">Telemetry Views</div>',
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigate",
        ["Overview", "Devices", "Alerts", "Predictions"],
        label_visibility="collapsed",
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    status_slot = st.empty()   # filled in live_view() with connection + sync time


# --- Everything below re-runs every `refresh_seconds` automatically ---------
@st.fragment(run_every=f"{refresh_seconds}s")
def live_view():
    try:
        devices = get_data("/devices")
        alerts = get_data("/alerts")
        predictions = get_data("/predictions")
    except requests.exceptions.RequestException:
        status_slot.markdown(
            f'<div class="live-pill" style="border-color:{C["critical"]}55; color:{C["critical"]};">'
            f'<span style="color:{C["critical"]};">●</span> disconnected</div>',
            unsafe_allow_html=True,
        )
        st.error(
            "Can't reach the monitoring API. Start it with:\n\n"
            "`python -m uvicorn main:app --reload`"
        )
        return

    status_slot.markdown(
        f'<div class="live-pill"><span class="live-dot"></span>'
        f'<span>LIVE · {datetime.now():%H:%M:%S}</span></div>',
        unsafe_allow_html=True,
    )

    devices_df = pd.DataFrame(devices)
    alerts_df = pd.DataFrame(alerts)
    predictions_df = pd.DataFrame(predictions)

    total = len(devices_df)
    online = int((devices_df["status"] == "online").sum()) if total else 0
    high_alerts = int((alerts_df["severity"] == "high").sum()) if len(
        alerts_df) else 0

    # ----------------------------------------------------------------- Overview
    if page == "Overview":
        st.markdown(
            '<div class="page-header">'
            '<span class="page-eyebrow">Real-Time Telemetry</span>'
            '<div class="page-title">Network Overview</div>'
            '<div class="page-sub">Current state of infrastructure health, active alerts, and node availability</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Devices", total)
        c2.metric(
            "Online",
            online,
            delta=f"{total - online} offline" if total -
            online else "100% healthy",
            delta_color="inverse" if total - online else "normal",
        )
        c3.metric("Active alerts", len(alerts_df))
        c4.metric("High severity", high_alerts)

        st.markdown("<div style='height: 12px;'></div>",
                    unsafe_allow_html=True)
        left, right = st.columns([3, 2], gap="medium")

        with left:
            with st.container(border=True):
                st.markdown(
                    f'<div class="panel-header">'
                    f'<div class="panel-title">Node Inventory</div>'
                    f'<span class="panel-subtitle">{online}/{total} online</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if total:
                    show = devices_df[[
                        "name", "device_type", "layer", "status"]]
                    st.dataframe(
                        style_df(show, ["status"]),
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "name": st.column_config.TextColumn("Device Name"),
                            "device_type": st.column_config.TextColumn("Type"),
                            "layer": st.column_config.TextColumn("Network Layer"),
                            "status": st.column_config.TextColumn("Status"),
                        },
                    )
                else:
                    st.markdown(
                        '<div class="empty-state">No devices registered in inventory.</div>',
                        unsafe_allow_html=True,
                    )

        with right:
            with st.container(border=True):
                urgent = alerts_df[alerts_df["severity"].isin(
                    ["high", "medium"])] if len(alerts_df) else alerts_df
                st.markdown(
                    f'<div class="panel-header">'
                    f'<div class="panel-title">Needs Attention</div>'
                    f'<span class="panel-subtitle">{len(urgent)} priority</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if urgent.empty:
                    st.markdown(
                        '<div class="empty-state">Nothing needs attention right now. All monitored thresholds are nominal.</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    id_to_name = {d["device_id"]: d["name"] for d in devices}
                    for _, row in urgent.sort_values("severity").head(6).iterrows():
                        name = id_to_name.get(
                            row["device_id"], f"device {row['device_id']}")
                        st.markdown(
                            f'<div class="alert-item">'
                            f'<div class="alert-item-top">'
                            f'<span class="alert-device">{name}</span>'
                            f'{badge(row["severity"])}'
                            f'</div>'
                            f'<div class="alert-desc">{row["description"]}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

    # ------------------------------------------------------------------ Devices
    elif page == "Devices":
        st.markdown(
            '<div class="page-header">'
            '<span class="page-eyebrow">Infrastructure Explorer</span>'
            '<div class="page-title">Devices & Telemetry</div>'
            '<div class="page-sub">Inventory filtering and granular per-device performance metrics</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Filter Inventory", expanded=False):
            fc1, fc2 = st.columns(2)
            layers = ["All"] + \
                sorted(devices_df["layer"].dropna().unique().tolist())
            layer_pick = fc1.selectbox("Layer", layers)
            statuses = ["All"] + \
                sorted(devices_df["status"].dropna().unique().tolist())
            status_pick = fc2.selectbox("Status", statuses)

        filtered = devices_df.copy()
        if layer_pick != "All":
            filtered = filtered[filtered["layer"] == layer_pick]
        if status_pick != "All":
            filtered = filtered[filtered["status"] == status_pick]

        with st.container(border=True):
            st.markdown(
                f'<div class="panel-header">'
                f'<div class="panel-title">Filtered Fleet</div>'
                f'<span class="panel-subtitle">{len(filtered)} shown</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(
                style_df(filtered, ["status"]),
                hide_index=True,
                use_container_width=True,
            )

        st.markdown("<div style='height: 12px;'></div>",
                    unsafe_allow_html=True)

        name_to_id = {d["name"]: d["device_id"] for d in devices}
        sel_col, toggle_col = st.columns([3, 1], gap="medium")
        with sel_col:
            st.markdown(
                '<div class="panel-title" style="margin-bottom:6px;">Select Device for Deep Telemetry</div>',
                unsafe_allow_html=True,
            )
            selected = st.selectbox(
                "Select a device",
                list(name_to_id.keys()),
                key="device_select",
                label_visibility="collapsed",
            )
        with toggle_col:
            st.markdown(
                '<div class="panel-title" style="margin-bottom:6px;">Display Mode</div>',
                unsafe_allow_html=True,
            )
            view = st.radio(
                "View",
                ["Chart", "Table"],
                horizontal=True,
                key="view_toggle",
                label_visibility="collapsed",
            )

        try:
            metrics = get_data(f"/devices/{name_to_id[selected]}/metrics")
        except requests.exceptions.HTTPError:
            metrics = []

        if not metrics:
            st.info("No telemetry recorded for this device yet.")
        else:
            mdf = pd.DataFrame(metrics)
            mdf["timestamp"] = pd.to_datetime(mdf["timestamp"])
            mdf = mdf.sort_values("timestamp").set_index("timestamp")
            latest = mdf.iloc[-1]

            st.markdown("<div style='height: 6px;'></div>",
                        unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("CPU Utilization", f"{latest['cpu']:.1f}%")
            c2.metric("Memory Usage", f"{latest['memory']:.1f}%")
            c3.metric("Round-Trip Latency", f"{latest['latency']:.1f} ms")
            c4.metric("Packet Loss", f"{latest['packet_loss']:.2f}%")

            st.markdown("<div style='height: 12px;'></div>",
                        unsafe_allow_html=True)

            if view == "Table":
                with st.container(border=True):
                    st.markdown(
                        f'<div class="panel-header">'
                        f'<div class="panel-title">Telemetry Log — {selected}</div>'
                        f'<span class="panel-subtitle">{len(mdf)} samples</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.dataframe(
                        mdf.sort_index(ascending=False),
                        use_container_width=True,
                    )
            else:
                charts = [
                    ("CPU & Memory (%)", ["cpu", "memory"],
                     [C["cpu"], C["memory"]]),
                    ("Chassis Temperature (°C)", [
                     "temperature"], [C["temperature"]]),
                    ("Network Latency (ms)", ["latency"], [C["latency"]]),
                    ("Packet Loss (%)", ["packet_loss"], [C["packet_loss"]]),
                ]
                cols = st.columns(2, gap="medium")
                for i, (title, cols_used, colors) in enumerate(charts):
                    with cols[i % 2]:
                        with st.container(border=True):
                            st.markdown(
                                f'<div class="panel-header">'
                                f'<div class="panel-title">{title}</div>'
                                f'<span class="panel-subtitle">{selected}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.line_chart(mdf[cols_used],
                                          color=colors, height=230)

    # ------------------------------------------------------------------- Alerts
    elif page == "Alerts":
        st.markdown(
            '<div class="page-header">'
            '<span class="page-eyebrow">Incident Management</span>'
            '<div class="page-title">Active Alerts</div>'
            '<div class="page-sub">Threshold violations and anomalies detected across the network</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        filter_col, _ = st.columns([1, 3])
        with filter_col:
            sev = st.selectbox("Filter by Severity", [
                               "All", "high", "medium", "low"])

        data = get_data("/alerts" if sev ==
                        "All" else f"/alerts?severity={sev}")
        df = pd.DataFrame(data)

        with st.container(border=True):
            st.markdown(
                f'<div class="panel-header">'
                f'<div class="panel-title">Alert Feed</div>'
                f'<span class="panel-subtitle">{len(df)} matching records</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if df.empty:
                st.markdown(
                    '<div class="empty-state">No alerts in this view. The network is behaving normally.</div>',
                    unsafe_allow_html=True,
                )
            else:
                id_to_name = {d["device_id"]: d["name"] for d in devices}
                df.insert(1, "device", df["device_id"].map(id_to_name))
                show = df[["timestamp", "device",
                           "metric", "severity", "description"]]
                st.dataframe(
                    style_df(show, ["severity"]),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "timestamp": st.column_config.TextColumn("Timestamp"),
                        "device": st.column_config.TextColumn("Device"),
                        "metric": st.column_config.TextColumn("Metric"),
                        "severity": st.column_config.TextColumn("Severity"),
                        "description": st.column_config.TextColumn("Diagnostic Details"),
                    },
                )

    # --------------------------------------------------------------- Predictions
    elif page == "Predictions":
        st.markdown(
            '<div class="page-header">'
            '<span class="page-eyebrow">Predictive Analytics</span>'
            '<div class="page-title">ML Failure Risk Predictions</div>'
            '<div class="page-sub">Estimated hardware & link failure probabilities scored by the model</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown(
                f'<div class="panel-header">'
                f'<div class="panel-title">Device Risk Forecast</div>'
                f'<span class="panel-subtitle">{len(predictions_df)} devices scored</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if predictions_df.empty:
                st.markdown(
                    '<div class="empty-state">No predictions yet — risk scores will appear here once the failure prediction model is live.</div>',
                    unsafe_allow_html=True,
                )
            else:
                id_to_name = {d["device_id"]: d["name"] for d in devices}
                predictions_df.insert(
                    1, "device", predictions_df["device_id"].map(id_to_name))
                show = predictions_df[["timestamp", "device",
                                       "risk_level", "failure_risk", "explanation"]]
                st.dataframe(
                    style_df(show, ["risk_level"]),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "timestamp": st.column_config.TextColumn("Scored At"),
                        "device": st.column_config.TextColumn("Device"),
                        "risk_level": st.column_config.TextColumn("Risk Level"),
                        "failure_risk": st.column_config.ProgressColumn(
                            "Failure Probability",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100,
                        ),
                        "explanation": st.column_config.TextColumn("Primary Anomaly Driver"),
                    },
                )


live_view()
