"""
CyberNova Analytics Ltd — BI Portal
app_html.py  |  CET333 Product Development
Visual spec: cybernova_dashboard_final_wireframe.html
Run: streamlit run app_html.py --server.port 8505
"""
from __future__ import annotations
from datetime import date, timedelta
from io import BytesIO
import shutil
import tempfile
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors as rlc
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CyberNova BI Portal",
    page_icon="https://i.imgur.com/placeholder.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# DESIGN TOKENS  (mirrors wireframe CSS variables)
# ─────────────────────────────────────────────────────────────────
BG         = "#F3F4F6"
CARD       = "#FFFFFF"
TEXT       = "#102A43"
SECONDARY  = "#374151"
MUTED      = "#4B5563"
BORDER     = "#D9E2EC"
NAVY       = "#0B1F3A"
HEADER     = "#1F3A5F"
BLUE       = "#2563FF"
BLUE_SOFT  = "#DBEAFE"
CYAN       = "#16B8C7"
CYAN_SOFT  = "#CFFAFE"
GREEN      = "#10B981"
GREEN_SOFT = "#D1FAE5"
AMBER      = "#F59E0B"
AMBER_SOFT = "#FEF3C7"
SLATE_SOFT = "#E5EAF0"
SHADOW     = "0 18px 45px rgba(11,31,58,.08)"
SHADOW_S   = "0 8px 24px rgba(11,31,58,.08)"

PALETTE    = [BLUE, CYAN, GREEN, AMBER, "#8B5CF6", "#EF4444", "#EC4899", "#14B8A6"]

# ─────────────────────────────────────────────────────────────────
# LOGO HELPER  — cached, reused across all render functions
# ─────────────────────────────────────────────────────────────────
@st.cache_resource
def _logo_b64() -> str:
    import base64, pathlib
    p = pathlib.Path(__file__).parent / "cybernova_logo_transparent.svg"
    try:
        return base64.b64encode(p.read_bytes()).decode()
    except Exception:
        return ""

def _logo_html(size: int = 46, radius: int = 14) -> str:
    b64 = _logo_b64()
    if b64:
        return (f'<img src="data:image/svg+xml;base64,{b64}" '
                f'width="{size}" height="{size}" '
                f'style="display:block;border-radius:{radius}px;" alt="CyberNova">')
    return (f'<div style="width:{size}px;height:{size}px;border-radius:{radius}px;'
            f'background:linear-gradient(135deg,#2563FF,#16B8C7);'
            f'display:grid;place-items:center;flex-shrink:0;">'
            f'<span style="color:white;font-size:{max(size//4,10)}px;font-weight:900;letter-spacing:-.02em;">CN</span></div>')

DAY_ORDER  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

SERVICE_URIS = [
    "/ai-assistant.php", "/cybersecurity-monitoring.php", "/risk-assessment.php",
    "/digital-transformation.php", "/predictive-maintenance.php",
    "/prototype.php", "/events.php",
]

# ─────────────────────────────────────────────────────────────────
# CSS  (injects wireframe visual shell into Streamlit)
# ─────────────────────────────────────────────────────────────────
def inject_css() -> None:
    st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════════
   RESET & BASE TYPOGRAPHY
═══════════════════════════════════════════════════════════════ */
html,body,[class*="css"]{
  font-family:Inter,"Segoe UI",Arial,sans-serif;
  line-height:1.55;
  -webkit-font-smoothing:antialiased;
}
.stApp{
  background:radial-gradient(circle at 18% 0%,rgba(37,99,255,.06),transparent 28%),
    radial-gradient(circle at 90% 8%,rgba(22,184,199,.09),transparent 28%),
    #F1F3F6;
}
.block-container{padding-top:1.8rem;padding-bottom:5rem;padding-left:2.5rem !important;padding-right:2.5rem !important;max-width:1620px;}

/* ═══════════════════════════════════════════════════════════════
   PREMIUM WHITE CARD SYSTEM  (st.container(border=True))
═══════════════════════════════════════════════════════════════ */

/* Outer border shell */
[data-testid="stVerticalBlockBorderWrapper"]{
  background:white !important;
  border-radius:20px !important;
  border:1px solid #D9E2EC !important;
  box-shadow:0 2px 6px rgba(11,31,58,.04), 0 8px 28px rgba(11,31,58,.08) !important;
  overflow:hidden !important;
  /* bottom-margin drives spacing between stacked cards */
  margin-bottom:28px !important;
  padding:0 !important;
  transition:box-shadow .2s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover{
  box-shadow:0 3px 8px rgba(11,31,58,.06), 0 14px 36px rgba(11,31,58,.11) !important;
}

/* Inner content block
   Bottom padding = 36px: must exceed the 20px border-radius so the last
   element never visually touches the rounded corner of the card border. */
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"]{
  padding:26px 28px 36px !important;
  gap:1.1rem !important;
}

/* ─── Equal-height cards in side-by-side columns ─── */
[data-testid="stHorizontalBlock"]{
  align-items:stretch !important;
  gap:24px !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"]{
  display:flex !important;
  flex-direction:column !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"]
  > [data-testid="stVerticalBlockBorderWrapper"]{
  flex:1 !important;
  display:flex !important;
  flex-direction:column !important;
  margin-bottom:0 !important; /* gap handles spacing inside a row */
}
[data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlock"]
  > [data-testid="stVerticalBlockBorderWrapper"]
  > [data-testid="stVerticalBlock"]{
  flex:1 !important;
}

/* ═══════════════════════════════════════════════════════════════
   SECTION HEADING SYSTEM
═══════════════════════════════════════════════════════════════ */
.cn-section-eyebrow{
  font-size:10.5px;text-transform:uppercase;letter-spacing:.16em;
  color:#7B8794;font-weight:900;line-height:1;
}
.cn-section-heading{
  font-size:22px;font-weight:900;color:#0B1F3A;
  letter-spacing:-.04em;line-height:1.2;margin:6px 0 0;
}
.cn-section-divider{
  height:1.5px;background:linear-gradient(90deg,#D9E2EC,transparent);
  border:none;margin:0;flex:1;
}

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR SHELL
═══════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0B1E3D 0%,#102A43 100%);
  border-right:1px solid rgba(255,255,255,.08);
}
section[data-testid="stSidebar"] *{color:#EFF6FF;}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label{color:#D9E2EC !important;}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] .stDateInput input,
section[data-testid="stSidebar"] .stTextInput input{
  color:#102A43 !important;background:white !important;border-radius:12px;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"]{
  background:rgba(37,99,255,.30);color:white;
}

/* ── Nav radio — styled as pill buttons ── */
section[data-testid="stSidebar"] .stRadio > label{display:none !important;}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"]{display:flex;flex-direction:column;gap:10px;}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label{
  background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.10);
  border-radius:15px;padding:15px 16px;cursor:pointer;display:flex !important;
  align-items:center;margin:0 !important;transition:.18s ease;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover{
  background:rgba(255,255,255,.10);transform:translateX(2px);
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child{display:none !important;}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:last-child p{
  color:white !important;font-weight:800 !important;font-size:.88rem !important;margin:0 !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked){
  border-color:#2563FF !important;
  background:linear-gradient(135deg,rgba(37,99,255,.76),rgba(22,184,199,.22)) !important;
  box-shadow:inset 4px 0 0 #16B8C7;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:has(input:checked) > div:last-child p{
  color:white !important;font-weight:900 !important;
}

/* ═══════════════════════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════════════════════ */
.stButton > button{
  border-radius:14px;border:0;font-weight:800;padding:.68rem 1.15rem;
  background:#2563FF !important;color:white !important;
  box-shadow:0 10px 24px rgba(37,99,255,.28);transition:.18s ease;
}
.stButton > button:hover{
  transform:translateY(-2px);
  background:#1d4ed8 !important;color:white !important;
  box-shadow:0 14px 32px rgba(37,99,255,.36);
}
.stButton > button:focus,
.stButton > button:active{
  background:#1e40af !important;color:white !important;outline:none;
}
div[data-testid="stDownloadButton"] > button{
  border-radius:14px;border:1.5px solid #D9E2EC;background:white !important;
  color:#102A43 !important;font-weight:800;padding:.62rem 1.05rem;
  box-shadow:0 4px 12px rgba(11,31,58,.07);transition:.18s ease;
}
div[data-testid="stDownloadButton"] > button:hover{
  border-color:#2563FF;color:#2563FF !important;background:white !important;
  box-shadow:0 6px 18px rgba(37,99,255,.18);
}

/* ═══════════════════════════════════════════════════════════════
   DATAFRAMES & TABLES
═══════════════════════════════════════════════════════════════ */
hr{border:none;border-top:1px solid #D9E2EC;margin:1.6rem 0;}
.stDataFrame{border-radius:18px;overflow:hidden;border:1px solid #D9E2EC;
  box-shadow:0 4px 12px rgba(11,31,58,.06);}
[data-testid="stDataFrame"]{border-radius:18px;}

/* ═══════════════════════════════════════════════════════════════
   EXPANDERS
═══════════════════════════════════════════════════════════════ */
[data-testid="stExpander"]{
  border-radius:18px !important;border:1px solid #D9E2EC !important;
  background:white !important;overflow:hidden;
}
[data-testid="stExpander"] summary{font-weight:800;color:#0B1F3A;}

/* ═══════════════════════════════════════════════════════════════
   CHART AREA BREATHING ROOM
═══════════════════════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] .js-plotly-plot,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"]{
  margin-top:6px;margin-bottom:6px;
}

/* ═══════════════════════════════════════════════════════════════
   CARD CONTENT — SAFE MARGIN RESET
   Only strip <p> tag margins (Streamlit injects these for plain
   text and they add unwanted vertical gaps inside cards).
   Do NOT touch stMarkdownContainer or its anonymous child div —
   those wrappers carry margins the insight notes depend on.
═══════════════════════════════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p{
  margin-top:0 !important;
  margin-bottom:0 !important;
}
/* ═══════════════════════════════════════════════════════════════
   ANIMATIONS
═══════════════════════════════════════════════════════════════ */
@keyframes live-tick{from{opacity:.55;transform:scale(.97)}to{opacity:1;transform:scale(1)}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# ROLES & AUTH
# ─────────────────────────────────────────────────────────────────
ROLES: dict[str, dict] = {
    "Sales Team Lead":       {"pw": "sales123",     "access": ["CyberNova Pulse"]},
    "Marketing Lead":        {"pw": "marketing123", "access": ["CyberNova Reach"]},
    "Executive Management":  {"pw": "exec123",      "access": ["CyberNova Horizon"]},
    "Admin / Lecturer View": {"pw": "admin123",     "access": ["CyberNova Pulse","CyberNova Reach","CyberNova Horizon"]},
}
DASHBOARDS  = ["CyberNova Pulse", "CyberNova Reach", "CyberNova Horizon"]
EXCEL_PATH  = "data/output/cybernova_web_logs.xlsx"    # primary live data source
ENRICH_PATH = "data/output/cybernova_enriched_logs.csv" # enrichment join

# ─────────────────────────────────────────────────────────────────
# DATA LOADING  — Excel is the true source; CSV supplies enriched cols
# ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame | None:
    # ── 1. Load raw Excel web logs (copy to temp to bypass OneDrive lock)
    try:
        tmp = tempfile.mktemp(suffix=".xlsx")
        shutil.copy2(EXCEL_PATH, tmp)
        xl = pd.read_excel(tmp)
        try:
            os.unlink(tmp)
        except Exception:
            pass
    except Exception:
        return None

    # ── 2. Join with enriched CSV to get derived columns ──────────
    try:
        csv = pd.read_csv(ENRICH_PATH)
        xl["_key"]  = xl["ip_address"].astype(str)  + "|" + xl["date"].astype(str)  + "|" + xl["time"].astype(str)
        csv["_key"] = csv["ip_address"].astype(str) + "|" + csv["date"].astype(str) + "|" + csv["time"].astype(str)
        enrich_cols = [c for c in csv.columns if c not in xl.columns and c != "_key"]
        df = xl.merge(csv[["_key"] + enrich_cols], on="_key", how="left")
        df.drop(columns=["_key"], inplace=True)
    except Exception:
        df = xl.copy()

    # ── 3. Derive timestamp and parse dates ───────────────────────
    df["timestamp"] = pd.to_datetime(
        df["date"].astype(str) + " " + df["time"].astype(str), errors="coerce"
    )
    for col in ("date", "first_request_ts", "last_request_ts"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "anomaly_name" in df.columns:
        df["anomaly_name"] = df["anomaly_name"].fillna("None").astype(str)
    if "session_number_for_ip" in df.columns:
        df["session_number_for_ip"] = pd.to_numeric(
            df["session_number_for_ip"], errors="coerce").fillna(1).astype(int)
    for bc in ("is_bot","is_warm_lead","is_anomaly","converted_to_lead",
               "is_sadc","is_weekend","is_campaign_period"):
        if bc in df.columns:
            df[bc] = df[bc].astype(bool)

    # ── 4. Sort by timestamp for natural live-ticker order ─────────
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df

# ─────────────────────────────────────────────────────────────────
# FILTER HELPERS
# ─────────────────────────────────────────────────────────────────
def apply_filters(
    df: pd.DataFrame,
    start: date, end: date,
    countries: list, services: list,
    status_classes: list, segments: list,
    include_bots: bool,
) -> pd.DataFrame:
    mask = (df["date"].dt.date >= start) & (df["date"].dt.date <= end)
    fdf  = df[mask].copy()
    if countries:      fdf = fdf[fdf["country"].isin(countries)]
    if services:       fdf = fdf[fdf["service_name"].isin(services)]
    if status_classes: fdf = fdf[fdf["status_class"].isin(status_classes)]
    if segments:       fdf = fdf[fdf["segment"].isin(segments)]
    if not include_bots: fdf = fdf[~fdf["is_bot"]]
    return fdf.reset_index(drop=True)

def wk(ts: pd.Series)  -> pd.Series: return ts.dt.strftime("%Y-W%V")
def mo(ts: pd.Series)  -> pd.Series: return ts.dt.strftime("%Y-%m")
def to_csv(df: pd.DataFrame) -> bytes: return df.to_csv(index=False).encode()

# ─────────────────────────────────────────────────────────────────
# CALCULATION HELPERS
# ─────────────────────────────────────────────────────────────────
def calculate_sales_metrics(fdf: pd.DataFrame) -> dict:
    m: dict = {}
    if fdf.empty:
        return {k: 0 for k in ("warm_total","leads_24h","leads_7d","ai_conv",
                                "top_country","top_service","funnel_drop","peak_hour")}
    warm      = fdf[fdf["is_warm_lead"]]
    max_ts    = fdf["date"].max()
    week_ago  = max_ts - pd.Timedelta(days=7)
    m["warm_total"]   = int(fdf["is_warm_lead"].sum())
    m["leads_24h"]    = int(fdf[fdf["date"] == max_ts]["is_warm_lead"].sum())
    m["leads_7d"]     = int(fdf[fdf["date"] > week_ago]["is_warm_lead"].sum())
    ai_sess           = set(fdf[fdf["uri"]=="/ai-assistant.php"]["session_id"]) if "uri" in fdf.columns else set()
    demo_ai           = fdf[fdf["session_id"].isin(ai_sess) & (fdf["uri"]=="/scheduledemo.php")]["session_id"].nunique() if ai_sess else 0
    m["ai_conv"]      = demo_ai / max(len(ai_sess),1)
    m["top_country"]  = warm["country"].value_counts().index[0] if not warm.empty else "—"
    _GENERIC_SVCS = {"contact", "schedule demo", "event signup", "contact request",
                     "demo request", "contact us", "events and promotions"}
    if not warm.empty and "service_name" in warm.columns:
        _svc_w = warm[~warm["service_name"].str.lower().isin(_GENERIC_SVCS)]
        m["top_service"] = _svc_w["service_name"].value_counts().index[0] if not _svc_w.empty else (warm["service_name"].value_counts().index[0])
    else:
        m["top_service"] = "—"
    m["top_action"] = (warm["event_type"].value_counts().index[0]
                       if not warm.empty and "event_type" in warm.columns
                       else "—")
    svc_sess          = fdf[fdf["uri"].isin(SERVICE_URIS)]["session_id"].nunique() if "uri" in fdf.columns else 0
    demo_sess         = fdf[fdf["uri"]=="/scheduledemo.php"]["session_id"].nunique() if "uri" in fdf.columns else 0
    m["funnel_drop"]  = (demo_sess / max(svc_sess,1)) < 0.10
    demo_df           = fdf[fdf["uri"]=="/scheduledemo.php"] if "uri" in fdf.columns else pd.DataFrame()
    m["peak_hour"]    = int(demo_df["hour"].value_counts().index[0]) if not demo_df.empty and "hour" in demo_df.columns else None
    return m

def calculate_marketing_metrics(fdf: pd.DataFrame) -> dict:
    m: dict = {}
    if fdf.empty:
        return {k:"—" for k in ("uniq_vis","eng_rate","top_entry","top_country","bot_ratio","geo_reach")}
    m["uniq_vis"]  = fdf["ip_address"].nunique() if "ip_address" in fdf.columns else 0
    sd             = fdf.drop_duplicates("session_id") if "session_id" in fdf.columns else fdf
    m["eng_rate"]  = float((sd["distinct_pages_session"]>=3).mean()) if "distinct_pages_session" in sd.columns else 0.0
    m["bot_ratio"] = float(fdf["is_bot"].mean()) if "is_bot" in fdf.columns else 0.0
    try:
        _BAD = {"undefined", "null", "none", "nan", "", "/"}
        if "entry_page" in sd.columns:
            _ep_s = sd["entry_page"].astype(str).str.lower()
            sd_ep = sd[sd["entry_page"].notna()
                       & ~_ep_s.isin(_BAD)
                       & ~_ep_s.str.contains("undefined", na=False)]
        else:
            sd_ep = sd
        dep = sd_ep.groupby("entry_page")["distinct_pages_session"].mean() if "entry_page" in sd_ep.columns else pd.Series()
        m["top_entry"] = dep.idxmax() if not dep.empty else "—"
    except Exception:
        m["top_entry"] = "—"
    m["top_country"] = (fdf.groupby("country")["ip_address"].nunique().idxmax()
                        if "ip_address" in fdf.columns and "country" in fdf.columns else "—")
    m["geo_reach"]   = int((fdf.groupby("country").size()>=10).sum()) if "country" in fdf.columns else 0
    return m

def calculate_executive_metrics(fdf: pd.DataFrame) -> dict:
    m: dict = {}
    if fdf.empty:
        return {k:0 for k in ("mom_growth","ai_share","sadc_total","anom_days","forecast","warm_total","curr_vis","prev_vis")}
    ym      = mo(fdf["date"])
    months  = sorted(ym.unique())
    cv      = fdf[ym==months[-1]]["ip_address"].nunique() if months else 0
    pv      = fdf[ym==months[-2]]["ip_address"].nunique() if len(months)>=2 else 0
    m["curr_vis"]   = cv
    m["prev_vis"]   = pv
    m["mom_growth"] = (cv-pv)/max(pv,1)*100
    ai_r    = int((fdf["uri"]=="/ai-assistant.php").sum()) if "uri" in fdf.columns else 0
    svc_r   = int(fdf["uri"].isin(SERVICE_URIS).sum())    if "uri" in fdf.columns else 1
    m["ai_share"]   = ai_r/max(svc_r,1)
    m["sadc_total"] = int(fdf[fdf["is_sadc"]]["country"].nunique()) if "is_sadc" in fdf.columns else 0
    m["anom_days"]  = int(fdf[fdf["is_anomaly"]]["date"].dt.date.nunique()) if "is_anomaly" in fdf.columns else 0
    m["warm_total"] = int(fdf["is_warm_lead"].sum()) if "is_warm_lead" in fdf.columns else 0
    wc = fdf[fdf["is_warm_lead"]].copy()
    wc["d"] = wc["date"].dt.date
    dl = wc.groupby("d").size()
    dl.index = pd.to_datetime(dl.index)
    if len(dl)>=7:
        x,y = np.arange(len(dl),dtype=float), dl.values.astype(float)
        mm,b = np.polyfit(x,y,1)
        fx = np.arange(len(x),len(x)+90,dtype=float)
        m["forecast"] = max(int(sum(np.maximum(mm*fx+b,0))),0)
    else:
        m["forecast"] = int(dl.mean()*90) if not dl.empty else 0
    return m

# ─────────────────────────────────────────────────────────────────
# STORY GENERATORS
# ─────────────────────────────────────────────────────────────────
def generate_sales_story(fdf: pd.DataFrame, m: dict) -> tuple[list[str], str]:
    if fdf.empty:
        return ["No data in the selected filter range."], "Adjust filters to load Sales insights."
    bullets: list[str] = []
    tc = m.get("top_country","—"); ts = m.get("top_service","—")
    warm = fdf[fdf["is_warm_lead"]]
    if not warm.empty:
        cnt = int(warm["country"].value_counts().iloc[0]) if "country" in warm.columns else 0
        bullets.append(f"<strong>{tc}</strong> leads warm-lead activity with {cnt:,} events in the selected period.")
        bullets.append(f"Highest service interest is <strong>{ts}</strong> — lead the sales conversation here.")
    else:
        bullets.append("No warm-lead events in current filter range — check status and date filters.")
    conv = m.get("ai_conv",0)
    lvl  = "strong" if conv>=0.15 else ("moderate" if conv>=0.05 else "weak")
    bullets.append(f"AI Assistant sessions converted to demo at <strong>{conv:.1%}</strong> — <strong>{lvl}</strong> product-led interest.")
    if m.get("funnel_drop", True):
        bullets.append("Main opportunity: <strong>reduce drop-off</strong> between service page and demo request.")
    else:
        bullets.append("Demo pipeline is healthy — prioritise <strong>rapid follow-up</strong> on warm leads.")
    ph = m.get("peak_hour")
    if ph is not None:
        bullets.append(f"Demo requests peak at <strong>{ph:02d}:00</strong> — align follow-up capacity to this window.")
    action = f"Prioritise warm leads from <strong>{tc}</strong> showing <strong>{ts}</strong> interest."
    return bullets, action

def generate_marketing_story(fdf: pd.DataFrame, m: dict) -> tuple[list[str], str]:
    if fdf.empty:
        return ["No data in the selected filter range."], "Adjust filters to load Marketing insights."
    bullets: list[str] = []
    tc = m.get("top_country","—"); uv = m.get("uniq_vis",0); er = m.get("eng_rate",0)
    bullets.append(f"<strong>{tc}</strong> is the largest audience market with <strong>{uv:,}</strong> unique visitors.")
    qlty = "strong" if er>=0.35 else ("moderate" if er>=0.18 else "low")
    bullets.append(f"Engaged session rate is <strong>{er:.1%}</strong> — <strong>{qlty}</strong> content depth signal.")
    te = m.get("top_entry","—")
    bullets.append(f"Top entry path: <strong>{te}</strong> — an important campaign landing page.")
    if "segment" in fdf.columns:
        segs = fdf[fdf["segment"]!="Bot"]["segment"].value_counts() if "Bot" in fdf["segment"].values else fdf["segment"].value_counts()
        if not segs.empty:
            ds = segs.index[0]
            dd = {"High-intent":"high-intent","Product-curious":"product-curious","General browser":"general"}.get(ds,"general")
            bullets.append(f"Dominant human segment: <strong>{ds}</strong> — site is attracting <strong>{dd}</strong> traffic.")
    br = m.get("bot_ratio",0)
    if br>0.15:
        bullets.append(f"Bot activity is <strong>elevated ({br:.1%})</strong> and may distort reach metrics.")
    else:
        bullets.append(f"Bot activity is controlled at <strong>{br:.1%}</strong> — analytics quality is sound.")
    action = f"Focus campaign testing on <strong>{tc}</strong> and <strong>{te}</strong>."
    return bullets, action

def generate_executive_story(fdf: pd.DataFrame, m: dict) -> tuple[list[str], str]:
    if fdf.empty:
        return ["No data in the selected filter range."], "Adjust filters to load Executive insights."
    bullets: list[str] = []
    bullets.append(f"CyberNova generated <strong>{m.get('warm_total',0):,}</strong> warm-lead events in the selected period.")
    ai_s = m.get("ai_share",0)
    tr   = "strong" if ai_s>=0.18 else ("moderate" if ai_s>=0.10 else "emerging")
    bullets.append(f"AI Assistant holds <strong>{ai_s:.1%}</strong> of service traffic — showing <strong>{tr}</strong> traction.")
    if "country" in fdf.columns and "is_warm_lead" in fdf.columns:
        try:
            tc = fdf.groupby("country")["ip_address"].nunique().idxmax() if "ip_address" in fdf.columns else "—"
            tv = int(fdf.groupby("country")["ip_address"].nunique().max()) if "ip_address" in fdf.columns else 0
            tw = int(fdf[fdf["is_warm_lead"]]["country"].value_counts().get(tc,0))
            bullets.append(f"Strongest regional market: <strong>{tc}</strong> with {tv:,} visitors and {tw:,} warm leads.")
        except Exception:
            pass
    ad = m.get("anom_days",0)
    if ad>0:
        bullets.append(f"<strong>{ad}</strong> anomaly days flagged — review for operational or security context.")
    else:
        bullets.append("No anomaly events visible in the selected filter context.")
    bullets.append(f"90-day warm-lead forecast: approximately <strong>{m.get('forecast',0):,}</strong> leads (linear projection — next 3 months).")
    mg = m.get("mom_growth",0); ai_share = m.get("ai_share",0)
    if ad>0:
        action = "Review anomaly log and protect reporting quality."
    elif ai_share>=0.12:
        action = "Scale AI Assistant positioning across high-performing SADC markets."
    else:
        action = "Strengthen campaign activity around high-intent services."
    return bullets, action

# ─────────────────────────────────────────────────────────────────
# CHART STYLE HELPER
# ─────────────────────────────────────────────────────────────────
def cs(fig: go.Figure, h: int = 420) -> go.Figure:
    fig.update_layout(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(249,251,253,1)",
        font=dict(color=TEXT, family="Inter, Segoe UI, Arial, sans-serif", size=12),
        margin=dict(l=12, r=12, t=44, b=14),
        legend=dict(bgcolor="rgba(255,255,255,0)", font=dict(size=11)),
    )
    fig.update_xaxes(gridcolor="#EAEDF0", showline=False, zeroline=False, tickfont=dict(size=11))
    fig.update_yaxes(gridcolor="#EAEDF0", showline=False, zeroline=False, tickfont=dict(size=11))
    return fig

# ─────────────────────────────────────────────────────────────────
# RENDER HELPERS — HTML COMPONENTS
# ─────────────────────────────────────────────────────────────────
def render_hero(title: str, badge: str, subtitle: str) -> None:
    st.markdown(f"""
<div style="position:relative;overflow:hidden;border-radius:28px;padding:36px 40px;
  background:linear-gradient(135deg,#0B1E3D 0%,#1F3A5F 52%,#2563FF 132%);
  color:white;box-shadow:{SHADOW};margin-bottom:18px;">
  <div style="position:absolute;right:-80px;top:-100px;width:310px;height:310px;
    border-radius:999px;background:rgba(22,184,199,.20);"></div>
  <div style="position:absolute;left:-40px;bottom:-60px;width:200px;height:200px;
    border-radius:999px;background:rgba(37,99,255,.12);"></div>
  <!-- CN logo mark -->
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:18px;position:relative;z-index:1;">
    <div style="overflow:hidden;flex-shrink:0;border-radius:14px;
      box-shadow:0 8px 24px rgba(37,99,255,.45),0 0 0 2px rgba(255,255,255,.15);">
      {_logo_html(46, 14)}
    </div>
    <div style="display:inline-flex;padding:7px 14px;border-radius:999px;
      border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.10);
      font-size:12px;font-weight:800;">
      {badge}
    </div>
  </div>
  <h1 style="margin:0;font-size:38px;letter-spacing:-.055em;line-height:1.05;
    position:relative;z-index:1;">{title}</h1>
  <p style="max-width:920px;margin:14px 0 0;color:#E6EEF8;font-size:16px;
    line-height:1.65;position:relative;z-index:1;">{subtitle}</p>
</div>""", unsafe_allow_html=True)

def render_story_strip(stages: list[str], accent: str = BLUE) -> None:
    pills = ""
    for s in stages:
        pills += (f'<span style="padding:8px 14px;border-radius:999px;font-size:12px;'
                  f'font-weight:800;background:{accent};color:white;border:1px solid {accent};">{s}</span> ')
    st.markdown(
        f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 18px;">{pills}</div>',
        unsafe_allow_html=True,
    )

def render_section_label(text: str) -> None:
    if " — " in text:
        eyebrow, heading = text.split(" — ", 1)
    else:
        eyebrow, heading = text, ""
    heading_html = (
        f'<div style="font-size:23px;font-weight:900;color:{NAVY};'
        f'letter-spacing:-.04em;line-height:1.2;margin:7px 0 0;">{heading}</div>'
        if heading else ""
    )
    st.markdown(
        f'<div style="margin:52px 0 22px;">'
        f'<div style="display:flex;align-items:center;gap:14px;">'
        f'<span style="font-size:10.5px;text-transform:uppercase;letter-spacing:.16em;'
        f'color:{MUTED};font-weight:900;white-space:nowrap;">{eyebrow}</span>'
        f'<span style="height:1.5px;background:linear-gradient(90deg,{BORDER},transparent);'
        f'flex:1;display:block;border-radius:2px;"></span>'
        f'</div>'
        + heading_html +
        f'</div>',
        unsafe_allow_html=True,
    )

def render_context_chips(filters: dict, role: str, row_count: int) -> None:
    c_str  = ", ".join(filters["countries"])      if filters["countries"]      else "All countries"
    s_str  = ", ".join(filters["services"])       if filters["services"]       else "All services"
    sc_str = ", ".join(filters["status_classes"]) if filters["status_classes"] else "All statuses"
    sg_str = ", ".join(filters["segments"])       if filters["segments"]       else "All segments"
    chip   = lambda lbl, val, col, tcol: (
        f'<span style="display:inline-flex;align-items:center;gap:6px;padding:7px 11px;'
        f'border-radius:999px;font-size:12px;font-weight:800;background:{col};color:{tcol};">'
        f'{lbl}: {val}</span> ')
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:8px;background:rgba(255,255,255,.88);'
        f'border:1px solid {BORDER};border-radius:18px;padding:13px;'
        f'box-shadow:{SHADOW_S};margin-bottom:20px;">'
        + chip("Role",    role,              "#EDE9FE","#5B21B6")
        + chip("Period",  f'{filters["start"]} to {filters["end"]}', BLUE_SOFT, BLUE)
        + chip("Countries",c_str[:28]+("…" if len(c_str)>28 else ""),SLATE_SOFT,SECONDARY)
        + chip("Services", s_str[:28]+("…" if len(s_str)>28 else ""),SLATE_SOFT,SECONDARY)
        + chip("Status",   sc_str,            SLATE_SOFT, SECONDARY)
        + chip("Segments", sg_str[:28]+("…" if len(sg_str)>28 else ""),SLATE_SOFT,SECONDARY)
        + chip("Bots",     "Included" if filters["include_bots"] else "Excluded",
               AMBER_SOFT if filters["include_bots"] else GREEN_SOFT,
               "#92400E" if filters["include_bots"] else "#047857")
        + chip("Rows",     f'{row_count:,}', GREEN_SOFT, "#047857")
        + chip("Data Quality", "Good" if row_count > 100 else "Review Needed",
               GREEN_SOFT if row_count > 100 else AMBER_SOFT,
               "#047857" if row_count > 100 else "#92400E")
        + '</div>', unsafe_allow_html=True,
    )

def _kpi_font_size(value: str) -> str:
    import re
    if re.match(r'^[+\-]?[\d,]+(\.\d+)?[%KMk~]?$', value.strip()):
        return "31px"
    return "17px"

def render_kpi_card(label: str, value: str, delta: str,
                    delta_good: bool = True, accent: str = BLUE) -> None:
    dc   = "#047857" if delta_good else "#92400E"
    dot  = GREEN if delta_good else AMBER
    st.markdown(f"""
<div style="background:white;border:1px solid {BORDER};border-radius:20px;
  box-shadow:0 2px 4px rgba(11,31,58,.04),0 8px 22px rgba(11,31,58,.07);
  padding:20px;min-height:160px;overflow:hidden;
  display:flex;flex-direction:column;justify-content:space-between;
  transition:box-shadow .2s;">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;">
    <div style="font-size:11px;color:{SECONDARY};font-weight:900;
      text-transform:uppercase;letter-spacing:.08em;line-height:1.3;">{label}</div>
    <div style="width:8px;height:8px;border-radius:50%;background:{dot};
      flex-shrink:0;margin-top:3px;box-shadow:0 0 0 3px {'rgba(16,185,129,.18)' if delta_good else 'rgba(245,158,11,.18)'};"></div>
  </div>
  <div style="font-size:{_kpi_font_size(value)};font-weight:950;color:{NAVY};letter-spacing:-.05em;
    line-height:1.1;margin:10px 0 8px;word-break:break-word;">{value}</div>
  <div style="font-size:12.5px;font-weight:700;color:{dc};">{delta}</div>
</div>""", unsafe_allow_html=True)

def render_live_card(title: str, subtitle: str, value: str, caption: str,
                     accent: str = BLUE) -> None:
    st.markdown(f"""
<div style="background:white;border:1px solid {BORDER};border-radius:18px;
  box-shadow:{SHADOW_S};padding:18px;min-height:168px;position:relative;overflow:hidden;">
  <div style="position:absolute;right:-45px;top:-45px;width:120px;height:120px;
    border-radius:999px;background:rgba(37,99,255,.06);"></div>
  <div style="font-size:13px;font-weight:900;color:{NAVY};position:relative;z-index:1;">{title}</div>
  <div style="font-size:12px;color:{MUTED};margin-top:3px;position:relative;z-index:1;">{subtitle}</div>
  <div style="font-size:30px;font-weight:950;letter-spacing:-.05em;color:{accent};
    margin:12px 0 4px;position:relative;z-index:1;">{value}</div>
  <div style="font-size:12px;font-weight:800;color:{SECONDARY};position:relative;z-index:1;">{caption}</div>
</div>""", unsafe_allow_html=True)

def render_story_card(title: str, subtitle: str, bullets: list[str],
                      action: str, accent: str = BLUE,
                      accent_soft: str = BLUE_SOFT) -> None:
    items = "".join(f'<li style="margin:8px 0;color:{SECONDARY};">{b}</li>' for b in bullets)
    st.markdown(f"""
<div style="background:white;border:1px solid {BORDER};border-radius:22px;
  box-shadow:{SHADOW_S};padding:22px;margin-bottom:18px;
  display:grid;grid-template-columns:1fr 280px;gap:18px;align-items:start;">
  <div>
    <h2 style="margin:0 0 6px;color:{NAVY};font-size:23px;letter-spacing:-.035em;">{title}</h2>
    <p style="margin:0 0 14px;color:{SECONDARY};font-size:14px;">{subtitle}</p>
    <ul style="margin:0;padding-left:20px;">{items}</ul>
  </div>
  <div style="border-radius:18px;padding:18px;
    background:linear-gradient(180deg,{accent_soft},#FFFFFF);
    border:1px solid rgba(37,99,255,.18);">
    <strong style="display:block;color:{accent};margin-bottom:6px;font-size:13px;
      text-transform:uppercase;letter-spacing:.08em;">Recommended Action</strong>
    <span style="color:{TEXT};font-weight:800;font-size:15px;">{action}</span>
  </div>
</div>""", unsafe_allow_html=True)

def render_insight_note(text: str, accent_soft: str = BLUE_SOFT, accent: str = "#1E40AF") -> None:
    st.markdown(
        f'<div style="margin-top:14px;margin-bottom:8px;padding:12px 18px;border-radius:12px;'
        f'background:{accent_soft};color:{accent};font-size:12.5px;font-weight:700;'
        f'display:flex;align-items:flex-start;gap:8px;line-height:1.55;width:100%;'
        f'box-sizing:border-box;">'
        f'<span style="width:7px;height:7px;border-radius:50%;background:{accent};'
        f'flex-shrink:0;margin-top:5px;opacity:.85;"></span>'
        f'<span style="flex:1;">{text}</span>'
        f'</div>', unsafe_allow_html=True,
    )

def render_empty_state(msg: str = "No data for current filters") -> None:
    st.markdown(f"""
<div style="background:white;border:1px dashed {BORDER};border-radius:18px;
  padding:3rem 2rem;text-align:center;margin-top:1rem;">
  <div style="font-size:1.3rem;font-weight:800;color:{NAVY};margin-bottom:.5rem;">{msg}</div>
  <div style="color:{MUTED};font-size:.9rem;">
    Try adjusting the date range, removing filters, or resetting to defaults.
  </div>
</div>""", unsafe_allow_html=True)

def render_card_header(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    eyebrow_html = (
        f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.14em;'
        f'color:{MUTED};font-weight:900;margin-bottom:6px;">{eyebrow}</div>'
        if eyebrow else ""
    )
    rule = (f'<div style="height:1px;background:linear-gradient(90deg,{BORDER},transparent);'
            f'margin:10px 0 14px;border-radius:1px;"></div>')
    st.markdown(
        f'<div style="margin-bottom:4px;">'
        + eyebrow_html
        + f'<h3 style="margin:0;font-size:17px;font-weight:900;color:{NAVY};'
        f'letter-spacing:-.03em;line-height:1.25;">{title}</h3>'
        + (f'<p style="margin:4px 0 0;color:{MUTED};font-size:12.5px;font-weight:500;'
           f'line-height:1.45;">{subtitle}</p>' if subtitle else "")
        + rule
        + "</div>", unsafe_allow_html=True,
    )

def render_live_feed(fdf: pd.DataFrame, role: str = "", limit: int = 10) -> None:
    if fdf.empty:
        render_empty_state("No activity events")
        return
    src = fdf.copy()
    src["timestamp"] = pd.to_datetime(src["timestamp"], errors="coerce")
    src = src.dropna(subset=["timestamp"]).sort_values("timestamp", ascending=False)
    # Priority filtering per role
    if "Sales" in role:
        hi_mask = (src.get("is_warm_lead", pd.Series(False, index=src.index)) |
                   src.get("event_type", pd.Series("", index=src.index))
                       .str.contains("demo|contact|event|ai", na=False, regex=True))
        src = pd.concat([src[hi_mask], src[~hi_mask]]).drop_duplicates()
    elif "Marketing" in role:
        hi_mask = (~src.get("is_bot", pd.Series(False, index=src.index)) |
                   src.get("campaign_name", pd.Series("", index=src.index)).notna())
        src = pd.concat([src[hi_mask], src[~hi_mask]]).drop_duplicates()
    elif "Executive" in role or "Admin" in role:
        hi_mask = (src.get("is_anomaly", pd.Series(False, index=src.index)) |
                   src.get("is_warm_lead", pd.Series(False, index=src.index)) |
                   src.get("uri", pd.Series("", index=src.index)).str.contains("ai-assistant", na=False))
        src = pd.concat([src[hi_mask], src[~hi_mask]]).drop_duplicates()
    src = src.head(limit)
    items_html = ""
    for _, row in src.iterrows():
        is_warm = bool(row.get("is_warm_lead", False))
        is_anom = bool(row.get("is_anomaly", False))
        is_bot  = bool(row.get("is_bot", False))
        stat    = str(row.get("status_class","2xx"))
        evt     = str(row.get("event_type","page_request"))
        if is_anom or stat in ("4xx","5xx"):
            dot_c = AMBER; dot_s = AMBER_SOFT
        elif is_warm or any(k in evt for k in ("demo","contact","ai","event")):
            dot_c = GREEN; dot_s = GREEN_SOFT
        else:
            dot_c = BLUE; dot_s = BLUE_SOFT
        warm_tag = f'<span style="background:{GREEN_SOFT};color:#047857;font-size:11px;font-weight:800;padding:2px 7px;border-radius:999px;margin-left:6px;">warm lead</span>' if is_warm else ""
        anom_tag = f'<span style="background:{AMBER_SOFT};color:#92400E;font-size:11px;font-weight:800;padding:2px 7px;border-radius:999px;margin-left:4px;">anomaly</span>' if is_anom else ""
        ts_str  = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if pd.notna(row.get("timestamp")) else "—"
        svc     = str(row.get("service_name","—"))[:34]
        country = str(row.get("country","—"))
        seg     = str(row.get("segment","—"))
        items_html += f"""
<div style="display:grid;grid-template-columns:14px 1fr auto;gap:12px;align-items:start;
  padding:13px 14px;border:1px solid {BORDER};border-radius:14px;background:#F8FAFC;margin-bottom:10px;">
  <div style="width:11px;height:11px;border-radius:999px;margin-top:5px;
    background:{dot_c};box-shadow:0 0 0 4px {dot_s};"></div>
  <div>
    <div style="font-weight:900;color:{NAVY};font-size:14px;">{country} &middot; {svc}{warm_tag}{anom_tag}</div>
    <div style="color:{MUTED};font-size:12px;margin-top:3px;">{evt} &middot; {seg} &middot; <strong>{stat}</strong> &middot; {ts_str}</div>
  </div>
  <div style="font-size:11px;color:{MUTED};white-space:nowrap;">{ts_str.split(' ')[1] if ' ' in ts_str else ''}</div>
</div>"""
    st.markdown(items_html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# LIVE TICKER  — advances one Excel record every 3 seconds
# ─────────────────────────────────────────────────────────────────
def _init_live_state(n: int) -> None:
    """Initialise live ticker session keys once per session."""
    st.session_state.setdefault("live_cursor", 0)
    st.session_state.setdefault("live_log", [])
    st.session_state["_live_total"] = n


@st.fragment(run_every=3)
def render_live_section(fdf: pd.DataFrame, role: str, dashboard: str) -> None:
    """Auto-refreshing fragment: ingests one Excel row every 3 s and renders
    the live stream banner, live pulse cards, and live activity feed."""
    full_df: pd.DataFrame | None = st.session_state.get("_full_df")
    if full_df is None or full_df.empty:
        st.info("Live data stream not available.")
        return

    # ── Advance cursor by one record ──────────────────────────────
    n      = len(full_df)
    cursor = int(st.session_state.get("live_cursor", 0)) % n
    row    = full_df.iloc[cursor].to_dict()

    log: list[dict] = list(st.session_state.get("live_log", []))
    log.insert(0, row)
    if len(log) > 300:
        log = log[:300]
    st.session_state["live_log"]    = log
    st.session_state["live_cursor"] = (cursor + 1) % n

    # ── Rebuild live DataFrame from ring buffer ────────────────────
    live_df = pd.DataFrame(log)
    for c in ("timestamp", "date"):
        if c in live_df.columns:
            live_df[c] = pd.to_datetime(live_df[c], errors="coerce")
    for bc in ("is_bot", "is_warm_lead", "is_anomaly", "is_sadc"):
        if bc in live_df.columns:
            live_df[bc] = live_df[bc].astype(bool)

    # ── Parse raw fields for the NOW STREAMING banner ─────────────
    curr_time  = str(row.get("time",  "—"))
    curr_ip    = str(row.get("ip_address", "—"))
    curr_uri   = str(row.get("uri",   "—"))
    curr_sc    = int(row.get("status_code", 200))
    curr_ms    = int(row.get("response_time_ms", 0))
    curr_bytes = int(row.get("bytes_transferred", 0))
    curr_ua    = str(row.get("user_agent", "—"))[:42]
    curr_meth  = str(row.get("method", "GET"))
    curr_ctry  = str(row.get("country", "—"))
    curr_svc   = str(row.get("service_name", curr_uri[:28]))[:32]
    curr_warm  = bool(row.get("is_warm_lead", False))
    curr_anom  = bool(row.get("is_anomaly", False))
    curr_bot   = bool(row.get("is_bot", False))
    sc_col     = GREEN if curr_sc < 300 else (AMBER if curr_sc < 500 else "#EF4444")
    flags      = ""
    if curr_warm: flags += f'<span style="background:{GREEN_SOFT};color:#047857;font-size:11px;font-weight:800;padding:2px 8px;border-radius:999px;margin-left:6px;">warm lead</span>'
    if curr_anom: flags += f'<span style="background:{AMBER_SOFT};color:#92400E;font-size:11px;font-weight:800;padding:2px 8px;border-radius:999px;margin-left:4px;">anomaly</span>'
    if curr_bot:  flags += f'<span style="background:{SLATE_SOFT};color:{SECONDARY};font-size:11px;font-weight:800;padding:2px 8px;border-radius:999px;margin-left:4px;">bot</span>'
    kb_label   = f"{curr_bytes//1024}K" if curr_bytes >= 1024 else str(curr_bytes)

    # ── NOW STREAMING banner ───────────────────────────────────────
    st.markdown(f"""
<div style="background:linear-gradient(135deg,{NAVY} 0%,{HEADER} 100%);
  border-radius:18px;padding:18px 22px;margin-bottom:18px;
  border:1px solid rgba(255,255,255,.07);box-shadow:{SHADOW_S};">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
    <div style="width:9px;height:9px;border-radius:999px;background:{GREEN};
      box-shadow:0 0 0 5px rgba(16,185,129,.30);flex-shrink:0;"></div>
    <span style="color:#9FB2C7;font-size:11px;font-weight:800;
      text-transform:uppercase;letter-spacing:.1em;">
      LIVE STREAM &nbsp;&middot;&nbsp; record {cursor+1:,} of {n:,}
    </span>
    <span style="margin-left:auto;color:#9FB2C7;font-size:12px;">{curr_time}</span>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr auto;gap:16px;align-items:start;">
    <div>
      <div style="color:#9FB2C7;font-size:10px;font-weight:700;text-transform:uppercase;
        letter-spacing:.09em;margin-bottom:4px;">Source</div>
      <div style="color:white;font-weight:900;font-size:15px;line-height:1.2;">{curr_ctry}{flags}</div>
      <div style="color:#9FB2C7;font-size:12px;margin-top:3px;">{curr_ip}</div>
      <div style="color:#9FB2C7;font-size:11px;margin-top:2px;">{curr_ua}</div>
    </div>
    <div>
      <div style="color:#9FB2C7;font-size:10px;font-weight:700;text-transform:uppercase;
        letter-spacing:.09em;margin-bottom:4px;">Request</div>
      <div style="color:white;font-weight:900;font-size:14px;line-height:1.2;
        font-family:monospace;">{curr_meth} {curr_uri}</div>
      <div style="color:#9FB2C7;font-size:12px;margin-top:3px;">{curr_svc}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
      <div style="background:rgba(255,255,255,.06);border-radius:10px;
        padding:12px 8px;text-align:center;min-width:52px;">
        <div style="color:{sc_col};font-size:20px;font-weight:900;line-height:1;">{curr_sc}</div>
        <div style="color:#9FB2C7;font-size:10px;margin-top:3px;">HTTP</div>
      </div>
      <div style="background:rgba(255,255,255,.06);border-radius:10px;
        padding:12px 8px;text-align:center;min-width:52px;">
        <div style="color:white;font-size:20px;font-weight:900;line-height:1;">{curr_ms}</div>
        <div style="color:#9FB2C7;font-size:10px;margin-top:3px;">ms</div>
      </div>
      <div style="background:rgba(255,255,255,.06);border-radius:10px;
        padding:12px 8px;text-align:center;min-width:52px;">
        <div style="color:white;font-size:18px;font-weight:900;line-height:1;">{kb_label}</div>
        <div style="color:#9FB2C7;font-size:10px;margin-top:3px;">bytes</div>
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Compute all 16 counter values from ring buffer ────────────
    total_seen   = len(live_df)
    unique_ips   = int(live_df["ip_address"].nunique())           if "ip_address"   in live_df.columns else 0
    human_reqs   = int((~live_df["is_bot"]).sum())                if "is_bot"       in live_df.columns else total_seen
    bot_reqs     = int(live_df["is_bot"].sum())                   if "is_bot"       in live_df.columns else 0
    warm_seen    = int(live_df["is_warm_lead"].sum())             if "is_warm_lead" in live_df.columns else 0
    demo_seen    = int((live_df["uri"]=="/scheduledemo.php").sum())  if "uri" in live_df.columns else 0
    ai_seen      = int((live_df["uri"]=="/ai-assistant.php").sum())  if "uri" in live_df.columns else 0
    contact_seen = int((live_df["uri"]=="/contact.php").sum())       if "uri" in live_df.columns else 0
    avg_ms       = int(live_df["response_time_ms"].mean())        if "response_time_ms"   in live_df.columns and total_seen>0 else 0
    total_kb     = int(live_df["bytes_transferred"].sum()//1024)  if "bytes_transferred"  in live_df.columns else 0
    ok_2xx       = int((live_df["status_code"]<300).sum())        if "status_code"  in live_df.columns else 0
    err_4xx5xx   = int((live_df["status_code"]>=400).sum())       if "status_code"  in live_df.columns else 0
    anom_seen    = int(live_df["is_anomaly"].sum())               if "is_anomaly"   in live_df.columns else 0
    ctry_seen    = int(live_df["country"].nunique())              if "country"      in live_df.columns else 0
    sadc_seen    = int(live_df[live_df["is_sadc"]]["country"].nunique()) if "is_sadc" in live_df.columns else 0
    camp_seen    = int(live_df["is_campaign_period"].sum())       if "is_campaign_period" in live_df.columns else 0

    # Accent colour per dashboard for section headers
    accent_hex = BLUE if dashboard=="CyberNova Pulse" else (CYAN if dashboard=="CyberNova Reach" else GREEN)

    def _c(n, col=TEXT):
        """Format counter value with comma thousands and optional colour."""
        return f'<span style="color:{col};animation:live-tick .45s ease-out;">{n:,}</span>'

    def _counter_row(items, pcts=None):
        """Build one row of 4 counters with optional progress bars.
        items = list of (value_html, label, sublabel, accent); pcts = list of floats or None."""
        pcts = pcts or [None]*len(items)
        cells = ""
        for (val_html, label, sublabel, ac), pct in zip(items, pcts):
            bar_html = ""
            if pct is not None:
                w = min(max(pct * 100, 0), 100)
                bar_html = (f'<div style="height:3px;border-radius:3px;'
                            f'background:rgba(255,255,255,.12);margin-top:8px;">'
                            f'<div style="height:100%;background:{ac};'
                            f'width:{w:.1f}%;border-radius:3px;transition:width .4s ease;"></div>'
                            f'</div>')
            cells += f"""
<div style="padding:22px 12px;text-align:center;background:white;border-right:1px solid {BORDER};">
  <div style="font-size:2.15rem;font-weight:900;line-height:1;
    font-variant-numeric:tabular-nums;letter-spacing:-.02em;
    animation:live-tick .45s ease-out;">{val_html}</div>
  <div style="font-size:11px;font-weight:800;text-transform:uppercase;
    letter-spacing:.09em;color:{ac};margin-top:7px;">{label}</div>
  <div style="font-size:11px;color:{MUTED};margin-top:3px;">{sublabel}</div>
  {bar_html}
</div>"""
        return f'<div style="display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid {BORDER};">{cells}</div>'

    def _section_hdr(title, colour):
        return f"""
<div style="background:{colour};padding:10px 20px;
  font-size:11px;font-weight:900;color:white;
  letter-spacing:.12em;text-transform:uppercase;">{title}</div>"""

    # ── Worldometers-style counter bank ───────────────────────────
    st.markdown(f"""
<style>
@keyframes live-tick {{
  0%   {{ opacity:.55; transform:translateY(-5px) scale(.96); }}
  70%  {{ opacity:1;   transform:translateY(1px)  scale(1.01); }}
  100% {{ opacity:1;   transform:translateY(0)    scale(1.0); }}
}}
</style>
<div style="background:white;border:1px solid {BORDER};border-radius:18px;
  overflow:hidden;box-shadow:{SHADOW_S};margin-bottom:18px;">

  {_section_hdr("LIVE WEB TRAFFIC", NAVY)}
  {_counter_row([
    (_c(total_seen, BLUE),   "Requests Streamed",  f"record {cursor+1:,} of {n:,}", BLUE),
    (_c(unique_ips, CYAN),   "Unique Visitors",    "distinct IP addresses",           CYAN),
    (_c(human_reqs, GREEN),  "Human Requests",     "non-bot traffic",                 GREEN),
    (_c(bot_reqs, SECONDARY),"Bots Blocked",       "crawler / spider traffic",        SECONDARY),
  ], pcts=[None, unique_ips/max(total_seen,1), human_reqs/max(total_seen,1), bot_reqs/max(total_seen,1)])}

  {_section_hdr("LEADS & CONVERSIONS", "#047857")}
  {_counter_row([
    (_c(warm_seen,    GREEN), "Warm Leads",      "high-intent visitors",              GREEN),
    (_c(demo_seen,    BLUE),  "Demo Requests",   "/scheduledemo hits",                BLUE),
    (_c(ai_seen,      CYAN),  "AI Asst. Hits",   "/ai-assistant requests",            CYAN),
    (_c(contact_seen, AMBER), "Contact Requests","/contact page hits",                AMBER),
  ], pcts=[warm_seen/max(human_reqs,1), demo_seen/max(warm_seen,1), ai_seen/max(human_reqs,1), contact_seen/max(human_reqs,1)])}

  {_section_hdr("PERFORMANCE", "#0E7490")}
  {_counter_row([
    (_c(avg_ms,     CYAN),   "Avg Response",   "milliseconds per request",    CYAN),
    (f'<span style="color:{BLUE};animation:live-tick .45s ease-out;">{total_kb:,}<span style="font-size:1.1rem;font-weight:700"> KB</span></span>',
                              "Data Served",   "total kilobytes transferred",  BLUE),
    (_c(ok_2xx,     GREEN),  "HTTP 2xx OK",    "successful responses",         GREEN),
    (_c(err_4xx5xx, "#EF4444" if err_4xx5xx>0 else MUTED),
                              "4xx / 5xx",     "client and server errors",     "#EF4444" if err_4xx5xx>0 else MUTED),
  ], pcts=[min(avg_ms/2000,1), None, ok_2xx/max(total_seen,1), err_4xx5xx/max(total_seen,1)])}

  {_section_hdr("SECURITY & GEOGRAPHIC REACH", "#92400E" if anom_seen>0 else "#374151")}
  {_counter_row([
    (_c(anom_seen,  "#EF4444" if anom_seen>0 else MUTED),
                              "Anomalies",     "flagged security events",       "#EF4444" if anom_seen>0 else MUTED),
    (_c(ctry_seen,  AMBER),   "Countries",     "unique markets seen",           AMBER),
    (_c(sadc_seen,  GREEN),   "SADC Markets",  "regional countries active",     GREEN),
    (_c(camp_seen,  BLUE),    "Campaign Hits", "campaign-period requests",      BLUE),
  ], pcts=[anom_seen/max(total_seen,1), ctry_seen/50, sadc_seen/16, camp_seen/max(total_seen,1)])}

</div>""", unsafe_allow_html=True)

    # ── Live Geographic Map + country table ───────────────────────
    render_section_label("LIVE GEOGRAPHIC REACH — REQUESTS BY COUNTRY")
    if "country" in live_df.columns:
        _geo = live_df.groupby("country").agg(
            requests=("country", "count"),
            warm_leads=("is_warm_lead", "sum") if "is_warm_lead" in live_df.columns else ("country", lambda x: 0),
        ).reset_index()
        _geo["warm_leads"] = _geo["warm_leads"].fillna(0).astype(int)
        _geo_fig = px.choropleth(
            _geo,
            locations="country",
            locationmode="country names",
            color="requests",
            hover_name="country",
            hover_data={"requests": True, "warm_leads": True},
            color_continuous_scale=[[0, "#DBEAFE"], [0.4, CYAN], [1, BLUE]],
            labels={"requests": "Requests", "warm_leads": "Warm Leads"},
        )
        _geo_fig.update_layout(
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            geo=dict(
                scope="africa",
                projection_type="natural earth",
                showframe=False,
                showcoastlines=True,
                coastlinecolor="#D9E2EC",
                showland=True,
                landcolor="#F8FAFC",
                showocean=True,
                oceancolor="#EFF6FF",
                showcountries=True,
                countrycolor="#D9E2EC",
                bgcolor="rgba(0,0,0,0)",
                fitbounds="locations",
            ),
            coloraxis_colorbar=dict(title="Requests", thickness=12, len=0.6, tickfont=dict(size=10)),
            margin=dict(l=0, r=0, t=8, b=0),
        )
        _map_col, _tbl_col = st.columns([3, 2], gap="medium")
        with _map_col:
            st.plotly_chart(_geo_fig, use_container_width=True)
        with _tbl_col:
            _top_geo = _geo.sort_values("requests", ascending=False).head(12).reset_index(drop=True)
            _max_req = int(_top_geo["requests"].max()) if not _top_geo.empty else 1
            tbl_rows = ""
            for i, row in _top_geo.iterrows():
                _pct = int(row["requests"] / _max_req * 100)
                _wl_badge = (
                    f'<span style="background:{GREEN_SOFT};color:#047857;font-size:10px;'
                    f'font-weight:800;padding:1px 6px;border-radius:999px;margin-left:5px;">'
                    f'{int(row["warm_leads"])} WL</span>'
                ) if int(row["warm_leads"]) > 0 else ""
                tbl_rows += f"""
<div style="display:grid;grid-template-columns:22px 1fr 44px;gap:8px;align-items:center;
  padding:7px 0;border-bottom:1px solid {BORDER};">
  <div style="font-size:11px;font-weight:900;color:{MUTED};text-align:right;">{i+1}</div>
  <div>
    <div style="font-size:12px;font-weight:800;color:{NAVY};">{row['country']}{_wl_badge}</div>
    <div style="height:4px;border-radius:3px;background:{SLATE_SOFT};margin-top:4px;">
      <div style="height:100%;width:{_pct}%;background:{BLUE};border-radius:3px;
        transition:width .4s ease;"></div>
    </div>
  </div>
  <div style="font-size:12px;font-weight:900;color:{BLUE};text-align:right;">{int(row['requests']):,}</div>
</div>"""
            st.markdown(f"""
<div style="background:white;border:1px solid {BORDER};border-radius:16px;
  padding:14px 16px;box-shadow:{SHADOW_S};height:320px;overflow-y:auto;">
  <div style="font-size:10.5px;font-weight:800;text-transform:uppercase;
    letter-spacing:.1em;color:{MUTED};margin-bottom:10px;">
    Live Country Rankings
  </div>
  {tbl_rows}
</div>""", unsafe_allow_html=True)
        if not _top_geo.empty:
            _top_ctry = _top_geo.iloc[0]["country"]
            _top_reqs = int(_top_geo.iloc[0]["requests"])
            _top_wl   = int(_top_geo.iloc[0]["warm_leads"])
            render_insight_note(
                f"<strong>{_top_ctry}</strong> is generating the most live traffic — "
                f"<strong>{_top_reqs:,}</strong> requests, <strong>{_top_wl:,}</strong> warm leads so far.",
                BLUE_SOFT, "#1E40AF"
            )

    # ── Live window context chip + rolling charts (3 per role) ──────
    render_section_label("LIVE ROLLING TREND — SIMULATED LOG STREAM")
    _lv_pct = f"{min(total_seen, 300)}/300"
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;">'
        f'<span style="background:{BLUE_SOFT};color:{BLUE};font-size:11px;font-weight:800;'
        f'padding:5px 11px;border-radius:999px;">Simulated Log Stream</span>'
        f'<span style="background:{SLATE_SOFT};color:{SECONDARY};font-size:11px;font-weight:700;'
        f'padding:5px 11px;border-radius:999px;">Records: {total_seen:,} of {n:,}</span>'
        f'<span style="background:{SLATE_SOFT};color:{SECONDARY};font-size:11px;font-weight:700;'
        f'padding:5px 11px;border-radius:999px;">Refresh: every 3 s</span>'
        f'<span style="background:{GREEN_SOFT};color:#047857;font-size:11px;font-weight:700;'
        f'padding:5px 11px;border-radius:999px;">Replayed from timestamped synthetic IIS records</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    def _chart_card(title: str, subtitle: str) -> None:
        st.markdown(
            f'<div style="background:white;border-radius:14px;padding:14px 14px 4px;'
            f'box-shadow:{SHADOW_S};margin-bottom:8px;">'
            f'<div style="color:{NAVY};font-size:13px;font-weight:700;margin-bottom:2px;">{title}</div>'
            f'<div style="color:{MUTED};font-size:11px;margin-bottom:4px;">{subtitle}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    def _chart_note(text: str) -> None:
        st.markdown(f'<p style="color:{SECONDARY};font-size:11px;margin:0 0 10px;padding:0 2px;">'
                    f'Simulated live view from timestamped synthetic IIS logs. {text}</p>',
                    unsafe_allow_html=True)

    def _collecting_state(msg: str = "Collecting enough live records to build a reliable trend…") -> None:
        st.markdown(
            f'<div style="background:white;border:1px solid {BORDER};border-radius:12px;padding:18px;'
            f'text-align:center;color:{NAVY};font-size:12px;font-weight:700;">{msg}</div>',
            unsafe_allow_html=True,
        )

    def _lc_layout(extra: dict | None = None) -> dict:
        base = dict(height=200, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white",
                    font=dict(color=TEXT, family="Inter,Segoe UI,Arial,sans-serif", size=11),
                    margin=dict(l=8, r=8, t=8, b=8),
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)))
        if extra:
            base.update(extra)
        return base

    if "timestamp" in live_df.columns and not live_df.empty:
        _lc = live_df.copy()
        _lc["minute"] = _lc["timestamp"].dt.floor("5min")
        _enough = len(_lc) >= 10
        _cc1, _cc2, _cc3 = st.columns(3)

        if dashboard == "CyberNova Pulse":
            # Chart 1 — Warm Lead & Demo Activity
            _wl_m = (_lc.groupby("minute")["is_warm_lead"].sum().reset_index(name="warm_leads")
                     if "is_warm_lead" in _lc.columns else pd.DataFrame())
            _dm_m = (_lc[_lc["uri"] == "/scheduledemo.php"].groupby("minute").size().reset_index(name="demo_req")
                     if "uri" in _lc.columns else pd.DataFrame())
            with _cc1:
                _chart_card("Is warm-lead activity growing?",
                             "Warm leads & demo requests per 5-min window")
                if not _enough:
                    _collecting_state()
                elif not _wl_m.empty:
                    _y_max = max(int(_wl_m["warm_leads"].max()), 1)
                    _f1 = go.Figure()
                    _f1.add_trace(go.Scatter(x=_wl_m["minute"], y=_wl_m["warm_leads"],
                        mode="lines+markers", fill="tozeroy", name="Warm Leads",
                        line=dict(color=GREEN, width=2.5), fillcolor="rgba(16,185,129,.12)",
                        marker=dict(size=4)))
                    if not _dm_m.empty:
                        _mg = _wl_m.merge(_dm_m, on="minute", how="left").fillna(0)
                        _f1.add_trace(go.Scatter(x=_mg["minute"], y=_mg["demo_req"],
                            mode="lines+markers", name="Demo Requests",
                            line=dict(color=BLUE, width=2), marker=dict(size=5)))
                    _f1.update_layout(**_lc_layout())
                    _f1.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False)
                    _f1.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False,
                                     range=[0, _y_max * 1.2])
                    st.plotly_chart(_f1, use_container_width=True)
                    _w_last = int(_wl_m["warm_leads"].iloc[-1])
                    _chart_note(f"Latest 5-min window: <strong>{_w_last}</strong> warm leads detected.")

            # Chart 2 — Service Demand Ticker
            with _cc2:
                _chart_card("Which services are getting attention right now?",
                             "Top service request counts in the live stream")
                if not _enough:
                    _collecting_state()
                else:
                    _svc_col = "service_name" if "service_name" in _lc.columns else ("uri" if "uri" in _lc.columns else None)
                    if _svc_col:
                        _svc_c = (_lc[_svc_col].value_counts().head(7)
                                   .reset_index())
                        _svc_c.columns = ["service", "count"]
                        _svc_c = _svc_c.sort_values("count")
                        _f2 = px.bar(_svc_c, x="count", y="service", orientation="h",
                                     color_discrete_sequence=[BLUE])
                        _f2.update_layout(**_lc_layout())
                        _f2.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False,
                                         title=None, range=[0, max(_svc_c["count"].max()*1.1, 1)])
                        _f2.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False, title=None)
                        st.plotly_chart(_f2, use_container_width=True)
                        _top_svc = str(_svc_c["service"].iloc[-1]) if not _svc_c.empty else "—"
                        _chart_note(f"Top live service: <strong>{_top_svc}</strong>.")

            # Chart 3 — Conversion Funnel (with demo AND event separate — FR10)
            with _cc3:
                _chart_card("How is the conversion funnel moving live?",
                             "All requests through to demo and event registrations")
                _f_total  = len(_lc)
                _f_ai     = int((_lc["uri"] == "/ai-assistant.php").sum()) if "uri" in _lc.columns else 0
                _f_warm   = int(_lc["is_warm_lead"].sum()) if "is_warm_lead" in _lc.columns else 0
                _f_demo   = int((_lc["uri"] == "/scheduledemo.php").sum()) if "uri" in _lc.columns else 0
                _f_event  = int((_lc["uri"].isin(["/event.php","/events.php"])).sum()) if "uri" in _lc.columns else 0
                _f_cont   = int((_lc["uri"] == "/contact.php").sum()) if "uri" in _lc.columns else 0
                _fdf2 = pd.DataFrame({
                    "stage": ["All Requests","AI Assist.","Warm Leads","Demo Req.","Event Signup","Contact"],
                    "count": [_f_total, _f_ai, _f_warm, _f_demo, _f_event, _f_cont],
                })
                _f3 = go.Figure(go.Funnel(
                    y=_fdf2["stage"], x=_fdf2["count"],
                    marker=dict(color=[BLUE, CYAN, GREEN, AMBER, "#8B5CF6", "#10B981"]),
                    textinfo="value+percent previous",
                    connector=dict(line=dict(color=BORDER, width=1)),
                ))
                _f3.update_layout(**_lc_layout())
                st.plotly_chart(_f3, use_container_width=True)
                _conv = f"{_f_demo / max(_f_total, 1):.1%}"
                _chart_note(f"Demo and event actions tracked separately. Live demo conversion: <strong>{_conv}</strong>.")

        elif dashboard == "CyberNova Reach":
            _h_m = pd.DataFrame(); _b_m = pd.DataFrame()
            if "is_bot" in _lc.columns:
                _lc["_ttype"] = _lc["is_bot"].map({True: "Bot", False: "Human"})
                _tr_m = _lc.groupby(["minute", "_ttype"]).size().reset_index(name="count")
                _h_m = _tr_m[_tr_m["_ttype"] == "Human"].copy()
                _b_m = _tr_m[_tr_m["_ttype"] == "Bot"].copy()

            # Chart 1 — Human Traffic Trend
            with _cc1:
                _chart_card("Is real audience traffic growing?",
                             "Human vs bot requests per 5-min window")
                if not _enough:
                    _collecting_state()
                elif not _h_m.empty:
                    _y_max_r = max(int(_h_m["count"].max()), 1)
                    _f1r = go.Figure()
                    _f1r.add_trace(go.Scatter(x=_h_m["minute"], y=_h_m["count"],
                        mode="lines+markers", fill="tozeroy", name="Human Traffic",
                        line=dict(color=CYAN, width=2.5), fillcolor="rgba(22,184,199,.12)",
                        marker=dict(size=4)))
                    if not _b_m.empty:
                        _f1r.add_trace(go.Scatter(x=_b_m["minute"], y=_b_m["count"],
                            mode="lines", name="Bot Traffic",
                            line=dict(color=AMBER, width=2, dash="dot")))
                    _f1r.update_layout(**_lc_layout())
                    _f1r.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False)
                    _f1r.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False,
                                      range=[0, _y_max_r * 1.2])
                    st.plotly_chart(_f1r, use_container_width=True)
                    _h_last = int(_h_m["count"].iloc[-1])
                    _chart_note(f"Latest 5-min human traffic: <strong>{_h_last}</strong> requests.")

            # Chart 2 — Human vs Bot Traffic Split
            with _cc2:
                _chart_card("What fraction of live traffic is genuine audience?",
                             "Human vs bot share of the current live window")
                if "is_bot" in _lc.columns:
                    _bot_ct = int(_lc["is_bot"].sum())
                    _hum_ct = len(_lc) - _bot_ct
                    _sp_df = pd.DataFrame({"type": ["Human", "Bot"], "count": [_hum_ct, _bot_ct]})
                    _f2r = px.pie(_sp_df, names="type", values="count",
                                  color="type", color_discrete_map={"Human": CYAN, "Bot": AMBER},
                                  hole=0.55)
                    _f2r.update_traces(textinfo="percent+label", textfont_size=12)
                    _f2r.update_layout(**_lc_layout({"showlegend": False}))
                    st.plotly_chart(_f2r, use_container_width=True)
                    _hum_pct = f"{_hum_ct / max(len(_lc), 1):.0%}"
                    _qual = "clean" if _bot_ct / max(len(_lc), 1) < 0.15 else "elevated bot noise"
                    _chart_note(f"<strong>{_hum_pct}</strong> human — audience quality is <strong>{_qual}</strong>.")

            # Chart 3 — Country Hotzone Ranking
            with _cc3:
                _chart_card("Which markets are most active right now?",
                             "Top countries by request volume in the live window")
                if "country" in _lc.columns:
                    _ctry_lv = (_lc.groupby("country").size().reset_index(name="requests")
                                  .sort_values("requests", ascending=True).tail(8))
                    _f3r = px.bar(_ctry_lv, x="requests", y="country", orientation="h",
                                  color_discrete_sequence=[GREEN])
                    _f3r.update_layout(**_lc_layout())
                    _f3r.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False,
                                      title=None, range=[0, max(_ctry_lv["requests"].max()*1.1, 1)])
                    _f3r.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False, title=None)
                    st.plotly_chart(_f3r, use_container_width=True)
                    _top_c = str(_ctry_lv["country"].iloc[-1]) if not _ctry_lv.empty else "—"
                    _chart_note(f"Top live market: <strong>{_top_c}</strong>.")
                else:
                    _collecting_state("No geographic activity available for this filter context.")

        else:  # CyberNova Horizon
            # Chart 1 — Strategic Demand (multi-signal grouped bar)
            with _cc1:
                _chart_card("Is strategic demand growing in real time?",
                             "High-intent signals per 5-min window — warm leads, demos, AI, events")
                if not _enough:
                    _collecting_state()
                else:
                    _sig_wl = (_lc.groupby("minute")["is_warm_lead"].sum().reset_index(name="warm_leads")
                               if "is_warm_lead" in _lc.columns else pd.DataFrame())
                    if not _sig_wl.empty:
                        _all_mins = _sig_wl[["minute"]].copy()
                        for _col_name, _uri_val, _label in [
                            ("demo_req",  "/scheduledemo.php", "Demo Requests"),
                            ("ai_req",    "/ai-assistant.php", "AI Assistant"),
                            ("event_req", "/event.php",        "Event Signup"),
                        ]:
                            if "uri" in _lc.columns:
                                _tmp = (_lc[_lc["uri"] == _uri_val]
                                        .groupby("minute").size().reset_index(name=_col_name))
                                _all_mins = _all_mins.merge(_tmp, on="minute", how="left")
                            else:
                                _all_mins[_col_name] = 0
                        _all_mins = _all_mins.fillna(0)
                        _all_mins = _sig_wl.merge(_all_mins.drop(columns=["minute"], errors="ignore"),
                                                  left_index=True, right_index=True, how="left").fillna(0)
                        _all_mins = _sig_wl.copy()
                        for _col_name, _uri_val in [
                            ("demo_req",  "/scheduledemo.php"),
                            ("ai_req",    "/ai-assistant.php"),
                            ("event_req", "/event.php"),
                        ]:
                            if "uri" in _lc.columns:
                                _tmp = (_lc[_lc["uri"] == _uri_val]
                                        .groupby("minute").size().reset_index(name=_col_name))
                                _all_mins = _all_mins.merge(_tmp, on="minute", how="left")
                            else:
                                _all_mins[_col_name] = 0
                        _all_mins = _all_mins.fillna(0)
                        _y_max_h = max(int(_all_mins["warm_leads"].max()), 1)
                        _f1h = go.Figure()
                        _f1h.add_trace(go.Bar(x=_all_mins["minute"], y=_all_mins["warm_leads"],
                            name="Warm Leads", marker_color=GREEN, opacity=0.85))
                        _f1h.add_trace(go.Bar(x=_all_mins["minute"], y=_all_mins.get("demo_req", 0),
                            name="Demo Req.", marker_color=BLUE, opacity=0.75))
                        _f1h.add_trace(go.Bar(x=_all_mins["minute"], y=_all_mins.get("ai_req", 0),
                            name="AI Assist.", marker_color=CYAN, opacity=0.75))
                        _f1h.add_trace(go.Bar(x=_all_mins["minute"], y=_all_mins.get("event_req", 0),
                            name="Event Signup", marker_color=AMBER, opacity=0.75))
                        if "is_anomaly" in _lc.columns:
                            _apts = _lc[_lc["is_anomaly"]].groupby("minute").size().reset_index(name="anoms")
                            if not _apts.empty:
                                _f1h.add_trace(go.Scatter(x=_apts["minute"], y=_apts["anoms"],
                                    mode="markers", name="Anomaly",
                                    marker=dict(color="#EF4444", size=10, symbol="x")))
                        _f1h.update_layout(**_lc_layout({"barmode": "stack"}))
                        _f1h.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False)
                        _f1h.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False,
                                          range=[0, _y_max_h * 1.25])
                        st.plotly_chart(_f1h, use_container_width=True)
                        _d_last = int(_all_mins["warm_leads"].iloc[-1])
                        _chart_note(f"Multi-signal demand view. Latest 5-min warm leads: <strong>{_d_last}</strong>.")
                    else:
                        _collecting_state("No strategic demand events in the current live window yet.")

            # Chart 2 — HTTP Health Monitor (status codes only — not human/bot)
            with _cc2:
                _chart_card("Is platform health holding under live load?",
                             "HTTP status distribution in the live window")
                _http_col = "http_status" if "http_status" in _lc.columns else ("status_code" if "status_code" in _lc.columns else None)
                if _http_col:
                    def _sband(s):
                        try:
                            c = int(s)
                            if 200 <= c < 300: return "2xx OK"
                            if 300 <= c < 400: return "3xx Redirect"
                            if 400 <= c < 500: return "4xx Error"
                            return "5xx Error"
                        except Exception:
                            return "Unknown"
                    _lc["_sb"] = _lc[_http_col].apply(_sband)
                    _sc_ct = _lc["_sb"].value_counts().reset_index()
                    _sc_ct.columns = ["status", "count"]
                    _scmap = {"2xx OK": GREEN, "3xx Redirect": BLUE,
                               "4xx Error": AMBER, "5xx Error": "#D97706", "Unknown": MUTED}
                    _f2h = px.bar(_sc_ct, x="status", y="count",
                                  color="status", color_discrete_map=_scmap)
                    _f2h.update_layout(**_lc_layout({"showlegend": False}))
                    _f2h.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False, title=None)
                    _f2h.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False,
                                      title=None, range=[0, max(_sc_ct["count"].max()*1.15, 1)])
                    st.plotly_chart(_f2h, use_container_width=True)
                    _err_n = int(_lc["_sb"].isin(["4xx Error", "5xx Error"]).sum())
                    _err_r = f"{_err_n / max(len(_lc), 1):.1%}"
                    _health = "healthy" if _err_n / max(len(_lc), 1) < 0.05 else "under stress"
                    _chart_note(f"Most live requests are successful when 2xx dominates. Error rate: <strong>{_err_r}</strong> — platform <strong>{_health}</strong>.")
                else:
                    _collecting_state("HTTP status data not available in this stream window.")

            # Chart 3 — Anomaly Pulse
            with _cc3:
                _chart_card("Are anomalies spiking in the live window?",
                             "Live anomaly events per 5-minute window")
                if "is_anomaly" in _lc.columns:
                    _anom_m = (_lc.groupby("minute")["is_anomaly"]
                                  .sum().reset_index(name="anomalies"))
                    _tot_a = int(_anom_m["anomalies"].sum()) if not _anom_m.empty else 0
                    if _tot_a == 0:
                        st.markdown(
                            f'<div style="background:{GREEN_SOFT};border-radius:12px;padding:18px;'
                            f'text-align:center;color:#047857;font-size:12px;font-weight:700;">'
                            f'No anomaly events detected in the current live window.</div>',
                            unsafe_allow_html=True,
                        )
                        _chart_note("Operations nominal — no anomaly signals in current stream window.")
                    else:
                        _acolors = [AMBER if v > 0 else SLATE_SOFT for v in _anom_m["anomalies"]]
                        _f3h = go.Figure(go.Bar(
                            x=_anom_m["minute"], y=_anom_m["anomalies"],
                            marker_color=_acolors, name="Anomalies",
                        ))
                        _f3h.update_layout(**_lc_layout())
                        _f3h.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False)
                        _f3h.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False,
                                          range=[0, max(_anom_m["anomalies"].max()*1.2, 1)])
                        st.plotly_chart(_f3h, use_container_width=True)
                        _risk = "risk elevated — review security log" if _tot_a > 5 else "minor anomaly signal — monitor"
                        _chart_note(f"Live anomaly count: <strong>{_tot_a}</strong> — <strong>{_risk}</strong>.")
                else:
                    _collecting_state("Anomaly data not available in this stream window.")

    # ── Live Activity Feed — last 12 from ring buffer ──────────────
    render_section_label("OPERATIONAL PULSE — LIVE ACTIVITY FEED")
    st.markdown(f"""
<div style="background:white;border:1px solid {BORDER};border-radius:18px;
  box-shadow:{SHADOW_S};padding:20px;margin-bottom:4px;">
  <h3 style="margin:0 0 4px;color:{NAVY};font-size:17px;">Live Activity Feed</h3>
  <p style="margin:0 0 14px;color:{MUTED};font-size:13px;">
    Streaming one record every 3 seconds from the log stream
    &mdash; {total_seen:,} records seen so far, latest first.
  </p>""", unsafe_allow_html=True)
    render_live_feed(live_df.head(60), role, limit=12)
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# PDF REPORT BUILDER
# ─────────────────────────────────────────────────────────────────
def _make_chart_image(fig, width_cm: float = 15, height_cm: float = 7) -> RLImage:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    buf.seek(0)
    plt.close(fig)
    return RLImage(buf, width=width_cm*cm, height=height_cm*cm)


def _chart_requests_by_service(df: pd.DataFrame):
    counts = (df["service_name"].value_counts().head(6)
              if "service_name" in df.columns else pd.Series(dtype=int))
    fig, ax = plt.subplots(figsize=(7, 3.2))
    if counts.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
    else:
        colors = ["#2563FF","#16B8C7","#10B981","#F59E0B","#8B5CF6","#EF4444"][:len(counts)]
        bars = ax.barh(counts.index[::-1], counts.values[::-1], color=colors[::-1],
                       height=0.6, edgecolor="none")
        ax.bar_label(bars, fmt="%d", padding=4, fontsize=8, color="#0B1F3A", fontweight="bold")
        ax.set_xlabel("Requests", fontsize=9, color="#374151")
        ax.tick_params(axis="y", labelsize=8, colors="#0B1F3A")
        ax.tick_params(axis="x", labelsize=8, colors="#374151")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D9E2EC")
        ax.spines["bottom"].set_color("#D9E2EC")
        ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.set_title("Requests by Service", fontsize=11, fontweight="bold", color="#0B1F3A", pad=8)
    fig.tight_layout()
    return fig


def _chart_daily_requests(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(7, 3.0))
    if "date" not in df.columns or df.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
    else:
        daily = df.groupby(pd.to_datetime(df["date"]).dt.date).size()
        ax.plot(range(len(daily)), daily.values, color="#2563FF", linewidth=2,
                marker="o", markersize=3.5, markerfacecolor="#16B8C7")
        ax.fill_between(range(len(daily)), daily.values, alpha=0.12, color="#2563FF")
        ax.set_xticks(range(0, len(daily), max(1, len(daily)//6)))
        ax.set_xticklabels([str(d) for d in list(daily.index)[::max(1, len(daily)//6)]],
                           fontsize=7, rotation=30, ha="right", color="#374151")
        ax.tick_params(axis="y", labelsize=8, colors="#374151")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D9E2EC")
        ax.spines["bottom"].set_color("#D9E2EC")
        ax.set_facecolor("white")
        ax.set_ylabel("Requests", fontsize=9, color="#374151")
    fig.patch.set_facecolor("white")
    ax.set_title("Daily Request Volume", fontsize=11, fontweight="bold", color="#0B1F3A", pad=8)
    fig.tight_layout()
    return fig


def _chart_top_countries(df: pd.DataFrame):
    counts = (df["country"].value_counts().head(6)
              if "country" in df.columns else pd.Series(dtype=int))
    fig, ax = plt.subplots(figsize=(7, 3.2))
    if counts.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
    else:
        colors = ["#16B8C7","#2563FF","#10B981","#F59E0B","#8B5CF6","#EF4444"][:len(counts)]
        bars = ax.barh(counts.index[::-1], counts.values[::-1], color=colors[::-1],
                       height=0.6, edgecolor="none")
        ax.bar_label(bars, fmt="%d", padding=4, fontsize=8, color="#0B1F3A", fontweight="bold")
        ax.set_xlabel("Requests", fontsize=9, color="#374151")
        ax.tick_params(axis="y", labelsize=8, colors="#0B1F3A")
        ax.tick_params(axis="x", labelsize=8, colors="#374151")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D9E2EC")
        ax.spines["bottom"].set_color("#D9E2EC")
        ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    ax.set_title("Top Countries by Traffic", fontsize=11, fontweight="bold", color="#0B1F3A", pad=8)
    fig.tight_layout()
    return fig


def build_pdf_report(
    dashboard: str, role: str, period: str,
    filters: dict, kpis: list[dict],
    bullets: list[str], evidence_df: pd.DataFrame,
    chart_df: pd.DataFrame | None = None,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2.2*cm, bottomMargin=2*cm)
    sty  = getSampleStyleSheet()
    navy = rlc.HexColor("#0B1F3A")
    blue = rlc.HexColor("#2563FF")
    cyan = rlc.HexColor("#16B8C7")
    grey = rlc.HexColor("#52606D")
    light = rlc.HexColor("#F3F4F6")

    h1  = ParagraphStyle("h1", parent=sty["Heading1"], textColor=navy,
                         fontSize=22, spaceAfter=2, spaceBefore=0, leading=26)
    h2  = ParagraphStyle("h2", parent=sty["Heading2"], textColor=blue,
                         fontSize=13, spaceAfter=4, spaceBefore=12, leading=18)
    bdy = ParagraphStyle("bd", parent=sty["Normal"],   textColor=navy,
                         fontSize=10, spaceAfter=4, leading=15)
    sub = ParagraphStyle("su", parent=sty["Normal"],   textColor=grey,
                         fontSize=9,  spaceAfter=3, leading=14)
    cap = ParagraphStyle("cp", parent=sty["Normal"],   textColor=grey,
                         fontSize=7.5, spaceAfter=2, leading=11)

    els: list = []

    # ── Cover header ──────────────────────────────────────────────
    els += [
        Paragraph("CyberNova Analytics Ltd", h1),
        Paragraph(f"{dashboard} — {period} Report", h2),
        Paragraph(
            f"<b>Role:</b> {role}&nbsp;&nbsp;&nbsp;"
            f"<b>Period:</b> {filters.get('start','')} to {filters.get('end','')}&nbsp;&nbsp;&nbsp;"
            f"<b>Generated:</b> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
            sub,
        ),
        HRFlowable(width="100%", thickness=1.5, color=blue, spaceAfter=10),
    ]

    # ── Filter context table ──────────────────────────────────────
    els.append(Paragraph("Filter Context", h2))
    frows = [
        ["Period",    f"{filters.get('start','')} → {filters.get('end','')}"],
        ["Countries", ", ".join(filters.get("countries",[])) or "All countries"],
        ["Services",  ", ".join(filters.get("services",[])) or "All services"],
        ["HTTP Status", ", ".join(filters.get("status_classes",[])) or "All"],
        ["Bot Traffic", "Included" if filters.get("include_bots") else "Excluded"],
    ]
    ft = Table([["Filter", "Value"]] + frows, colWidths=[4.5*cm, 12.5*cm])
    ft.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), navy),
        ("TEXTCOLOR",     (0,0), (-1,0), rlc.white),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [light, rlc.white]),
        ("GRID",          (0,0), (-1,-1), 0.3, rlc.HexColor("#D9E2EC")),
        ("PADDING",       (0,0), (-1,-1), 6),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    els += [ft, Spacer(1, 14)]

    # ── KPIs ──────────────────────────────────────────────────────
    if kpis:
        els.append(Paragraph("Key Performance Indicators", h2))
        kr = [[k.get("label",""), k.get("value",""), k.get("note","")] for k in kpis]
        kt = Table([["Metric", "Value", "Note"]] + kr, colWidths=[7*cm, 4*cm, 6*cm])
        kt.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), rlc.HexColor("#2563FF")),
            ("TEXTCOLOR",     (0,0), (-1,0), rlc.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [rlc.HexColor("#DBEAFE"), rlc.white]),
            ("GRID",          (0,0), (-1,-1), 0.3, rlc.HexColor("#D9E2EC")),
            ("PADDING",       (0,0), (-1,-1), 7),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        els += [kt, Spacer(1, 14)]

    # ── Insights ──────────────────────────────────────────────────
    if bullets:
        els.append(Paragraph("Insights", h2))
        for b in bullets:
            clean = b.replace("<strong>", "").replace("</strong>", "")
            els.append(Paragraph(f"• &nbsp;{clean}", bdy))
        els.append(Spacer(1, 10))

    # ── 3 Charts ─────────────────────────────────────────────────
    data_for_charts = chart_df if (chart_df is not None and not chart_df.empty) else evidence_df
    if not data_for_charts.empty:
        els.append(Paragraph("Analytics Charts", h2))
        try:
            els.append(_make_chart_image(_chart_requests_by_service(data_for_charts), 15, 6.5))
            els.append(Spacer(1, 8))
            els.append(_make_chart_image(_chart_daily_requests(data_for_charts), 15, 6))
            els.append(Spacer(1, 8))
            els.append(_make_chart_image(_chart_top_countries(data_for_charts), 15, 6.5))
            els.append(Spacer(1, 12))
        except Exception:
            pass

    # ── Evidence table ────────────────────────────────────────────
    if not evidence_df.empty:
        els.append(Paragraph("Evidence (Top 25 rows)", h2))
        show_cols = [c for c in ["timestamp","country","service_name","event_type",
                                 "segment","status_class","is_warm_lead","response_time_ms"]
                     if c in evidence_df.columns]
        evd = evidence_df[show_cols].head(25) if show_cols else evidence_df.head(25)
        er2 = [list(evd.columns)] + evd.astype(str).values.tolist()
        ncols = len(evd.columns)
        col_w = 17*cm / ncols
        et = Table(er2, colWidths=[col_w]*ncols, repeatRows=1)
        et.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,0), rlc.HexColor("#1F3A5F")),
            ("TEXTCOLOR",     (0,0), (-1,0), rlc.white),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0), (-1,-1), 7.5),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [rlc.HexColor("#F0F7FF"), rlc.white]),
            ("GRID",          (0,0), (-1,-1), 0.3, rlc.HexColor("#D9E2EC")),
            ("PADDING",       (0,0), (-1,-1), 5),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        els.append(et)

    # ── Footer ────────────────────────────────────────────────────
    els += [
        Spacer(1, 18),
        HRFlowable(width="100%", thickness=0.5, color=rlc.HexColor("#D9E2EC"), spaceAfter=6),
        Paragraph(
            "Generated from CyberNova synthetic IIS web-log dataset · "
            "CET333 Product Development prototype · Rule-based insights only.",
            cap,
        ),
    ]
    doc.build(els)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────
# REPORT SECTION (export buttons row)
# ─────────────────────────────────────────────────────────────────
def render_report_section(
    dashboard: str, role: str, filters: dict,
    kpis: list[dict], bullets: list[str],
    fdf: pd.DataFrame, evidence_df: pd.DataFrame,
    evidence_name: str = "evidence",
) -> None:
    render_section_label("REPORTS & EXPORTS")
    _now_str = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
    _c_str  = ", ".join(filters.get("countries",[])) or "All countries"
    _s_str  = ", ".join(filters.get("services",[])) or "All services"
    st.markdown(f"""
<div style="background:white;border:1px solid {BORDER};border-radius:22px;
  box-shadow:0 4px 6px rgba(11,31,58,.04),0 12px 28px rgba(11,31,58,.08);
  padding:26px 28px;margin-bottom:20px;">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:24px;
    flex-wrap:wrap;">
    <div style="flex:1;min-width:260px;">
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:{MUTED};
        font-weight:900;margin-bottom:7px;">Evidence Pack</div>
      <h3 style="margin:0 0 5px;color:{NAVY};font-size:18px;font-weight:900;
        letter-spacing:-.03em;">Export &amp; Download</h3>
      <p style="margin:0;color:{MUTED};font-size:13px;font-weight:500;">
        Generate reports and download data for offline use.
      </p>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding-top:4px;">
      <span style="background:{BLUE_SOFT};color:{BLUE};padding:5px 11px;border-radius:999px;
        font-size:11px;font-weight:800;">Rows: {len(fdf):,}</span>
      <span style="background:{SLATE_SOFT};color:{SECONDARY};padding:5px 11px;border-radius:999px;
        font-size:11px;font-weight:800;">Filters: {_c_str[:22]}</span>
      <span style="background:{GREEN_SOFT};color:#047857;padding:5px 11px;border-radius:999px;
        font-size:11px;font-weight:800;">Generated: {_now_str}</span>
    </div>
  </div>
  <div style="margin-top:18px;border-top:1px solid {BORDER};padding-top:14px;">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;
      font-size:12px;color:{SECONDARY};">
      <div><strong style="color:{NAVY};">Weekly PDF includes:</strong>
        KPI summary &middot; live pulse snapshot &middot; top hotzones &middot; evidence table</div>
      <div><strong style="color:{NAVY};">Monthly PDF includes:</strong>
        Trend analysis &middot; forecast &middot; regional analysis &middot; recommendations</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
    # Date-bounded slices for weekly and monthly reports
    _today       = date.today()
    _week_start  = _today - timedelta(days=7)
    _month_ago   = date(_today.year if _today.month > 1 else _today.year - 1,
                        _today.month - 1 if _today.month > 1 else 12,
                        _today.day)

    def _slice_df(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
        if df.empty or "date" not in df.columns:
            return df
        d = pd.to_datetime(df["date"], errors="coerce").dt.date
        return df[(d >= start) & (d <= end)].reset_index(drop=True)

    _weekly_filters  = {**filters, "start": str(_week_start),  "end": str(_today)}
    _monthly_filters = {**filters, "start": str(_month_ago),   "end": str(_today)}
    _weekly_evd  = _slice_df(evidence_df, _week_start, _today)
    _monthly_evd = _slice_df(evidence_df, _month_ago,  _today)
    _weekly_fdf  = _slice_df(fdf,         _week_start, _today)
    _monthly_fdf = _slice_df(fdf,         _month_ago,  _today)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        try:
            pdf_w = build_pdf_report(dashboard, role, "Weekly",
                                     _weekly_filters, kpis, bullets,
                                     _weekly_evd, chart_df=_weekly_fdf)
            st.download_button("Weekly PDF Report", data=pdf_w,
                               file_name=f"{dashboard.lower().replace(' ','_')}_weekly.pdf",
                               mime="application/pdf", use_container_width=True,
                               key=f"pdf_w_{dashboard}")
        except Exception as e:
            st.error(f"PDF error: {e}")
    with c2:
        try:
            pdf_m = build_pdf_report(dashboard, role, "Monthly",
                                     _monthly_filters, kpis, bullets,
                                     _monthly_evd, chart_df=_monthly_fdf)
            st.download_button("Monthly PDF Report", data=pdf_m,
                               file_name=f"{dashboard.lower().replace(' ','_')}_monthly.pdf",
                               mime="application/pdf", use_container_width=True,
                               key=f"pdf_m_{dashboard}")
        except Exception as e:
            st.error(f"PDF error: {e}")
    with c3:
        st.download_button(f"Download {evidence_name} CSV",
                           data=to_csv(evidence_df),
                           file_name=f"{evidence_name.lower().replace(' ','_')}.csv",
                           mime="text/csv", use_container_width=True,
                           key=f"evd_csv_{dashboard}")
    with c4:
        st.download_button("Download Filtered Data CSV",
                           data=to_csv(fdf),
                           file_name=f"{dashboard.lower().replace(' ','_')}_data.csv",
                           mime="text/csv", use_container_width=True,
                           key=f"fdf_csv_{dashboard}")
    st.caption("Rule-based insights only. CET333 Product Development prototype — not for production.")
    with st.expander("Methodology Note & ETL Pipeline", expanded=False):
        # ── ETL Flow Diagram — inline SVG icons, no emoji ─────────
        _nd = (
            f"border:1.5px solid {BORDER};border-radius:14px;padding:10px 14px;"
            f"text-align:center;font-size:12px;font-weight:800;color:{NAVY};"
            f"min-width:108px;box-shadow:0 2px 8px rgba(11,31,58,.07);"
        )
        _sb = f"font-size:10px;font-weight:500;color:{MUTED};margin-top:4px;line-height:1.45;"
        _ar = (
            f"display:flex;align-items:center;justify-content:center;"
            f"color:{MUTED};font-size:18px;font-weight:900;padding:0 2px;flex-shrink:0;"
        )

        # Inline SVG icons (stroke-based, no emoji, consistent 16×16)
        _S = 'width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-bottom:2px;"'
        def _svg(paths, color=NAVY):
            s = _S.replace('"{c}"', f'"{color}"')
            return f'<svg {s}>{paths}</svg>'

        IC_CONFIG  = _svg('<path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/>')
        IC_GEN     = _svg('<circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>')
        IC_LOGS    = _svg('<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>')
        IC_ETL     = _svg('<polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>')
        IC_CLEAN   = _svg('<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>')
        IC_ANAL    = _svg('<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/>')
        IC_DASH    = _svg('<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>')
        IC_EXPORT  = _svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>')
        IC_CRISP   = _svg('<polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>')

        def _node(icon_svg, label, sub, grad_a, grad_b=None):
            bg = grad_b or SLATE_SOFT
            return (
                f'<div style="{_nd}background:linear-gradient(135deg,{grad_a},{bg});">'
                f'<div style="display:flex;align-items:center;justify-content:center;gap:5px;">'
                f'{icon_svg}'
                f'<span>{label}</span>'
                f'</div>'
                f'<div style="{_sb}">{sub}</div>'
                f'</div>'
            )
        def _arrow():
            return f'<div style="{_ar}">&#8594;</div>'

        _etl_html = (
            f'<div style="background:{SLATE_SOFT};border-radius:16px;'
            f'padding:20px 24px 16px;margin:4px 0 12px;font-family:Inter,Segoe UI,sans-serif;">'

            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">'
            f'{IC_CRISP}'
            f'<span style="font-size:10px;text-transform:uppercase;letter-spacing:.15em;'
            f'font-weight:900;color:{MUTED};">ETL Pipeline — CRISP-DM</span>'
            f'</div>'

            f'<div style="display:flex;align-items:center;flex-wrap:wrap;gap:8px;">'
            + _node(IC_CONFIG, "Config",    "config.yaml<br>seed = 333",                BLUE_SOFT)
            + _arrow()
            + _node(IC_GEN,    "Generator", "Faker + IIS<br>W3C format",                CYAN_SOFT)
            + _arrow()
            + _node(IC_LOGS,   "Raw Logs",  "Excel + CSV<br>&ge;1,000 rows",            SLATE_SOFT, "#E2E8F0")
            + _arrow()
            + _node(IC_ETL,    "ETL Layer", "load_data()<br>IP resolve &middot; parse", AMBER_SOFT)
            + _arrow()
            + _node(IC_CLEAN,  "Clean DF",  "Merged &middot; typed<br>sorted &middot; filtered", BLUE_SOFT)
            + _arrow()
            + _node(IC_ANAL,   "Analytics", "KPIs &middot; segments<br>stats &middot; forecast",  GREEN_SOFT)
            + _arrow()
            + _node(IC_DASH,   "Dashboard", "Sales &middot; Mktg<br>Executive",         "#EDE9FE")
            + _arrow()
            + _node(IC_EXPORT, "Exports",   "PDF reports<br>CSV evidence",              AMBER_SOFT)
            + f'</div>'

            f'<div style="margin-top:12px;padding-top:10px;display:flex;align-items:center;gap:8px;'
            f'border-top:1px solid {BORDER};font-size:11px;font-weight:700;color:{SECONDARY};">'
            f'<strong>CRISP-DM:</strong>&nbsp;'
            f'Business Understanding &rarr; Data Understanding &rarr; Preparation'
            f' &rarr; Modelling &rarr; Evaluation &rarr; Deployment'
            f'</div>'
            f'</div>'
        )
        # st.html() renders raw HTML without markdown sanitisation (Streamlit ≥1.31).
        # Falls back gracefully to st.markdown for older installs.
        try:
            st.html(_etl_html)
        except AttributeError:
            st.markdown(_etl_html, unsafe_allow_html=True)

        st.markdown(f"""
**Dataset:** Synthetically generated using an IIS W3C Extended Log Format generator
seeded with `random_seed: 333` for full reproducibility. Country distribution reflects
realistic Southern African proportions (≥30% Botswana). No real personal data used.

**ETL Pipeline (`load_data()`):** Loads raw Excel log file, joins with enriched CSV for
derived columns (IP-to-country, session IDs, segments, event types, anomaly flags).
Timestamps are parsed, boolean columns cast, and records sorted chronologically. A
data quality summary (raw rows → usable rows) is shown on load.

**Live layer:** The live stream section replays timestamped synthetic IIS records through a
ring buffer (up to 300 records, advancing one every 3 seconds via Streamlit's
`@st.fragment(run_every=3)` mechanism). This simulates real-time operational monitoring
without requiring a live data pipeline.

**Forecasting:** All forecast charts use simple linear regression (`numpy.polyfit`) on daily
aggregated warm-lead or session counts. This is a planning-level trend estimate, not a
production model. Selected for interpretability over ARIMA/Prophet given the dataset scale.

**Segmentation:** Four behavioural tiers — High-intent (demo/event pages), Product-curious
(AI/prototype pages), General browser (index/about), and Bot/crawler (user-agent detection).
Tier quality is confirmed by inspecting whether each tier produces a meaningfully distinct
traffic profile.

**Role-based access:** Prototype-level only. Production would require password hashing,
audit logging, session management, and full RBAC.

**Ethics:** No real personal data used. All IPs are algorithmically constructed from synthetic
country prefixes and are not traceable to any real individual. Dataset fully synthetic.""")


# ─────────────────────────────────────────────────────────────────
# DASHBOARD 1 — CYBERNOVA PULSE  (Sales)
# ─────────────────────────────────────────────────────────────────
def show_pulse(fdf: pd.DataFrame, filters: dict, role: str) -> None:
    render_hero(
        "CyberNova Pulse",
        "Sales Command Center",
        "Real-time lead signals, service demand, and funnel diagnostics. "
        "Identify which leads to prioritise, which service to lead with, and where the pipeline needs attention.",
    )
    render_story_strip(["Context","Live Pulse","Sales Insight","Lead Diagnostics","Action Queue","Export"], BLUE)
    # Action row
    _, a1, a2 = st.columns([4,1,1])
    with a1:
        if st.button("Refresh Data", key="pulse_refresh", use_container_width=True):
            load_data.clear(); st.rerun()
    with a2:
        st.download_button("Export CSV", data=to_csv(fdf),
                           file_name="pulse_export.csv", mime="text/csv",
                           use_container_width=True, key="pulse_exp_csv")
    render_context_chips(filters, role, len(fdf))

    if fdf.empty:
        render_empty_state(); return

    m = calculate_sales_metrics(fdf)
    warm = fdf[fdf["is_warm_lead"]]

    # ── SIGNAL — KPI row ──────────────────────────────────────────
    render_section_label("SIGNAL — KEY METRICS")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    max_ts   = fdf["date"].max()
    week_ago = max_ts - pd.Timedelta(days=7)
    prev_24h = int(fdf[fdf["date"] == max_ts - pd.Timedelta(days=1)]["is_warm_lead"].sum())
    with k1: render_kpi_card("New Warm Leads (24h)", f"{m['leads_24h']:,}",
                              f"vs {prev_24h:,} yesterday", m["leads_24h"]>=prev_24h)
    with k2: render_kpi_card("Weekly Warm Leads", f"{m['leads_7d']:,}", "Last 7 days", True, CYAN)
    with k3: render_kpi_card("AI → Demo Conv.", f"{m['ai_conv']:.1%}",
                              "strong" if m["ai_conv"]>=0.15 else "moderate" if m["ai_conv"]>=0.05 else "weak",
                              m["ai_conv"]>=0.05, GREEN)
    with k4: render_kpi_card("Top Warm Market", m["top_country"], "By warm-lead volume", True, AMBER)
    with k5: render_kpi_card("Top Service Demand", m["top_service"][:22],
                              "Highest warm-lead interest", True, BLUE)
    with k6: render_kpi_card("Top Lead Action", m["top_action"][:20],
                              "Most frequent event type", True, CYAN)

    # ── ROLE SUMMARY BANNER — TODAY'S SALES FOCUS ────────────────
    _ia_hotzone  = m.get("top_country","—")
    _ia_service  = m.get("top_service","—")
    _ia_action   = m.get("top_action","—")
    _ia_conv     = m.get("ai_conv",0)
    _ia_step     = ("Prioritise rapid follow-up — strong AI conversion signal." if _ia_conv>=0.15
                    else "Focus on reducing service-to-demo drop-off." if m.get("funnel_drop",True)
                    else "Pipeline healthy — maintain follow-up cadence.")
    st.markdown(f"""
<div style="background:white;border:1px solid #BFDBFE;border-radius:22px;
  box-shadow:0 4px 6px rgba(37,99,255,.05),0 12px 32px rgba(37,99,255,.10);
  padding:24px 28px;margin-bottom:22px;position:relative;overflow:hidden;">
  <div style="position:absolute;right:-60px;top:-60px;width:220px;height:220px;
    border-radius:50%;background:rgba(37,99,255,.05);pointer-events:none;"></div>
  <div style="position:absolute;left:-30px;bottom:-40px;width:160px;height:160px;
    border-radius:50%;background:rgba(22,184,199,.05);pointer-events:none;"></div>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;position:relative;">
    <span style="font-size:10px;text-transform:uppercase;letter-spacing:.16em;
      font-weight:900;color:{BLUE};">Today's Sales Focus</span>
    <span style="height:1px;background:linear-gradient(90deg,#BFDBFE,transparent);flex:1;"></span>
    <span style="font-size:11px;color:{MUTED};font-weight:700;">AI Conv. Rate:
      <strong style="color:{'#047857' if _ia_conv>=0.10 else NAVY};">{_ia_conv:.1%}</strong>
    </span>
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px;position:relative;">
    <div style="border-right:1px solid {BORDER};padding-right:20px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Top Hotzone</div>
      <div style="font-size:19px;font-weight:900;color:{NAVY};letter-spacing:-.03em;
        line-height:1.1;">{_ia_hotzone}</div>
      <div style="font-size:11px;color:{SECONDARY};margin-top:4px;font-weight:600;">
        Highest warm-lead market</div>
    </div>
    <div style="border-right:1px solid {BORDER};padding-right:20px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Top Service</div>
      <div style="font-size:15px;font-weight:900;color:{NAVY};line-height:1.2;">{_ia_service[:26]}</div>
      <div style="font-size:11px;color:{SECONDARY};margin-top:4px;font-weight:600;">
        Lead with this in outreach</div>
    </div>
    <div style="border-right:1px solid {BORDER};padding-right:20px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Highest-Intent Action</div>
      <div style="font-size:15px;font-weight:900;color:{NAVY};line-height:1.2;">{_ia_action[:26]}</div>
      <div style="font-size:11px;color:{SECONDARY};margin-top:4px;font-weight:600;">
        Most frequent lead event</div>
    </div>
    <div>
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Recommended Follow-Up</div>
      <div style="font-size:13px;font-weight:800;color:{NAVY};line-height:1.4;">{_ia_step}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── LIVE PULSE + FEED  (auto-refreshes every 3 s) ────────────
    render_section_label("LIVE PULSE — STREAMING FROM LOG STREAM")
    render_live_section(fdf, role, "CyberNova Pulse")

    # ── INSIGHT ───────────────────────────────────────────────────
    render_section_label("SALES INSIGHT")
    bullets, action = generate_sales_story(fdf, m)
    render_story_card("Sales Insight", "What the current web activity suggests Sales should prioritise.",
                      bullets, action, BLUE, BLUE_SOFT)

    # ── DIAGNOSIS — STRATEGIC ANALYTICS ──────────────────────────
    render_section_label("DIAGNOSIS — STRATEGIC ANALYTICS")
    # Row 1: origins + service demand
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            render_card_header("Where did warm leads come from?", "Warm lead events by country")
            lc = warm["country"].value_counts().head(12).reset_index()
            lc.columns = ["country","leads"]
            if not lc.empty:
                fig = px.bar(lc.sort_values("leads"), x="leads", y="country", orientation="h",
                             color_discrete_sequence=[BLUE])
                st.plotly_chart(cs(fig), use_container_width=True)
                render_insight_note(f"Top market: <strong>{lc['country'].iloc[-1]}</strong> with {int(lc['leads'].iloc[-1]):,} warm lead events.")
            else:
                render_empty_state("No warm leads in current filters")
    with c2:
        with st.container(border=True):
            render_card_header("What service should Sales lead with?", "Warm lead demand by service")
            ls = warm["service_name"].value_counts().head(10).reset_index()
            ls.columns = ["service","leads"]
            if not ls.empty:
                fig = px.bar(ls.sort_values("leads"), x="leads", y="service", orientation="h",
                             color_discrete_sequence=[CYAN])
                st.plotly_chart(cs(fig), use_container_width=True)
                render_insight_note(f"Lead the conversation with <strong>{ls['service'].iloc[-1]}</strong> — highest warm-lead demand.", CYAN_SOFT, "#0E7490")
            else:
                render_empty_state("No warm lead data")
    # Row 2: demo heatmap + conversion by cohort
    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            render_card_header("When are people most likely to request a demo?", "Demo requests by hour and day")
            demo_df = fdf[fdf["uri"]=="/scheduledemo.php"].copy() if "uri" in fdf.columns else pd.DataFrame()
            if not demo_df.empty and "hour" in demo_df.columns and "day_of_week" in demo_df.columns:
                heat = demo_df.groupby(["day_of_week","hour"]).size().reset_index(name="count")
                piv  = heat.pivot(index="hour", columns="day_of_week", values="count")
                piv  = piv.reindex(columns=[d for d in DAY_ORDER if d in piv.columns]).fillna(0)
                fig  = px.imshow(piv, color_continuous_scale=[[0,"#EEF6FF"],[1,BLUE]],
                                 labels=dict(x="Day",y="Hour",color="Requests"), aspect="auto")
                fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=12,b=10))
                st.plotly_chart(fig, use_container_width=True)
                if m["peak_hour"] is not None:
                    render_insight_note(f"Peak demo intent at <strong>{m['peak_hour']:02d}:00</strong> — align follow-up capacity to this window.")
            else:
                render_empty_state("No demo page requests in current filters")
    with c4:
        with st.container(border=True):
            render_card_header("Are repeat visitors more likely to convert?", "Conversion rate by session cohort")
            if "session_number_for_ip" in fdf.columns:
                sdf = fdf.drop_duplicates("session_id")[["session_number_for_ip","converted_to_lead"]].copy()
                def _coh(n):
                    return "1st" if n==1 else "2nd" if n==2 else "3–5" if n<=5 else "6+"
                sdf["cohort"] = sdf["session_number_for_ip"].apply(_coh)
                cc = sdf.groupby("cohort")["converted_to_lead"].mean().reindex(["1st","2nd","3–5","6+"]).fillna(0).reset_index()
                cc.columns = ["cohort","rate"]
                fig = px.bar(cc, x="cohort", y="rate", text=cc["rate"].map("{:.1%}".format),
                             color_discrete_sequence=[GREEN])
                fig.update_traces(textposition="outside")
                fig.update_yaxes(tickformat=".0%")
                st.plotly_chart(cs(fig), use_container_width=True)
                best = cc.loc[cc["rate"].idxmax(),"cohort"] if not cc.empty else "—"
                render_insight_note(f"<strong>{best} visit</strong> sessions show the highest conversion rate.", GREEN_SOFT, "#047857")
            else:
                render_empty_state("Session data not available")
    # Row 3: pipeline trend + funnel
    c5, c6 = st.columns([1.3, 1])
    with c5:
        with st.container(border=True):
            render_card_header("Is the warm-lead pipeline accelerating or slowing?", "Weekly warm-lead trend")
            wo = fdf[fdf["is_warm_lead"]].copy()
            if not wo.empty:
                wo["week"] = wk(wo["date"])
                wl = wo.groupby("week").size().reset_index(name="warm_leads")
                fig = px.line(wl, x="week", y="warm_leads", markers=True,
                              color_discrete_sequence=[BLUE])
                fig.update_traces(line=dict(width=3), marker=dict(size=7, color=CYAN))
                fig.update_xaxes(tickangle=-30)
                st.plotly_chart(cs(fig), use_container_width=True)
                if len(wl)>=4:
                    half = len(wl)//2
                    fa   = wl["warm_leads"].iloc[:half].mean()
                    la   = wl["warm_leads"].iloc[half:].mean()
                    dir_ = "accelerating" if la>fa*1.05 else ("slowing" if la<fa*0.95 else "stable")
                    render_insight_note(f"Warm-lead pipeline is <strong>{dir_}</strong> ({fa:.1f} → {la:.1f} leads/week).")
            else:
                render_empty_state("No warm lead trend data")
    with c6:
        with st.container(border=True):
            render_card_header("Where in the funnel are we losing leads?", "Index → Service → Demo → Submit")
            idx_s  = fdf[fdf.get("uri",pd.Series())=="/index.html"]["session_id"].nunique() if "uri" in fdf.columns else 0
            svc_s  = fdf[fdf.get("uri",pd.Series()).isin(SERVICE_URIS)]["session_id"].nunique() if "uri" in fdf.columns else 0
            demo_s = fdf[fdf.get("uri",pd.Series())=="/scheduledemo.php"]["session_id"].nunique() if "uri" in fdf.columns else 0
            sub_s  = int(fdf.drop_duplicates("session_id")["converted_to_lead"].sum()) if "session_id" in fdf.columns else 0
            fig = go.Figure(go.Funnel(
                y=["Index Page","Service Pages","Demo Page","Demo Submitted"],
                x=[idx_s, svc_s, demo_s, sub_s],
                textinfo="value+percent initial",
                marker=dict(color=[BLUE,CYAN,GREEN,AMBER]),
            ))
            fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)",
                              font=dict(color=TEXT, family="Inter, Segoe UI, Arial, sans-serif", size=12),
                              margin=dict(l=10,r=10,t=12,b=10))
            st.plotly_chart(fig, use_container_width=True)
            render_insight_note("This shows where prospects drop before becoming warm leads.")

    # ── FLAGSHIP — AI CYBER ASSISTANT ────────────────────────────
    render_section_label("FLAGSHIP PRODUCT — AI CYBER ASSISTANT INTELLIGENCE")
    with st.container(border=True):
        render_card_header(
            "Is the AI Cyber Assistant creating sales interest?",
            "AI Assistant traffic vs AI-related demo and contact conversations over time"
        )
        _ai_df = fdf.copy()
        _ai_df["week"] = wk(_ai_df["date"])
        _ai_sessions = set(_ai_df[_ai_df["uri"]=="/ai-assistant.php"]["session_id"]) if "uri" in _ai_df.columns and "session_id" in _ai_df.columns else set()
        _weekly_ai = _ai_df.groupby("week").agg(
            ai_hits=("uri", lambda x: int((x=="/ai-assistant.php").sum())),
        ).reset_index()
        # AI-linked conversion events: sessions that visited AI page AND later hit demo/contact
        if _ai_sessions and "uri" in _ai_df.columns:
            _conv_df = _ai_df[_ai_df["session_id"].isin(_ai_sessions) &
                               (_ai_df["uri"].isin(["/scheduledemo.php","/contact.php"]))].copy()
            _weekly_conv = _conv_df.groupby("week").size().reset_index(name="ai_conv_events")
        else:
            _weekly_conv = pd.DataFrame(columns=["week","ai_conv_events"])
        _merged = _weekly_ai.merge(_weekly_conv, on="week", how="left").fillna(0)
        if not _merged.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=_merged["week"], y=_merged["ai_hits"],
                name="AI Assistant Hits", marker_color=CYAN, opacity=0.85,
            ))
            fig.add_trace(go.Scatter(
                x=_merged["week"], y=_merged["ai_conv_events"],
                mode="lines+markers", name="AI-Linked Demo/Contact",
                line=dict(color=GREEN, width=3), marker=dict(size=7, color=GREEN),
                yaxis="y2",
            ))
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", showgrid=False,
                            title="Conversion Events"),
                height=420, paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT, family="Inter, Segoe UI, Arial, sans-serif", size=12),
                margin=dict(l=12, r=52, t=44, b=12),
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
                barmode="overlay",
            )
            fig.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False, tickangle=-30)
            fig.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False)
            st.plotly_chart(fig, use_container_width=True)
            _ai_total = int(_merged["ai_hits"].sum())
            _conv_total = int(_merged["ai_conv_events"].sum())
            _ai_conv_rate = _conv_total / max(_ai_total, 1)
            render_insight_note(
                f"The AI Cyber Assistant received <strong>{_ai_total:,}</strong> hits in this period. "
                f"<strong>{_conv_total:,}</strong> of those sessions progressed to a demo or contact request "
                f"(<strong>{_ai_conv_rate:.1%}</strong> conversion). "
                + ("Strong sales pipeline signal — prioritise AI Assistant in outreach." if _ai_conv_rate >= 0.10
                   else "Moderate conversion — consider improving AI-to-demo call-to-action placement."),
                CYAN_SOFT, "#0E7490"
            )
        else:
            render_empty_state("No AI Assistant data in current filter range")

    # ── FR10 — HIGH-INTENT FUNNEL BREAKDOWN ──────────────────────
    render_section_label("HIGH-INTENT FUNNEL BREAKDOWN")
    _hi_demo    = int((fdf["uri"] == "/scheduledemo.php").sum()) if "uri" in fdf.columns else 0
    _hi_event   = int(fdf["uri"].isin(["/event.php","/events.php"]).sum()) if "uri" in fdf.columns else 0
    _hi_contact = int((fdf["uri"] == "/contact.php").sum()) if "uri" in fdf.columns else 0
    _hi_ai      = int((fdf["uri"] == "/ai-assistant.php").sum()) if "uri" in fdf.columns else 0
    _hi_total   = max(len(fdf), 1)
    _hi_wl_pct  = f"{int(fdf['is_warm_lead'].sum()) / _hi_total:.1%}"
    hf1, hf2, hf3, hf4, hf5 = st.columns(5)
    with hf1: render_kpi_card("Schedule Demo Requests", f"{_hi_demo:,}", "/scheduledemo.php hits", True, BLUE)
    with hf2: render_kpi_card("Event Registrations", f"{_hi_event:,}", "/event.php hits", True, AMBER)
    with hf3: render_kpi_card("Contact Requests", f"{_hi_contact:,}", "/contact.php hits", True, CYAN)
    with hf4: render_kpi_card("AI Assistant Inquiries", f"{_hi_ai:,}", "/ai-assistant.php hits", True, GREEN)
    with hf5: render_kpi_card("Warm Leads / Total", _hi_wl_pct, "High-intent share of all traffic", True, NAVY)
    with st.container(border=True):
        render_card_header("What type of high-intent action are visitors taking?",
                           "Breakdown of sales-relevant actions in the selected period")
        _hi_df = pd.DataFrame({
            "action": ["Schedule Demo", "Event Signup", "Contact Request", "AI Assistant Inquiry"],
            "count":  [_hi_demo, _hi_event, _hi_contact, _hi_ai],
        }).sort_values("count")
        _fi_colors = [BLUE, AMBER, CYAN, GREEN]
        if not _hi_df.empty and _hi_df["count"].sum() > 0:
            _fi_fig = px.bar(_hi_df, x="count", y="action", orientation="h",
                             color="action",
                             color_discrete_map={"Schedule Demo": BLUE, "Event Signup": AMBER,
                                                  "Contact Request": CYAN, "AI Assistant Inquiry": GREEN})
            _fi_fig.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white",
                font=dict(color=TEXT, family="Inter,Segoe UI,Arial,sans-serif", size=12),
                margin=dict(l=8,r=8,t=8,b=8), showlegend=False)
            _fi_fig.update_xaxes(gridcolor="#E8EAED", showline=False, zeroline=False,
                                  range=[0, max(_hi_df["count"].max()*1.15, 1)])
            _fi_fig.update_yaxes(gridcolor="#E8EAED", showline=False, zeroline=False, title=None)
            st.plotly_chart(_fi_fig, use_container_width=True)
        render_insight_note(
            "Demo and contact activity indicate stronger immediate sales intent than general browsing. "
            f"Demo requests (<strong>{_hi_demo:,}</strong>) and event signups (<strong>{_hi_event:,}</strong>) "
            "are tracked separately to distinguish sales-ready demand from event-led engagement.",
            BLUE_SOFT, "#1E40AF"
        )

    # ── FR12 — STATISTICAL EVIDENCE: SERVICE-LEVEL SALES STATS ───
    render_section_label("STATISTICAL EVIDENCE — SERVICE-LEVEL SALES STATISTICS")
    if "service_name" in fdf.columns:
        _st_rows = []
        for svc, sg in fdf.groupby("service_name"):
            _tot_req  = len(sg)
            _wl_ct    = int(sg["is_warm_lead"].sum()) if "is_warm_lead" in sg.columns else 0
            _demo_ct  = int((sg["uri"] == "/scheduledemo.php").sum()) if "uri" in sg.columns else 0
            _cont_ct  = int((sg["uri"] == "/contact.php").sum()) if "uri" in sg.columns else 0
            _rt_col   = "response_time_ms" if "response_time_ms" in sg.columns else ("bytes_sent" if "bytes_sent" in sg.columns else None)
            if _rt_col:
                _rt_mean = round(sg[_rt_col].mean(), 1)
                _rt_med  = round(sg[_rt_col].median(), 1)
                _rt_std  = round(sg[_rt_col].std(), 1)
            else:
                _rt_mean = _rt_med = _rt_std = "—"
            _wl_rate  = f"{_wl_ct / max(_tot_req, 1):.1%}"
            _st_rows.append({"Service": svc, "Total Requests": _tot_req, "Warm Leads": _wl_ct,
                              "Demo Requests": _demo_ct, "Contact Requests": _cont_ct,
                              "Mean RT/Bytes": _rt_mean, "Median RT/Bytes": _rt_med,
                              "Std Dev RT/Bytes": _rt_std, "Warm Lead Rate": _wl_rate})
        _st_df = pd.DataFrame(_st_rows).sort_values("Warm Leads", ascending=False)
        if not _st_df.empty:
            with st.container(border=True):
                render_card_header("Service-Level Sales Statistics",
                                   "Mean, median, and standard deviation of response time/bytes per service, plus warm lead rates.")
                st.dataframe(_st_df, use_container_width=True, hide_index=True)
                _best_svc = _st_df.iloc[0]["Service"]
                render_insight_note(
                    f"<strong>{_best_svc}</strong> generates the highest warm-lead volume — lead with this service in outreach conversations.",
                    BLUE_SOFT, "#1E40AF"
                )

    # ── FR12 — TIME-OF-DAY × SERVICE CORRELATION HEATMAP ─────────
    render_section_label("STATISTICAL EVIDENCE — WHEN IS EACH SERVICE MOST REQUESTED?")
    with st.container(border=True):
        render_card_header("When is each service most requested throughout the day?",
                           "Hour × service heatmap — warmer = more requests")
        if "hour" in fdf.columns and "service_name" in fdf.columns:
            _tod_sv = fdf.groupby(["hour", "service_name"]).size().reset_index(name="requests")
            _tod_pv = _tod_sv.pivot(index="service_name", columns="hour", values="requests").fillna(0)
            if not _tod_pv.empty:
                _tod_fig = px.imshow(_tod_pv, color_continuous_scale=[[0,"#DBEAFE"],[0.5,CYAN],[1,BLUE]],
                                      labels=dict(x="Hour of Day", y="Service", color="Requests"),
                                      aspect="auto")
                _tod_fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=TEXT, family="Inter,Segoe UI,Arial,sans-serif", size=11),
                    margin=dict(l=10,r=10,t=12,b=10))
                st.plotly_chart(_tod_fig, use_container_width=True)
                _peak_row = _tod_sv.loc[_tod_sv["requests"].idxmax()]
                _peak_hr  = int(_peak_row["hour"])
                _peak_svc = _peak_row["service_name"]
                render_insight_note(
                    f"Peak demand: <strong>{_peak_svc}</strong> at <strong>{_peak_hr:02d}:00</strong>. "
                    "Service demand is concentrated in business hours (10:00–14:00), suggesting time-of-day "
                    "affects service interest patterns — align follow-up capacity to these windows.",
                    BLUE_SOFT, "#1E40AF"
                )
            else:
                render_empty_state("No time-of-day data available")
        else:
            render_empty_state("Hour or service data not available")

    # ── SALES FORECAST — 30-day warm-lead projection ──────────────
    render_section_label("SALES FORECAST — 30-DAY WARM-LEAD PROJECTION")
    with st.container(border=True):
        render_card_header(
            "What do the next 30 days of warm-lead demand look like?",
            "Daily warm leads — historical trend + 30-day linear forecast"
        )
        _sf_wc = fdf[fdf["is_warm_lead"]].copy()
        _sf_wc["d"] = _sf_wc["date"].dt.date
        _sf_dl = _sf_wc.groupby("d").size()
        _sf_dl.index = pd.to_datetime(_sf_dl.index)
        if len(_sf_dl) >= 7:
            _sf_x, _sf_y = np.arange(len(_sf_dl), dtype=float), _sf_dl.values.astype(float)
            _sf_mm, _sf_b = np.polyfit(_sf_x, _sf_y, 1)
            _sf_fx     = np.arange(len(_sf_x), len(_sf_x)+30, dtype=float)
            _sf_fdates = pd.date_range(_sf_dl.index[-1]+pd.Timedelta(days=1), periods=30)
            _sf_fc     = pd.Series(np.maximum(_sf_mm*_sf_fx+_sf_b, 0), index=_sf_fdates)
            _sf_fig    = go.Figure()
            _sf_fig.add_trace(go.Scatter(x=_sf_dl.index, y=_sf_dl.values,
                mode="lines+markers", name="Historical",
                line=dict(color=BLUE, width=2.5), marker=dict(size=5)))
            _sf_fig.add_trace(go.Scatter(x=_sf_fc.index, y=_sf_fc.values,
                mode="lines", name="Forecast (30d)",
                line=dict(color=AMBER, width=2.5, dash="dash")))
            _sf_fig.update_xaxes(tickangle=-30)
            st.plotly_chart(cs(_sf_fig, 380), use_container_width=True)
            _sf_total = max(int(sum(_sf_fc)), 0)
            _sf_dir   = "accelerating" if _sf_mm > 0.05 else ("declining" if _sf_mm < -0.05 else "stable")
            render_insight_note(
                f"30-day forecast: ~<strong>{_sf_total:,}</strong> warm leads. "
                f"Pipeline trend is <strong>{_sf_dir}</strong>. "
                "Blue = historical, amber dashed = forecast. Rule-based linear projection.",
                AMBER_SOFT, "#92400E"
            )
        else:
            render_empty_state("Insufficient history for sales forecast — need at least 7 days of data")

    # ── EVIDENCE — SALES ACTION QUEUE ─────────────────────────────
    render_section_label("EVIDENCE — SALES ACTION QUEUE")
    q = fdf.copy()
    def _rec(row):
        et  = str(row.get("event_type","")).lower()
        sc  = str(row.get("status_class","2xx"))
        uri = str(row.get("uri","")).lower()
        is_warm = bool(row.get("is_warm_lead", False))
        # 4xx/5xx warm lead — review before follow-up
        if is_warm and sc in ("4xx","5xx"):
            return "Review failed request before follow-up"
        if "demo"    in et or "scheduledemo" in uri: return "Contact within 24 hours"
        if "contact" in et or "/contact"     in uri: return "Assign a sales representative"
        if "event"   in et:                          return "Invite to product demo follow-up"
        if "ai"      in et or "ai-assistant" in uri: return "Send AI Assistant solution brief"
        return "Monitor session activity"
    def _pri(row):
        sc = str(row.get("status_class","2xx"))
        if row.get("is_warm_lead",False) and sc not in ("4xx","5xx"): return "High"
        if row.get("is_warm_lead",False) and sc in ("4xx","5xx"):     return "Review"
        if str(row.get("segment",""))=="Product-curious":             return "Medium"
        return "Low"
    q["recommended_action"] = q.apply(_rec, axis=1)
    q["priority"]           = q.apply(_pri, axis=1)
    q["_pord"] = q["priority"].map({"High":0,"Review":1,"Medium":2,"Low":3}).fillna(3)
    q = q.sort_values(["_pord","timestamp"], ascending=[True,False])
    show_cols = ["priority","timestamp","country","service_name","event_type",
                 "status_class","segment","recommended_action"]
    show_q    = q[[c for c in show_cols if c in q.columns]].head(50)
    with st.container(border=True):
        render_card_header("Sales Action Queue",
                           "Prioritised events — High = warm lead ready · Review = check before outreach · Medium = product-curious")
        st.dataframe(show_q, use_container_width=True, hide_index=True)

    # ── REPORTS & EXPORTS ─────────────────────────────────────────
    kpis = [
        {"label":"Warm Leads (24h)",     "value":str(m["leads_24h"]),     "note":f"As of {max_ts.date()}"},
        {"label":"Weekly Warm Leads",    "value":str(m["leads_7d"]),      "note":"Last 7 days"},
        {"label":"AI to Demo Conv.",     "value":f"{m['ai_conv']:.1%}",   "note":"AI sessions"},
        {"label":"Top Country",          "value":m["top_country"],        "note":"By warm leads"},
        {"label":"Hot Service",          "value":m["top_service"][:22],   "note":"Most demand"},
    ]
    render_report_section("CyberNova Pulse", role, filters, kpis, bullets, fdf,
                          show_q if not show_q.empty else pd.DataFrame(), "Warm Leads")

# ─────────────────────────────────────────────────────────────────
# DASHBOARD 2 — CYBERNOVA REACH  (Marketing)
# ─────────────────────────────────────────────────────────────────
def show_reach(fdf: pd.DataFrame, filters: dict, role: str) -> None:
    render_hero(
        "CyberNova Reach",
        "Marketing Intelligence Hub",
        "Audience quality, content performance, segment evolution, geographic reach, "
        "and campaign opportunity scoring — all in one view.",
    )
    render_story_strip(["Context","Live Pulse","Marketing Insight","Audience Diagnostics","Campaign Matrix","Export"], CYAN)
    _, a1, a2 = st.columns([4,1,1])
    with a1:
        if st.button("Refresh Data", key="reach_refresh", use_container_width=True):
            load_data.clear(); st.rerun()
    with a2:
        st.download_button("Export CSV", data=to_csv(fdf),
                           file_name="reach_export.csv", mime="text/csv",
                           use_container_width=True, key="reach_exp_csv")
    render_context_chips(filters, role, len(fdf))

    if fdf.empty:
        render_empty_state(); return

    m = calculate_marketing_metrics(fdf)

    # ── SIGNAL ────────────────────────────────────────────────────
    render_section_label("SIGNAL — KEY METRICS")
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: render_kpi_card("Unique Visitors", f"{m['uniq_vis']:,}", "Unique IP addresses", True, CYAN)
    with k2: render_kpi_card("Engaged Session Rate", f"{m['eng_rate']:.1%}", "Sessions ≥3 pages",
                              m["eng_rate"]>=0.18, GREEN)
    with k3: render_kpi_card("Top Entry Page", str(m["top_entry"])[:20], "Highest avg depth", True, BLUE)
    with k4: render_kpi_card("Geographic Reach", f"{m['geo_reach']} countries", "Countries ≥10 req.", True, AMBER)
    with k5: render_kpi_card("Bot Ratio", f"{m['bot_ratio']:.1%}", "Of all requests",
                              m["bot_ratio"]<=0.15, BLUE)

    # ── ROLE SUMMARY BANNER — TODAY'S MARKETING FOCUS ────────────
    _ia_ctry   = m.get("top_country","—")
    _ia_entry  = str(m.get("top_entry","—"))[:28]
    _ia_eng    = m.get("eng_rate",0)
    _ia_bot    = m.get("bot_ratio",0)
    _ia_qual   = ("Strong engagement — audience quality is high." if _ia_eng>=0.35
                  else "Moderate engagement — consider deeper content." if _ia_eng>=0.18
                  else "Low engagement — review landing page quality.")
    _ia_camp   = (f"Prioritise paid campaign testing in {_ia_ctry} via {_ia_entry}."
                  if _ia_eng>=0.18 else f"Nurture {_ia_ctry} audience before scaling spend.")
    st.markdown(f"""
<div style="background:white;border:1px solid #A5F3FC;border-radius:22px;
  box-shadow:0 4px 6px rgba(22,184,199,.06),0 12px 32px rgba(22,184,199,.12);
  padding:24px 28px;margin-bottom:22px;position:relative;overflow:hidden;">
  <div style="position:absolute;right:-60px;top:-60px;width:220px;height:220px;
    border-radius:50%;background:rgba(22,184,199,.05);pointer-events:none;"></div>
  <div style="position:absolute;left:-30px;bottom:-40px;width:160px;height:160px;
    border-radius:50%;background:rgba(16,185,129,.04);pointer-events:none;"></div>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;position:relative;">
    <span style="font-size:10px;text-transform:uppercase;letter-spacing:.16em;
      font-weight:900;color:{CYAN};">Today's Marketing Focus</span>
    <span style="height:1px;background:linear-gradient(90deg,#A5F3FC,transparent);flex:1;"></span>
    <span style="font-size:11px;color:{MUTED};font-weight:700;">Engaged Rate:
      <strong style="color:{'#047857' if _ia_eng>=0.18 else NAVY};">{_ia_eng:.1%}</strong>
    </span>
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:20px;position:relative;">
    <div style="border-right:1px solid {BORDER};padding-right:20px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Top Engaged Market</div>
      <div style="font-size:19px;font-weight:900;color:{NAVY};letter-spacing:-.03em;
        line-height:1.1;">{_ia_ctry}</div>
      <div style="font-size:11px;color:{SECONDARY};margin-top:4px;font-weight:600;">
        Largest audience market</div>
    </div>
    <div style="border-right:1px solid {BORDER};padding-right:20px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Strongest Page / Service</div>
      <div style="font-size:15px;font-weight:900;color:{NAVY};line-height:1.2;">{_ia_entry}</div>
      <div style="font-size:11px;color:{SECONDARY};margin-top:4px;font-weight:600;">
        Best session depth entry path</div>
    </div>
    <div style="border-right:1px solid {BORDER};padding-right:20px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Audience Quality Note</div>
      <div style="font-size:13px;font-weight:800;color:{NAVY};line-height:1.35;">{_ia_qual}</div>
      <div style="font-size:11px;color:{SECONDARY};margin-top:4px;font-weight:600;">
        Bot ratio: {_ia_bot:.1%}</div>
    </div>
    <div>
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Recommended Campaign Action</div>
      <div style="font-size:13px;font-weight:800;color:{NAVY};line-height:1.4;">{_ia_camp}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── LIVE PULSE + FEED  (auto-refreshes every 3 s) ────────────
    render_section_label("LIVE PULSE — STREAMING FROM LOG STREAM")
    render_live_section(fdf, role, "CyberNova Reach")

    # ── INSIGHT ───────────────────────────────────────────────────
    render_section_label("MARKETING INSIGHT")
    bullets, action = generate_marketing_story(fdf, m)
    render_story_card("Marketing Insight",
                      "What current audience behaviour suggests Marketing should optimise.",
                      bullets, action, CYAN, CYAN_SOFT)

    # ── DIAGNOSIS ────────────────────────────────────────────────
    render_section_label("DIAGNOSIS — AUDIENCE QUALITY")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            render_card_header("Where should we direct ad spend?",
                               "Visitors vs engagement vs warm leads by country")
            c_stats = []
            for ctry, cdf in fdf.groupby("country"):
                sd = cdf.drop_duplicates("session_id") if "session_id" in cdf.columns else cdf
                c_stats.append({"country":ctry,
                                 "visitors":cdf["ip_address"].nunique() if "ip_address" in cdf.columns else len(cdf),
                                 "engaged_rate":float((sd["distinct_pages_session"]>=3).mean()) if "distinct_pages_session" in sd.columns else 0,
                                 "warm_leads":int(cdf["is_warm_lead"].sum()) if "is_warm_lead" in cdf.columns else 0})
            cst = pd.DataFrame(c_stats)
            if not cst.empty:
                fig = px.scatter(cst, x="visitors", y="engaged_rate", size="warm_leads",
                                 color="country", hover_name="country", size_max=40,
                                 color_discrete_sequence=PALETTE,
                                 labels={"visitors":"Unique Visitors","engaged_rate":"Engaged Rate"})
                fig.update_yaxes(tickformat=".0%")
                st.plotly_chart(cs(fig,420), use_container_width=True)
                render_insight_note("Countries in the high-engagement/high-volume zone are strongest campaign candidates.", CYAN_SOFT, "#0E7490")
            else:
                render_empty_state()
    with c2:
        with st.container(border=True):
            render_card_header("Which content is under-promoted?",
                               "Visit share vs conversion share by service")
            total_req  = max(len(fdf),1); total_warm = max(int(fdf["is_warm_lead"].sum()),1)
            vs   = fdf.groupby("service_name").size() / total_req
            cs2  = fdf[fdf["is_warm_lead"]].groupby("service_name").size() / total_warm
            idx  = vs.index.union(cs2.index)
            gap  = pd.DataFrame({
                "service":          idx,
                "Visit Share":      vs.reindex(idx).fillna(0).values,
                "Conversion Share": cs2.reindex(idx).fillna(0).values,
            }).melt(id_vars="service", var_name="metric", value_name="share")
            fig = px.bar(gap, x="share", y="service", color="metric", orientation="h",
                         barmode="group", color_discrete_map={"Visit Share":BLUE,"Conversion Share":GREEN})
            fig.update_xaxes(tickformat=".0%")
            st.plotly_chart(cs(fig,420), use_container_width=True)
            render_insight_note("Services where conversion share exceeds visit share are under-promoted opportunities.")

    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            render_card_header("How is audience mix shifting over time?",
                               "Segment composition by week")
            if "session_id" in fdf.columns and "segment" in fdf.columns:
                ss = fdf.drop_duplicates("session_id").copy()
                ss["week"] = wk(ss["date"])
                wseg = ss.groupby(["week","segment"]).size().reset_index(name="sessions")
                fig = px.bar(wseg, x="week", y="sessions", color="segment",
                             color_discrete_sequence=PALETTE, barmode="stack")
                fig.update_xaxes(tickangle=-30)
                st.plotly_chart(cs(fig), use_container_width=True)
                render_insight_note("This explains whether traffic is becoming more sales-ready over time.")
            else:
                render_empty_state()
    with c4:
        with st.container(border=True):
            render_card_header("How is SADC reach growing?",
                               "Visitors by country — SADC vs other")
            if "is_sadc" in fdf.columns and "country" in fdf.columns:
                geo = fdf.groupby(["country","is_sadc"]).agg(visitors=("ip_address","nunique")).reset_index()
                geo["market"] = geo["is_sadc"].map({True:"SADC",False:"Other"})
                fig = px.bar(geo.sort_values("visitors"), x="visitors", y="country",
                             color="market", orientation="h",
                             color_discrete_map={"SADC":GREEN,"Other":BLUE})
                st.plotly_chart(cs(fig), use_container_width=True)
                render_insight_note("SADC countries represent CyberNova's primary target expansion region.", GREEN_SOFT, "#047857")
            else:
                render_empty_state()

    c5, c6 = st.columns(2)
    with c5:
        with st.container(border=True):
            render_card_header("When are humans most active?",
                               "Human activity heatmap — bot traffic excluded")
            human = fdf[~fdf["is_bot"]].copy() if "is_bot" in fdf.columns else fdf.copy()
            if not human.empty and "hour" in human.columns and "day_of_week" in human.columns:
                ht  = human.groupby(["day_of_week","hour"]).size().reset_index(name="count")
                pv  = ht.pivot(index="hour", columns="day_of_week", values="count")
                pv  = pv.reindex(columns=[d for d in DAY_ORDER if d in pv.columns]).fillna(0)
                fig = px.imshow(pv, color_continuous_scale=[[0,"#CFFAFE"],[1,CYAN]],
                                labels=dict(x="Day",y="Hour",color="Sessions"), aspect="auto")
                fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=12,b=10))
                st.plotly_chart(fig, use_container_width=True)
                render_insight_note("Align campaign scheduling and content releases to peak human activity windows.", CYAN_SOFT, "#0E7490")
            else:
                render_empty_state()
    with c6:
        with st.container(border=True):
            render_card_header("Is bot traffic distorting analytics?",
                               "Bot vs human traffic by week")
            fdf2 = fdf.copy()
            fdf2["week"] = wk(fdf2["date"])
            fdf2["type"] = fdf2["is_bot"].map({True:"Bot",False:"Human"}) if "is_bot" in fdf2.columns else "Human"
            bw = fdf2.groupby(["week","type"]).size().reset_index(name="requests")
            fig = px.bar(bw, x="week", y="requests", color="type",
                         color_discrete_map={"Bot":AMBER,"Human":BLUE}, barmode="stack")
            fig.update_xaxes(tickangle=-30)
            st.plotly_chart(cs(fig), use_container_width=True)
            br = m.get("bot_ratio",0)
            render_insight_note(
                f"Bot ratio: {br:.1%}. {'Elevated — filter bots for cleaner analytics.' if br>0.15 else 'Controlled — analytics quality is sound.'}",
                AMBER_SOFT if br>0.15 else CYAN_SOFT,
                "#92400E" if br>0.15 else "#0E7490",
            )

    render_section_label("AUDIENCE — ENTRY PAGE DEPTH")
    _BAD_EP = {"undefined", "null", "none", "nan", "", "/"}
    if "entry_page" in fdf.columns and "distinct_pages_session" in fdf.columns:
        _ep_df = (fdf.drop_duplicates("session_id")
                    .assign(_ep=lambda d: d["entry_page"].astype(str))
                    .loc[lambda d: ~(d["_ep"].str.lower().isin(_BAD_EP)
                                     | d["_ep"].str.lower().str.contains("undefined", na=False))])
        dep = (_ep_df.groupby("_ep")["distinct_pages_session"].mean()
                     .reset_index()
                     .rename(columns={"_ep": "entry_page", "distinct_pages_session": "avg_pages"})
                     .sort_values("avg_pages", ascending=True)
                     .tail(12))
    else:
        dep = pd.DataFrame()
    with st.container(border=True):
        render_card_header("Which entry pages drive the deepest sessions?",
                           "Average pages per session by entry URL — bots excluded")
        if not dep.empty:
            fig = px.bar(dep, x="avg_pages", y="entry_page", orientation="h",
                         color_discrete_sequence=[CYAN])
            fig.update_layout(title=None)
            st.plotly_chart(cs(fig, 420), use_container_width=True)
            best_ep = dep["entry_page"].iloc[-1]
            render_insight_note(
                f"<strong>{best_ep}</strong> drives the deepest sessions — prioritise it as a campaign landing page.",
                CYAN_SOFT, "#0E7490"
            )
        else:
            render_empty_state("No entry page data in current filters")

    # ── EVIDENCE — CAMPAIGN OPPORTUNITY MATRIX ────────────────────
    render_section_label("EVIDENCE — CAMPAIGN OPPORTUNITY MATRIX")
    rows = []
    for ctry, cdf in fdf.groupby("country"):
        uv  = cdf["ip_address"].nunique() if "ip_address" in cdf.columns else len(cdf)
        sd  = cdf.drop_duplicates("session_id") if "session_id" in cdf.columns else cdf
        eng = int((sd["distinct_pages_session"]>=3).sum()) if "distinct_pages_session" in sd.columns else 0
        wl  = int(cdf["is_warm_lead"].sum()) if "is_warm_lead" in cdf.columns else 0
        br  = float(cdf["is_bot"].mean()) if "is_bot" in cdf.columns else 0.0
        rows.append({"country":ctry,"unique_visitors":uv,"engaged_sessions":eng,"warm_leads":wl,"bot_ratio":br})
    mx = pd.DataFrame(rows).sort_values("unique_visitors", ascending=False)
    if not mx.empty:
        mx["uv_rank"]  = mx["unique_visitors"].rank(pct=True)
        mx["eng_rank"] = mx["engaged_sessions"].rank(pct=True)
        mx["wl_rank"]  = mx["warm_leads"].rank(pct=True)
        mx["bot_pen"]  = mx["bot_ratio"].clip(0,1)*0.5
        mx["opportunity_score"] = (mx["uv_rank"]+mx["eng_rank"]+mx["wl_rank"]-mx["bot_pen"]).round(2)
        def _oact(s):
            if s>=2.0: return "Prioritise campaign test"
            if s>=1.2: return "Retarget and nurture"
            return "Monitor before spending"
        mx["recommended_action"] = mx["opportunity_score"].apply(_oact)
        mx["bot_ratio"] = mx["bot_ratio"].map("{:.1%}".format)
        show_mx = mx[["country","unique_visitors","engaged_sessions","warm_leads","bot_ratio","opportunity_score","recommended_action"]]
        with st.container(border=True):
            render_card_header("Campaign Opportunity Matrix",
                               "Country-level scoring for campaign prioritisation — ranked by visitor volume and engagement quality.")
            st.dataframe(show_mx, use_container_width=True, hide_index=True)

    # ── FR12 — COUNTRY-LEVEL ENGAGEMENT STATISTICS ───────────────
    render_section_label("STATISTICAL EVIDENCE — COUNTRY-LEVEL ENGAGEMENT STATISTICS")
    if "country" in fdf.columns:
        _ce_rows = []
        for ctry, cg in fdf.groupby("country"):
            _cg_tot = len(cg)
            _cg_uv  = cg["ip_address"].nunique() if "ip_address" in cg.columns else _cg_tot
            _cg_sd  = cg.drop_duplicates("session_id") if "session_id" in cg.columns else cg
            _cg_eng = int((_cg_sd["distinct_pages_session"] >= 3).sum()) if "distinct_pages_session" in _cg_sd.columns else 0
            _dp_col = "distinct_pages_session"
            _cg_mean = round(_cg_sd[_dp_col].mean(), 2) if _dp_col in _cg_sd.columns else "—"
            _cg_med  = round(_cg_sd[_dp_col].median(), 2) if _dp_col in _cg_sd.columns else "—"
            _cg_std  = round(_cg_sd[_dp_col].std(), 2) if _dp_col in _cg_sd.columns else "—"
            _cg_bot  = f"{float(cg['is_bot'].mean()):.1%}" if "is_bot" in cg.columns else "—"
            _cg_wl   = int(cg["is_warm_lead"].sum()) if "is_warm_lead" in cg.columns else 0
            _ce_rows.append({"Country": ctry, "Total Requests": _cg_tot, "Unique Visitors": _cg_uv,
                              "Engaged Sessions": _cg_eng, "Mean Pages/Session": _cg_mean,
                              "Median Pages/Session": _cg_med, "Std Dev Pages": _cg_std,
                              "Bot Ratio": _cg_bot, "Warm Leads": _cg_wl})
        _ce_df = pd.DataFrame(_ce_rows).sort_values("Unique Visitors", ascending=False)
        if not _ce_df.empty:
            with st.container(border=True):
                render_card_header("Country-Level Engagement Statistics",
                                   "Mean, median, and standard deviation of pages per session per country — with bot ratio and warm lead count.")
                st.dataframe(_ce_df, use_container_width=True, hide_index=True)
                _top_ce = _ce_df.iloc[0]["Country"]
                render_insight_note(
                    f"<strong>{_top_ce}</strong> is the largest audience market — prioritise campaigns here for maximum reach.",
                    CYAN_SOFT, "#0E7490"
                )

    # ── FR12 — TIME-OF-DAY × SERVICE HEATMAP (Marketing view) ────
    render_section_label("STATISTICAL EVIDENCE — WHEN IS EACH SERVICE MOST REQUESTED?")
    with st.container(border=True):
        render_card_header("When are humans most active on each service?",
                           "Hour × service heatmap — human traffic only, bots excluded")
        if "hour" in fdf.columns and "service_name" in fdf.columns:
            _human_fdf = fdf[~fdf["is_bot"]] if "is_bot" in fdf.columns else fdf
            _tod_mk = _human_fdf.groupby(["hour","service_name"]).size().reset_index(name="requests")
            _tod_mk_pv = _tod_mk.pivot(index="service_name", columns="hour", values="requests").fillna(0)
            if not _tod_mk_pv.empty:
                _tod_mk_fig = px.imshow(_tod_mk_pv,
                                         color_continuous_scale=[[0,"#CFFAFE"],[0.5,CYAN],[1,"#0E7490"]],
                                         labels=dict(x="Hour of Day", y="Service", color="Human Requests"),
                                         aspect="auto")
                _tod_mk_fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=TEXT, family="Inter,Segoe UI,Arial,sans-serif", size=11),
                    margin=dict(l=10,r=10,t=12,b=10))
                st.plotly_chart(_tod_mk_fig, use_container_width=True)
                _mk_pk = _tod_mk.loc[_tod_mk["requests"].idxmax()]
                render_insight_note(
                    f"Peak human demand: <strong>{_mk_pk['service_name']}</strong> at <strong>{int(_mk_pk['hour']):02d}:00</strong>. "
                    "Service demand is concentrated around 10:00–14:00, suggesting time-of-day affects "
                    "service interest patterns — align campaign activity to these windows.",
                    CYAN_SOFT, "#0E7490"
                )
            else:
                render_empty_state("No heatmap data available")
        else:
            render_empty_state("Hour or service data not available")

    # ── MARKETING FORECAST — engaged sessions ─────────────────────
    render_section_label("MARKETING FORECAST — 30-DAY ENGAGED SESSION PROJECTION")
    with st.container(border=True):
        render_card_header(
            "What does audience engagement look like over the next 30 days?",
            "Daily engaged sessions (>=3 pages) — historical + 30-day forecast"
        )
        if "session_id" in fdf.columns and "distinct_pages_session" in fdf.columns:
            _mf_sess = fdf.drop_duplicates("session_id").copy()
            _mf_sess["d"] = _mf_sess["date"].dt.date
            _mf_dl = _mf_sess[_mf_sess["distinct_pages_session"] >= 3].groupby("d").size()
            _mf_dl.index = pd.to_datetime(_mf_dl.index)
            if len(_mf_dl) >= 7:
                _mf_x, _mf_y = np.arange(len(_mf_dl), dtype=float), _mf_dl.values.astype(float)
                _mf_mm, _mf_b = np.polyfit(_mf_x, _mf_y, 1)
                _mf_fx     = np.arange(len(_mf_x), len(_mf_x)+30, dtype=float)
                _mf_fdates = pd.date_range(_mf_dl.index[-1]+pd.Timedelta(days=1), periods=30)
                _mf_fc     = pd.Series(np.maximum(_mf_mm*_mf_fx+_mf_b, 0), index=_mf_fdates)
                _mf_fig    = go.Figure()
                _mf_fig.add_trace(go.Scatter(x=_mf_dl.index, y=_mf_dl.values,
                    mode="lines+markers", name="Historical",
                    line=dict(color=CYAN, width=2.5), marker=dict(size=5)))
                _mf_fig.add_trace(go.Scatter(x=_mf_fc.index, y=_mf_fc.values,
                    mode="lines", name="Forecast (30d)",
                    line=dict(color=AMBER, width=2.5, dash="dash")))
                _mf_fig.update_xaxes(tickangle=-30)
                st.plotly_chart(cs(_mf_fig, 380), use_container_width=True)
                _mf_total = max(int(sum(_mf_fc)), 0)
                _mf_dir   = "growing" if _mf_mm > 0.05 else ("declining" if _mf_mm < -0.05 else "stable")
                render_insight_note(
                    f"30-day engaged-session forecast: ~<strong>{_mf_total:,}</strong> sessions. "
                    f"Engagement trend is <strong>{_mf_dir}</strong>. "
                    "Blue = historical, amber dashed = forecast.",
                    AMBER_SOFT, "#92400E"
                )
            else:
                render_empty_state("Insufficient history for marketing forecast")
        else:
            render_empty_state("Session data not available for forecast")

    # Segment detail
    render_section_label("EVIDENCE — VISITOR SEGMENT DETAIL")
    seg_tbl = fdf.drop_duplicates("session_id")[
        ["country","segment","session_id","distinct_pages_session","converted_to_lead","campaign_name"]
    ].sort_values("distinct_pages_session", ascending=False) if "session_id" in fdf.columns else pd.DataFrame()
    if not seg_tbl.empty:
        with st.container(border=True):
            render_card_header("Visitor Segment Detail",
                               "Session-level breakdown by country, segment, pages visited, lead status, and campaign.")
            st.dataframe(seg_tbl.head(200), use_container_width=True, hide_index=True)

    # ── REPORTS ───────────────────────────────────────────────────
    kpis = [
        {"label":"Unique Visitors",     "value":f"{m['uniq_vis']:,}",    "note":"Unique IPs"},
        {"label":"Engaged Session Rate","value":f"{m['eng_rate']:.1%}",  "note":"Sessions ≥3 pages"},
        {"label":"Top Entry Page",      "value":str(m["top_entry"])[:22],"note":"Best depth"},
        {"label":"Geographic Reach",    "value":f"{m['geo_reach']} ctry","note":"Countries ≥10 req"},
        {"label":"Bot Ratio",           "value":f"{m['bot_ratio']:.1%}", "note":"Of all requests"},
    ]
    render_report_section("CyberNova Reach", role, filters, kpis, bullets, fdf,
                          show_mx if not mx.empty else pd.DataFrame(), "Campaign Matrix")

# ─────────────────────────────────────────────────────────────────
# DASHBOARD 3 — CYBERNOVA HORIZON  (Executive)
# ─────────────────────────────────────────────────────────────────
def show_horizon(fdf: pd.DataFrame, filters: dict, role: str) -> None:
    render_hero(
        "CyberNova Horizon",
        "Executive Insights Dashboard",
        "Strategic growth signals, AI Assistant traction, SADC market penetration, "
        "30-day demand forecast, and operational risk at a glance.",
    )
    render_story_strip(["Context","Executive Pulse","Strategic Signal","Growth Diagnostics","Decision Brief","Export"], GREEN)
    _, a1, a2 = st.columns([4,1,1])
    with a1:
        if st.button("Refresh Data", key="horiz_refresh", use_container_width=True):
            load_data.clear(); st.rerun()
    with a2:
        st.download_button("Export CSV", data=to_csv(fdf),
                           file_name="horizon_export.csv", mime="text/csv",
                           use_container_width=True, key="horiz_exp_csv")
    render_context_chips(filters, role, len(fdf))

    if fdf.empty:
        render_empty_state(); return

    m = calculate_executive_metrics(fdf)
    ym_series = mo(fdf["date"])
    months    = sorted(ym_series.unique())

    # ── SIGNAL ────────────────────────────────────────────────────
    render_section_label("SIGNAL — KEY METRICS")
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: render_kpi_card("MoM Visitor Growth", f"{m['mom_growth']:+.1f}%",
                              f"{m['prev_vis']:,} to {m['curr_vis']:,}", m["mom_growth"]>=0)
    with k2: render_kpi_card("AI Assistant Traction", f"{m['ai_share']:.1%}",
                              "Service traffic share", m["ai_share"]>=0.10, CYAN)
    with k3: render_kpi_card("SADC Active Markets", str(m["sadc_total"]),
                              "Countries with traffic", True, GREEN)
    with k4: render_kpi_card("30-Day Lead Forecast", f"~{m['forecast']:,}",
                              "Linear projection", True, AMBER)
    with k5: render_kpi_card("Anomaly Days", str(m["anom_days"]),
                              "Days flagged", m["anom_days"]==0, BLUE)

    # ── ROLE SUMMARY BANNER — BOARD SUMMARY ─────────────────────
    _ia_mg    = m.get("mom_growth",0)
    _ia_ai    = m.get("ai_share",0)
    _ia_fc    = m.get("forecast",0)
    _ia_anom  = m.get("anom_days",0)
    _ia_mkt   = (fdf.groupby("country")["ip_address"].nunique().idxmax()
                 if "ip_address" in fdf.columns and "country" in fdf.columns else "—")
    _ia_trend = "Accelerating" if _ia_mg>=5 else ("Stable" if _ia_mg>=-2 else "Declining")
    _ia_ai_note = ("Strong traction — scale AI positioning." if _ia_ai>=0.15
                   else "Emerging — increase AI visibility." if _ia_ai>=0.08 else "Low — promote AI Assistant.")
    _ia_risk   = (f"{_ia_anom} anomaly days — review security log." if _ia_anom>0
                  else "No anomalies detected — operations nominal.")
    _ia_risk_col = "#EF4444" if _ia_anom > 0 else NAVY
    _ia_lead_rec = ("Scale AI Assistant positioning across high-performing SADC markets."
                    if _ia_ai>=0.12 else "Strengthen campaign activity around high-intent services."
                    if _ia_mg>=0 else "Investigate traffic decline — review campaign performance.")
    st.markdown(f"""
<div style="background:white;border:1px solid #6EE7B7;border-radius:22px;
  box-shadow:0 4px 6px rgba(16,185,129,.06),0 12px 32px rgba(16,185,129,.12);
  padding:24px 28px;margin-bottom:22px;position:relative;overflow:hidden;">
  <div style="position:absolute;right:-60px;top:-60px;width:220px;height:220px;
    border-radius:50%;background:rgba(16,185,129,.05);pointer-events:none;"></div>
  <div style="position:absolute;left:-30px;bottom:-40px;width:160px;height:160px;
    border-radius:50%;background:rgba(245,158,11,.04);pointer-events:none;"></div>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;position:relative;">
    <span style="font-size:10px;text-transform:uppercase;letter-spacing:.16em;
      font-weight:900;color:{GREEN};">Board Summary</span>
    <span style="height:1px;background:linear-gradient(90deg,#6EE7B7,transparent);flex:1;"></span>
    <span style="font-size:11px;color:{MUTED};font-weight:700;">MoM Growth:
      <strong style="color:{'#047857' if _ia_mg>=0 else '#DC2626'};">{_ia_mg:+.1f}%</strong>
      &nbsp;({_ia_trend})
    </span>
  </div>
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:18px;position:relative;">
    <div style="border-right:1px solid {BORDER};padding-right:18px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Strongest Market</div>
      <div style="font-size:18px;font-weight:900;color:{NAVY};letter-spacing:-.03em;
        line-height:1.1;">{_ia_mkt}</div>
      <div style="font-size:11px;color:{SECONDARY};margin-top:4px;font-weight:600;">
        Growth: {_ia_mg:+.1f}%</div>
    </div>
    <div style="border-right:1px solid {BORDER};padding-right:18px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">AI Traction</div>
      <div style="font-size:16px;font-weight:900;color:{NAVY};line-height:1.2;">{_ia_ai:.1%}</div>
      <div style="font-size:11px;color:{SECONDARY};margin-top:4px;font-weight:600;">
        {_ia_ai_note}</div>
    </div>
    <div style="border-right:1px solid {BORDER};padding-right:18px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">90-Day Forecast</div>
      <div style="font-size:16px;font-weight:900;color:{NAVY};">~{_ia_fc:,} leads</div>
      <div style="font-size:11px;color:{SECONDARY};margin-top:4px;font-weight:600;">
        Linear projection</div>
    </div>
    <div style="border-right:1px solid {BORDER};padding-right:18px;">
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Top Risk</div>
      <div style="font-size:13px;font-weight:800;color:{_ia_risk_col};line-height:1.35;">{_ia_risk}</div>
    </div>
    <div>
      <div style="font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;
        color:{MUTED};margin-bottom:6px;">Leadership Recommendation</div>
      <div style="font-size:12px;font-weight:800;color:{NAVY};line-height:1.4;">{_ia_lead_rec}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── EXECUTIVE PULSE + FEED  (auto-refreshes every 3 s) ──────
    render_section_label("EXECUTIVE PULSE — STREAMING FROM LOG STREAM")
    render_live_section(fdf, role, "CyberNova Horizon")

    # ── INSIGHT ───────────────────────────────────────────────────
    render_section_label("EXECUTIVE INSIGHT")
    bullets, action = generate_executive_story(fdf, m)
    render_story_card("This Month at a Glance",
                      "Board-level summary generated from the selected dataset.",
                      bullets, action, GREEN, GREEN_SOFT)

    # ── DIAGNOSIS ────────────────────────────────────────────────
    render_section_label("DIAGNOSIS — STRATEGIC DIRECTION")
    # Full-width: growth trend
    with st.container(border=True):
        render_card_header("Are we on track for strategic growth?",
                           "Weekly visitors, warm leads, and AI interest — the three growth signals")
        fdf2 = fdf.copy(); fdf2["week"] = wk(fdf2["date"])
        weekly = fdf2.groupby("week").agg(
            unique_visitors=("ip_address","nunique"),
            warm_leads=("is_warm_lead","sum"),
            ai_requests=("uri", lambda x: int((x=="/ai-assistant.php").sum())),
        ).reset_index()
        fig = go.Figure()
        for col, colour, name in [
            ("unique_visitors",BLUE, "Unique Visitors"),
            ("warm_leads",     GREEN,"Warm Leads"),
            ("ai_requests",    CYAN, "AI Requests"),
        ]:
            fig.add_trace(go.Scatter(x=weekly["week"], y=weekly[col],
                                     mode="lines+markers", name=name,
                                     line=dict(color=colour,width=3), marker=dict(size=6)))
        fig.update_xaxes(tickangle=-30)
        st.plotly_chart(cs(fig,460), use_container_width=True)
        render_insight_note("This shows whether awareness, demand, and AI Assistant interest are moving together.", GREEN_SOFT, "#047857")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            render_card_header("Where is regional expansion concentrating?",
                               "Country demand with MoM growth signal")
            fdf3 = fdf.copy(); fdf3["ym"] = ym_series.values
            mc   = fdf3.groupby(["country","ym"]).agg(visitors=("ip_address","nunique")).reset_index()
            lm   = months[-1] if months else None
            pm   = months[-2] if len(months)>=2 else None
            cc_  = mc[mc["ym"]==lm].set_index("country")["visitors"] if lm else pd.Series(dtype=int)
            pc_  = mc[mc["ym"]==pm].set_index("country")["visitors"] if pm else pd.Series(dtype=int)
            all_ = cc_.index.union(pc_.index)
            if len(all_):
                reg = pd.DataFrame({
                    "country":   all_,
                    "visitors":  cc_.reindex(all_).fillna(0).astype(int).values,
                    "warm_leads":fdf[fdf["is_warm_lead"]].groupby("country").size().reindex(all_).fillna(0).astype(int).values,
                    "growth_pct":((cc_.reindex(all_).fillna(0)-pc_.reindex(all_).fillna(0))
                                  /pc_.reindex(all_).replace(0,np.nan)*100).fillna(0).round(1).values,
                }).sort_values("visitors", ascending=False)
                fig = px.bar(reg.sort_values("visitors"), x="visitors", y="country",
                             orientation="h", color="growth_pct",
                             color_continuous_scale=[[0,AMBER],[0.5,"#F3F4F6"],[1,GREEN]],
                             labels={"growth_pct":"MoM Growth %"})
                st.plotly_chart(cs(fig,420), use_container_width=True)
                render_insight_note("This shows which SADC markets are becoming commercially meaningful.", GREEN_SOFT, "#047857")
            else:
                render_empty_state()
    with c2:
        with st.container(border=True):
            render_card_header("Is the AI Cyber Assistant gaining traction?",
                               "AI request volume and service share by month")
            fdf4 = fdf.copy(); fdf4["ym"] = ym_series.values
            mai  = fdf4.groupby("ym").agg(
                ai_reqs=("uri", lambda x: int((x=="/ai-assistant.php").sum())),
                svc_reqs=("uri", lambda x: int(x.isin(SERVICE_URIS).sum())),
            ).reset_index()
            mai["ai_share"] = mai["ai_reqs"] / mai["svc_reqs"].clip(lower=1)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=mai["ym"], y=mai["ai_reqs"],
                                 name="AI Requests", marker_color=CYAN, opacity=0.8))
            fig.add_trace(go.Scatter(x=mai["ym"], y=mai["ai_share"],
                                     mode="lines+markers", name="AI Share %",
                                     line=dict(color=BLUE,width=3), yaxis="y2",
                                     marker=dict(size=7)))
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", tickformat=".0%", showgrid=False),
                height=420, paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=12,r=44,t=44,b=12),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig, use_container_width=True)
            render_insight_note(f"AI share of service traffic: <strong>{m['ai_share']:.1%}</strong>. "
                                + ("Strong momentum — scale positioning." if m["ai_share"]>=0.15 else "Emerging signal — increase AI Assistant visibility."),
                                CYAN_SOFT, "#0E7490")

    # Forecast chart
    with st.container(border=True):
        render_card_header("What does the next 3 months look like?",
                           "90-day warm-lead forecast with anomaly markers")
        wc2 = fdf[fdf["is_warm_lead"]].copy()
        wc2["d"] = wc2["date"].dt.date
        dl  = wc2.groupby("d").size()
        dl.index = pd.to_datetime(dl.index)
        if len(dl)>=7:
            x, y = np.arange(len(dl),dtype=float), dl.values.astype(float)
            mm, b = np.polyfit(x, y, 1)
            fx = np.arange(len(x),len(x)+90,dtype=float)
            fdates = pd.date_range(dl.index[-1]+pd.Timedelta(days=1), periods=90)
            fc = pd.Series(np.maximum(mm*fx+b,0), index=fdates)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dl.index, y=dl.values, mode="lines+markers",
                                     name="Historical", line=dict(color=BLUE,width=2), marker=dict(size=5)))
            fig.add_trace(go.Scatter(x=fc.index, y=fc.values, mode="lines",
                                     name="Forecast (90d / 3 months)", line=dict(color=AMBER,width=2,dash="dash")))
            if "is_anomaly" in fdf.columns:
                for ad in fdf[fdf["is_anomaly"]]["date"].dt.date.unique():
                    adt = pd.Timestamp(ad)
                    if adt in dl.index:
                        fig.add_vline(x=adt, line_width=1, line_dash="dot",
                                      line_color="#EF4444", opacity=0.5)
            fig.update_xaxes(tickangle=-30)
            st.plotly_chart(cs(fig,460), use_container_width=True)
            render_insight_note(f"90-day forecast (3 months): ~{m['forecast']:,} warm leads. Red lines = anomaly days. Rule-based linear projection.", AMBER_SOFT, "#92400E")
        else:
            render_empty_state("Insufficient history for forecast — need at least 7 days of data")

    # Anomaly log
    render_section_label("OPERATIONAL — ANOMALY LOG")
    anom_tbl = fdf[fdf["is_anomaly"]][
        ["timestamp","country","service_name","anomaly_name","response_time_ms","status_class"]
    ].sort_values("timestamp",ascending=False) if "is_anomaly" in fdf.columns else pd.DataFrame()
    with st.container(border=True):
        render_card_header("Anomaly Event Log",
                           "Flagged events with anomaly type, country, service, and HTTP status for operational review.")
        if not anom_tbl.empty:
            st.dataframe(anom_tbl.head(100), use_container_width=True, hide_index=True)
            render_insight_note(
                f"<strong>{len(anom_tbl):,}</strong> anomaly events detected. Review service and response time columns for operational or security patterns.",
                AMBER_SOFT, "#92400E"
            )
        else:
            render_empty_state("No anomalies detected in current filter range — operations nominal.")

    # ── FR6 — REGIONAL EXPANSION TARGET CHECK ────────────────────
    render_section_label("REGIONAL EXPANSION TARGET CHECK")
    if "country" in fdf.columns:
        _total_reqs = max(len(fdf), 1)
        _sadc_set   = {"Botswana","South Africa","Zambia","Namibia","Zimbabwe",
                       "Lesotho","Eswatini","Mozambique","Malawi","Tanzania"}
        _reg_rows   = []
        for ctry, cg in fdf.groupby("country"):
            if ctry not in _sadc_set:
                continue
            _r_tot  = len(cg)
            _r_wl   = int(cg["is_warm_lead"].sum()) if "is_warm_lead" in cg.columns else 0
            _r_pct  = _r_tot / _total_reqs
            if _r_pct >= 0.10:
                _r_status = "Above target"
            elif _r_pct >= 0.05:
                _r_status = "On watch"
            else:
                _r_status = "Below expansion target"
            _reg_rows.append({"Country": ctry, "Total Requests": _r_tot, "Warm Leads": _r_wl,
                               "Share of Traffic": f"{_r_pct:.1%}", "Target Status": _r_status})
        _reg_df = pd.DataFrame(_reg_rows).sort_values("Total Requests", ascending=False)
        if not _reg_df.empty:
            # Colour-coded status column using custom HTML table
            def _status_badge(s):
                if s == "Above target":
                    return (f'<span style="background:{GREEN_SOFT};color:#047857;font-size:11px;'
                            f'font-weight:800;padding:3px 9px;border-radius:999px;">{s}</span>')
                if s == "On watch":
                    return (f'<span style="background:{CYAN_SOFT};color:#0E7490;font-size:11px;'
                            f'font-weight:800;padding:3px 9px;border-radius:999px;">{s}</span>')
                return (f'<span style="background:{AMBER_SOFT};color:#92400E;font-size:11px;'
                        f'font-weight:800;padding:3px 9px;border-radius:999px;">{s}</span>')
            rows_html = "".join(
                f'<tr style="border-bottom:1px solid {BORDER};">'
                f'<td style="padding:10px 12px;font-weight:800;color:{NAVY};font-size:13px;">{r["Country"]}</td>'
                f'<td style="padding:10px 12px;color:{TEXT};font-size:13px;">{r["Total Requests"]:,}</td>'
                f'<td style="padding:10px 12px;color:{TEXT};font-size:13px;">{r["Warm Leads"]}</td>'
                f'<td style="padding:10px 12px;color:{TEXT};font-size:13px;">{r["Share of Traffic"]}</td>'
                f'<td style="padding:10px 12px;">{_status_badge(r["Target Status"])}</td>'
                f'</tr>'
                for _, r in _reg_df.iterrows()
            )
            st.markdown(f"""
<div style="background:white;border:1px solid {BORDER};border-radius:18px;
  box-shadow:{SHADOW_S};padding:20px;margin-bottom:18px;">
  <h3 style="margin:0 0 4px;color:{NAVY};font-size:17px;">Regional Expansion Target Check</h3>
  <p style="margin:0 0 14px;color:{MUTED};font-size:13px;">
    SADC market performance against traffic share targets.
    Above target ≥10% &nbsp;&middot;&nbsp; On watch 5–10% &nbsp;&middot;&nbsp; Below target &lt;5%.
  </p>
  <table style="width:100%;border-collapse:collapse;">
    <thead><tr style="background:{SLATE_SOFT};">
      <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:900;color:{SECONDARY};
        text-transform:uppercase;letter-spacing:.07em;">Country</th>
      <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:900;color:{SECONDARY};
        text-transform:uppercase;letter-spacing:.07em;">Total Requests</th>
      <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:900;color:{SECONDARY};
        text-transform:uppercase;letter-spacing:.07em;">Warm Leads</th>
      <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:900;color:{SECONDARY};
        text-transform:uppercase;letter-spacing:.07em;">Traffic Share</th>
      <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:900;color:{SECONDARY};
        text-transform:uppercase;letter-spacing:.07em;">Target Status</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>""", unsafe_allow_html=True)
            _below = _reg_df[_reg_df["Target Status"] == "Below expansion target"]["Country"].tolist()
            _above = _reg_df[_reg_df["Target Status"] == "Above target"]["Country"].tolist()
            render_insight_note(
                ("Underperforming markets indicate where CyberNova may need more campaign activity or regional outreach. "
                 f"<strong>{', '.join(_below) if _below else 'No markets'}</strong> are below expansion target. "
                 f"<strong>{', '.join(_above[:2]) if _above else 'None'}</strong> "
                 f"{'are' if len(_above) > 1 else 'is'} above target."),
                AMBER_SOFT if _below else GREEN_SOFT,
                "#92400E" if _below else "#047857",
            )

    # ── EVIDENCE — EXECUTIVE DECISION BRIEF ─────────────────────
    render_section_label("EVIDENCE — EXECUTIVE DECISION BRIEF")
    brief_rows = [
        {"Strategic Signal":     "Growth improving" if m["mom_growth"]>=0 else "Growth declining",
         "Evidence":             f"MoM visitor change: {m['mom_growth']:+.1f}%",
         "Leadership Action":    "Sustain current acquisition momentum." if m["mom_growth"]>=0 else "Investigate and address traffic decline.",
         "Risk / Dependency":    "Seasonal variation may affect trend reliability."},
        {"Strategic Signal":     "AI Assistant gaining traction" if m["ai_share"]>=0.10 else "AI needs promotion",
         "Evidence":             f"AI share: {m['ai_share']:.1%} of service traffic",
         "Leadership Action":    "Scale AI positioning in SADC markets." if m["ai_share"]>=0.10 else "Increase AI Assistant campaign visibility.",
         "Risk / Dependency":    "Conversion quality must be tracked alongside volume."},
        {"Strategic Signal":     "Regional reach broadening" if m["sadc_total"]>=7 else "Regional penetration limited",
         "Evidence":             f"{m['sadc_total']} SADC markets active",
         "Leadership Action":    "Activate targeted content per SADC market." if m["sadc_total"]>=7 else "Focus on top 3 SADC markets first.",
         "Risk / Dependency":    "Country-specific regulatory and compliance factors."},
        {"Strategic Signal":     "Operational review required" if m["anom_days"]>0 else "Operations nominal",
         "Evidence":             f"{m['anom_days']} anomaly days flagged",
         "Leadership Action":    "Review anomaly log for security or infrastructure issues." if m["anom_days"]>0 else "Continue standard monitoring.",
         "Risk / Dependency":    "Anomaly patterns may require IT security team review." if m["anom_days"]>0 else "No elevated risk identified."},
    ]
    brief_df = pd.DataFrame(brief_rows)
    with st.container(border=True):
        render_card_header("Executive Decision Brief",
                           "Board-level strategic signals with recommended leadership actions and risk notes.")
        st.dataframe(brief_df, use_container_width=True, hide_index=True)

    # Regional priority table
    render_section_label("EVIDENCE — REGIONAL PRIORITY TABLE")
    if "country" in fdf.columns and "is_sadc" in fdf.columns:
        rpt = fdf.groupby(["country","is_sadc"]).agg(
            visitors=("ip_address","nunique"),
            warm_leads=("is_warm_lead","sum"),
            sessions=("session_id","nunique"),
        ).reset_index().sort_values("visitors",ascending=False)
        rpt["is_sadc"] = rpt["is_sadc"].map({True:"SADC",False:"Other"})
        rpt.columns = ["Country","Region","Visitors","Warm Leads","Sessions"]
        with st.container(border=True):
            render_card_header("Regional Priority Table",
                               "SADC vs other markets — ranked by unique visitors, warm leads, and session count.")
            st.dataframe(rpt, use_container_width=True, hide_index=True)

    # ── REPORTS ───────────────────────────────────────────────────
    kpis = [
        {"label":"MoM Visitor Growth",    "value":f"{m['mom_growth']:+.1f}%",  "note":f"{m['prev_vis']:,} to {m['curr_vis']:,}"},
        {"label":"AI Traction",           "value":f"{m['ai_share']:.1%}",      "note":"Service share"},
        {"label":"SADC Active Markets",   "value":str(m["sadc_total"]),         "note":"Countries"},
        {"label":"30-Day Lead Forecast",  "value":f"~{m['forecast']:,}",        "note":"Linear projection"},
        {"label":"Anomaly Days",          "value":str(m["anom_days"]),          "note":"Days flagged"},
    ]
    render_report_section("CyberNova Horizon", role, filters, kpis, bullets, fdf,
                          brief_df, "Executive Summary")

# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
def render_sidebar(df: pd.DataFrame) -> dict:
    role = st.session_state.get("role","")
    # Brand
    st.sidebar.markdown(f"""
<div style="padding:.8rem 0 .5rem;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;">
    <div style="overflow:hidden;flex-shrink:0;border-radius:15px;
      box-shadow:0 16px 32px rgba(37,99,255,.28);">{_logo_html(46, 15)}</div>
    <div>
      <strong style="display:block;font-size:18px;color:white;letter-spacing:-.04em;">CyberNova</strong>
      <span style="display:block;font-size:13px;color:#B8C7D9;margin-top:2px;">BI Intelligence Portal</span>
    </div>
  </div>
  <span style="display:inline-flex;align-items:center;padding:9px 14px;border-radius:999px;
    background:rgba(37,99,255,.20);border:1px solid rgba(37,99,255,.48);color:white;
    font-size:13px;font-weight:800;">{role}</span>
</div>
""", unsafe_allow_html=True)

    st.sidebar.markdown("---")

    # Demo credentials
    with st.sidebar.expander("Demo Credentials", expanded=False):
        rows_html = "".join(
            f'<div class="cred-row" style="display:flex;justify-content:space-between;'
            f'gap:10px;font-size:13px;margin:8px 0;color:#EFF6FF;">'
            f'<span>{r}</span>'
            f'<code style="background:rgba(37,99,255,.30);border:1px solid rgba(37,99,255,.55);'
            f'padding:3px 8px;border-radius:7px;color:white;font-weight:800;">{info["pw"]}</code>'
            f'</div>'
            for r, info in ROLES.items()
        )
        st.markdown(f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:.1em;'
                    f'color:#9FB2C7;margin-bottom:10px;font-weight:800;">Role → Password</div>'
                    f'{rows_html}', unsafe_allow_html=True)

    st.sidebar.markdown("---")
    # Navigation
    st.sidebar.markdown('<div style="font-size:11px;text-transform:uppercase;letter-spacing:.1em;'
                        'color:#9FB2C7;margin-bottom:10px;font-weight:800;">Navigation</div>',
                        unsafe_allow_html=True)
    accessible = [d for d in DASHBOARDS if d in ROLES.get(role,{}).get("access",[])]
    default    = st.session_state.get("nav", accessible[0] if accessible else DASHBOARDS[0])
    if default not in DASHBOARDS:
        default = DASHBOARDS[0]
    st.sidebar.radio("", DASHBOARDS, key="nav", index=DASHBOARDS.index(default))

    st.sidebar.markdown("---")
    # Filters
    st.sidebar.markdown('<div style="font-size:11px;text-transform:uppercase;letter-spacing:.1em;'
                        'color:#9FB2C7;margin-bottom:10px;font-weight:800;">Global Filters</div>',
                        unsafe_allow_html=True)
    if "fv" not in st.session_state:
        st.session_state["fv"] = 0
    v    = st.session_state["fv"]
    mn_d = df["date"].dt.date.min()
    mx_d = df["date"].dt.date.max()
    start = st.sidebar.date_input("Start date", value=mn_d, min_value=mn_d, max_value=mx_d, key=f"sd_{v}")
    end   = st.sidebar.date_input("End date",   value=mx_d, min_value=mn_d, max_value=mx_d, key=f"ed_{v}")
    all_c = sorted(df["country"].dropna().unique().tolist())
    all_s = sorted(df["service_name"].dropna().unique().tolist())
    all_t = sorted(df["status_class"].dropna().unique().tolist())
    all_g = sorted(df["segment"].dropna().unique().tolist())
    countries = st.sidebar.multiselect("Countries",    all_c, default=[],      key=f"co_{v}")
    services  = st.sidebar.multiselect("Services",     all_s, default=[],      key=f"sv_{v}")
    status_cl = st.sidebar.multiselect("HTTP Status",  all_t, default=["2xx"], key=f"sc_{v}")
    segments  = st.sidebar.multiselect("Segments",     all_g, default=[],      key=f"sg_{v}")
    inc_bots  = st.sidebar.toggle("Include bot traffic", value=False,           key=f"bt_{v}")
    cf1, cf2 = st.sidebar.columns(2)
    with cf1:
        if st.button("Apply", key="filter_apply", use_container_width=True):
            st.rerun()
    with cf2:
        if st.button("Reset", key="filter_reset", use_container_width=True):
            st.session_state["fv"] = v+1; st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        for k in ["logged_in","role","nav","fv"]: st.session_state.pop(k,None)
        st.rerun()
    st.sidebar.markdown(
        f'<div style="color:#9FB2C7;font-size:11px;line-height:1.5;margin-top:12px;">'
        f'Prototype access layer only. Production deployment requires authentication, '
        f'password hashing, audit logging, and full RBAC.</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption(f"CET333 · v3.0 · {pd.Timestamp.now().strftime('%H:%M')}")
    return {"start":start,"end":end,"countries":countries,"services":services,
            "status_classes":status_cl,"segments":segments,"include_bots":inc_bots}

# ─────────────────────────────────────────────────────────────────
# LOGIN  — two-panel full-page design
# ─────────────────────────────────────────────────────────────────
def render_login() -> None:
    # ── Page-level CSS overrides ──────────────────────────────────
    st.markdown("""
<style>
.stApp {
  background: #F8FAFC !important;
}
.block-container {
  padding-top: .6rem !important;
  padding-bottom: 1rem !important;
  max-width: 1300px !important;
}
[data-testid="stSidebarCollapsedControl"],
section[data-testid="stSidebar"] { display: none !important; }
.stSelectbox label { color: #52606D !important; font-weight: 700 !important; font-size: 13px !important; }
.stTextInput  label { color: #52606D !important; font-weight: 700 !important; font-size: 13px !important; }
div[data-testid="stSelectbox"] > div > div {
  border-radius: 11px !important; border: 1.5px solid #D9E2EC !important;
}
div[data-testid="stTextInputRootElement"] input {
  border-radius: 11px !important; border: 1.5px solid #D9E2EC !important;
}
</style>""", unsafe_allow_html=True)

    left, right = st.columns([12, 9], gap="large")

    # ──────────────────────────────────────────────────────────────
    # LEFT PANEL — hero card
    # ──────────────────────────────────────────────────────────────
    with left:
        dash_icons = {
            "Live Pulse":                 ("#2563FF", "#1E40AF",
                '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>'),
            "Strategic Analytics":        ("#16B8C7", "#0E7490",
                '<line x1="18" y1="20" x2="18" y2="10"/>'
                '<line x1="12" y1="20" x2="12" y2="4"/>'
                '<line x1="6"  y1="20" x2="6"  y2="14"/>'),
            "Weekly &amp; Monthly Reports": ("#10B981", "#065F46",
                '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
                '<polyline points="14 2 14 8 20 8"/>'
                '<line x1="16" y1="13" x2="8" y2="13"/>'
                '<line x1="16" y1="17" x2="8" y2="17"/>'),
            "Role-Based Access":          ("#F59E0B", "#78350F",
                '<rect x="3" y="11" width="18" height="11" rx="2"/>'
                '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'),
        }
        feat_descs = {
            "Live Pulse":
                "One Excel record streams every 3 seconds — real-time counters track traffic, "
                "warm leads, performance and security as they happen.",
            "Strategic Analytics":
                "Heatmaps, funnels, segment composition, geographic scatter charts, "
                "and a 30-day warm-lead forecast built from the full dataset.",
            "Weekly &amp; Monthly Reports":
                "Branded PDF exports with filter context, KPI summaries, narrative bullets, "
                "and evidence tables — generated on demand for every role.",
            "Role-Based Access":
                "Four tailored workspaces: Sales Command Center, Marketing Intelligence Hub, "
                "Executive Insights Dashboard, and full Admin view.",
        }

        feat_cards_html = ""
        for feat_title, (col_main, col_dark, icon_path) in dash_icons.items():
            feat_cards_html += f"""
<div style="display:flex;gap:14px;align-items:flex-start;
  padding:14px 16px 14px 14px;margin-bottom:10px;
  background:{SLATE_SOFT};
  border:1px solid {BORDER};
  border-radius:16px;
  box-shadow:0 4px 18px rgba(0,0,0,.18);">
  <div style="width:40px;height:40px;flex-shrink:0;border-radius:12px;
    background:linear-gradient(135deg,{col_main}dd,{col_main}66);
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 6px 16px {col_main}44;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      {icon_path}
    </svg>
  </div>
  <div style="flex:1;min-width:0;">
    <div style="color:{NAVY};font-weight:800;font-size:14px;margin-bottom:4px;
      letter-spacing:-.01em;">{feat_title}</div>
    <div style="color:{SECONDARY};font-size:12.5px;line-height:1.6;">
      {feat_descs[feat_title]}
    </div>
  </div>
</div>"""

        logo_img = _logo_html(72, 16)

        st.markdown(f"""
<div style="padding:2.2rem 2rem 2.2rem .5rem;min-height:90vh;
  display:flex;flex-direction:column;justify-content:center;">

  <!-- Logo + brand -->
  <div style="display:flex;align-items:center;gap:18px;margin-bottom:2rem;">
    <div style="border-radius:20px;overflow:hidden;flex-shrink:0;
      box-shadow:0 12px 32px rgba(37,99,255,.25),0 0 0 2px rgba(22,184,199,.20);">
      {logo_img}
    </div>
    <div>
      <div style="color:{NAVY};font-size:1.5rem;font-weight:900;
        letter-spacing:-.04em;line-height:1.1;">CyberNova Analytics</div>
      <div style="color:{CYAN};font-size:.8rem;font-weight:700;
        margin-top:4px;letter-spacing:.06em;text-transform:uppercase;">
        BI Intelligence Portal
      </div>
    </div>
  </div>

  <!-- Headline -->
  <div style="margin-bottom:1.6rem;">
    <h2 style="color:{NAVY};font-size:1.8rem;font-weight:900;letter-spacing:-.04em;
      line-height:1.18;margin:0 0 .6rem;">
      Sign in to your<br>intelligence workspace.
    </h2>
    <p style="color:{SECONDARY};font-size:14px;line-height:1.65;margin:0;max-width:420px;">
      Your role unlocks the right analytics, charts, and decisions.
      No noise — just the signals that matter to your team.
    </p>
  </div>

  <!-- Feature cards -->
  <div style="margin-bottom:1.5rem;">
    {feat_cards_html}
  </div>

  <!-- Role callout -->
  <div style="display:flex;align-items:center;gap:10px;padding:.75rem 1.1rem;
    border-radius:14px;background:{BLUE_SOFT};border:1px solid #BFDBFE;margin-bottom:.9rem;">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
      stroke="{BLUE}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
    <span style="color:{BLUE};font-size:13px;font-weight:700;">
      Select your role to access the correct intelligence workspace
    </span>
  </div>

  <!-- CET333 badge -->
  <div style="padding:.55rem .9rem;border-radius:10px;
    background:{AMBER_SOFT};border:1px solid #FCD34D;">
    <span style="color:#92400E;font-size:11px;font-weight:800;">
      CET333 Product Development &nbsp;&middot;&nbsp; Prototype &nbsp;&middot;&nbsp;
      CyberNova Analytics Ltd (Fictitious)
    </span>
  </div>

</div>""", unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────
    # RIGHT PANEL — demo credentials + login card
    # ──────────────────────────────────────────────────────────────
    with right:
        # ── Credentials card ──────────────────────────────────────
        dash_colours = {
            "CyberNova Pulse":    BLUE,
            "CyberNova Reach":    CYAN,
            "CyberNova Horizon":  GREEN,
        }
        cred_rows = ""
        for r, info in ROLES.items():
            badge_str = "&nbsp;+&nbsp;".join(
                f'<span style="background:{dash_colours.get(d,BLUE)}22;'
                f'color:{dash_colours.get(d,BLUE)};font-size:10px;font-weight:800;'
                f'padding:2px 7px;border-radius:6px;">'
                f'{d.replace("CyberNova ","")}</span>'
                for d in info["access"]
            )
            cred_rows += f"""
<tr>
  <td style="padding:9px 10px;font-weight:700;color:{NAVY};font-size:12px;
    border-bottom:1px solid {BORDER};">{r}</td>
  <td style="padding:9px 10px;font-size:12px;border-bottom:1px solid {BORDER};">
    {badge_str}
  </td>
  <td style="padding:9px 10px;border-bottom:1px solid {BORDER};">
    <code style="background:{BLUE_SOFT};color:{BLUE};font-size:11.5px;
      padding:3px 9px;border-radius:7px;font-weight:800;
      letter-spacing:.03em;">{info["pw"]}</code>
  </td>
</tr>"""

        st.markdown(f"""
<div style="background:white;border-radius:24px;padding:1.6rem 1.8rem 1.5rem;
  box-shadow:0 20px 50px rgba(0,0,0,.30),0 0 0 1px rgba(37,99,255,.07);
  margin-top:1.5rem;margin-bottom:.9rem;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
      stroke="{BLUE}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
    <span style="font-size:11px;font-weight:800;text-transform:uppercase;
      letter-spacing:.1em;color:{SECONDARY};">Demo Credentials</span>
  </div>
  <div style="border:1px solid {BORDER};border-radius:12px;overflow:hidden;">
    <table style="width:100%;border-collapse:collapse;font-size:12px;">
      <thead>
        <tr style="background:{SLATE_SOFT};">
          <th style="padding:8px 10px;text-align:left;color:{SECONDARY};font-size:10px;
            font-weight:800;text-transform:uppercase;letter-spacing:.08em;
            border-bottom:1px solid {BORDER};">Role</th>
          <th style="padding:8px 10px;text-align:left;color:{SECONDARY};font-size:10px;
            font-weight:800;text-transform:uppercase;letter-spacing:.08em;
            border-bottom:1px solid {BORDER};">Dashboard Access</th>
          <th style="padding:8px 10px;text-align:left;color:{SECONDARY};font-size:10px;
            font-weight:800;text-transform:uppercase;letter-spacing:.08em;
            border-bottom:1px solid {BORDER};">Password</th>
        </tr>
      </thead>
      <tbody>{cred_rows}</tbody>
    </table>
  </div>
</div>""", unsafe_allow_html=True)

        # ── Login card ────────────────────────────────────────────
        st.markdown(f"""
<div style="background:white;border-radius:24px;
  padding:1.8rem 1.8rem .5rem;
  box-shadow:0 20px 50px rgba(0,0,0,.30),0 0 0 1px rgba(37,99,255,.07);
  margin-bottom:.5rem;">
  <div style="display:inline-flex;align-items:center;gap:8px;
    background:{BLUE_SOFT};border-radius:999px;padding:5px 12px;margin-bottom:14px;">
    <div style="width:7px;height:7px;border-radius:999px;background:{GREEN};
      box-shadow:0 0 0 3px rgba(16,185,129,.28);"></div>
    <span style="color:{BLUE};font-size:11px;font-weight:800;
      text-transform:uppercase;letter-spacing:.09em;">Live Dashboard</span>
  </div>
  <h3 style="margin:0 0 5px;font-size:1.45rem;font-weight:900;
    color:{NAVY};letter-spacing:-.04em;">Sign in to your dashboard</h3>
  <p style="margin:0 0 1.1rem;color:{MUTED};font-size:13.5px;line-height:1.55;">
    Select your role to access the right intelligence workspace.
  </p>
</div>""", unsafe_allow_html=True)

        role = st.selectbox("Select your role", list(ROLES.keys()), key="login_role")
        pwd  = st.text_input("Password", type="password",
                             placeholder="Enter your password", key="login_pwd")
        login_clicked = st.button("Sign In to Dashboard",
                                  use_container_width=True, key="login_btn")
        if login_clicked:
            if pwd == ROLES[role]["pw"]:
                st.session_state["logged_in"] = True
                st.session_state["role"]      = role
                st.session_state["nav"]       = ROLES[role]["access"][0]
                st.rerun()
            else:
                st.error("Incorrect password — please check your credentials.")

        st.markdown(f"""
<div style="background:{AMBER_SOFT};border-left:3px solid {AMBER};
  padding:.6rem .9rem;border-radius:8px;color:#78350F;
  font-size:11.5px;line-height:1.55;margin-top:.6rem;margin-bottom:1rem;">
  <strong>Prototype access layer only.</strong> Production deployment would require
  authentication, password hashing, audit logging, and full role-based access control.
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main() -> None:
    inject_css()

    if not st.session_state.get("logged_in"):
        render_login()
        return

    with st.spinner("Loading cybernova_web_logs.xlsx..."):
        df = load_data()

    if df is None:
        st.error("Dataset not found at `data/output/cybernova_web_logs.xlsx`. "
                 "Ensure the Excel file exists in data/output/.")
        return

    missing = [c for c in ("timestamp","date","country","service_name","status_class",
                            "is_bot","session_id","is_warm_lead","event_type","uri",
                            "segment","ip_address","is_anomaly","distinct_pages_session",
                            "entry_page","hour","day_of_week","is_sadc","converted_to_lead")
               if c not in df.columns]
    if missing:
        st.warning(f"Dataset is missing columns: {missing}. Some charts may be limited.")

    # ── FR2 — Data Load Quality Summary (always visible) ─────────
    _raw_rows      = len(df)
    _bad_ts        = int(df["timestamp"].isna().sum()) if "timestamp" in df.columns else 0
    _bad_ip        = int(df["ip_address"].isna().sum()) if "ip_address" in df.columns else 0
    _usable_rows   = _raw_rows - max(_bad_ts, _bad_ip)
    _dup_rows      = int(df.duplicated().sum())
    _dq_good       = _bad_ts == 0 and _bad_ip == 0 and _dup_rows == 0
    _dq_col        = GREEN if _dq_good else AMBER
    _dq_soft       = GREEN_SOFT if _dq_good else AMBER_SOFT
    _dq_label      = "Good" if _dq_good else "Review Needed"

    def _dq_pill(label, val, col, soft):
        return (
            f'<div style="display:flex;flex-direction:column;align-items:center;'
            f'padding:10px 18px;border-radius:14px;background:{soft};'
            f'border:1px solid {col}22;min-width:110px;">'
            f'<span style="font-size:20px;font-weight:900;color:{col};letter-spacing:-.04em;">{val}</span>'
            f'<span style="font-size:10.5px;font-weight:700;color:{SECONDARY};'
            f'text-transform:uppercase;letter-spacing:.08em;margin-top:3px;">{label}</span>'
            f'</div>'
        )

    _dq_html = (
        f'<div style="background:white;border:1px solid {BORDER};border-radius:18px;'
        f'padding:14px 20px;margin-bottom:18px;box-shadow:0 2px 8px rgba(11,31,58,.05);">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'flex-wrap:wrap;gap:12px;">'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<span style="width:8px;height:8px;border-radius:50%;background:{_dq_col};'
        f'box-shadow:0 0 0 3px {_dq_soft};flex-shrink:0;"></span>'
        f'<span style="font-size:11px;text-transform:uppercase;letter-spacing:.12em;'
        f'font-weight:900;color:{MUTED};">Data Load Quality</span>'
        f'<span style="font-size:12px;font-weight:800;color:{_dq_col};'
        f'padding:3px 10px;border-radius:999px;background:{_dq_soft};">{_dq_label}</span>'
        f'</div>'
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;">'
        + _dq_pill("Raw Rows",   f"{_raw_rows:,}",   BLUE,      BLUE_SOFT)
        + _dq_pill("Usable",     f"{_usable_rows:,}", GREEN,     GREEN_SOFT)
        + _dq_pill("Bad Timestamps", f"{_bad_ts:,}",  AMBER if _bad_ts else GREEN, AMBER_SOFT if _bad_ts else GREEN_SOFT)
        + _dq_pill("Missing IPs",    f"{_bad_ip:,}",  AMBER if _bad_ip else GREEN, AMBER_SOFT if _bad_ip else GREEN_SOFT)
        + (f'<div style="display:flex;flex-direction:column;align-items:center;'
           f'padding:10px 18px;border-radius:14px;background:#FEE2E2;'
           f'border:1px solid #EF444422;min-width:110px;">'
           f'<span style="font-size:20px;font-weight:900;color:#DC2626;letter-spacing:-.04em;">{_dup_rows:,}</span>'
           f'<span style="font-size:10.5px;font-weight:700;color:{SECONDARY};'
           f'text-transform:uppercase;letter-spacing:.08em;margin-top:3px;">Duplicates</span>'
           f'</div>' if _dup_rows > 0 else "")
        + f'</div>'
        f'</div>'
        f'<div style="margin-top:8px;font-size:11px;color:{MUTED};">'
        f'Dropped/invalid records estimated from parsing checks. '
        f'Active row count shown in the filter chip bar above each dashboard.'
        f'</div>'
        f'</div>'
    )
    st.markdown(_dq_html, unsafe_allow_html=True)

    # Store full sorted DataFrame for the live ticker fragment
    st.session_state["_full_df"] = df
    _init_live_state(len(df))

    filters = render_sidebar(df)
    fdf     = apply_filters(
        df,
        filters["start"], filters["end"],
        filters["countries"], filters["services"],
        filters["status_classes"], filters["segments"],
        filters["include_bots"],
    )
    role = st.session_state.get("role","")
    nav  = st.session_state.get("nav", DASHBOARDS[0])

    # Scroll to top whenever the user switches dashboard
    if st.session_state.get("_prev_nav") != nav:
        st.session_state["_prev_nav"] = nav
        st.components.v1.html(
            "<script>"
            "const el = window.parent.document.querySelector("
            "  '[data-testid=\"stAppViewContainer\"] > section.main');"
            "if(el) el.scrollTo({top:0,behavior:'instant'});"
            "</script>",
            height=0,
        )

    has_access = lambda dash: dash in ROLES.get(role,{}).get("access",[])

    if nav == "CyberNova Pulse":
        if has_access(nav):
            show_pulse(fdf, filters, role)
        else:
            st.markdown(f"""
<div style="background:white;border:1px solid #FECACA;border-radius:20px;
  padding:3rem 2rem;text-align:center;margin-top:2rem;">
  <div style="font-size:1.35rem;font-weight:800;color:#0B1F3A;margin:.7rem 0 .5rem;">
    Access Restricted</div>
  <div style="color:#64748B;">
    <strong>{role}</strong> does not have access to <strong>{nav}</strong>.
  </div>
</div>""", unsafe_allow_html=True)
    elif nav == "CyberNova Reach":
        if has_access(nav):
            show_reach(fdf, filters, role)
        else:
            st.error(f"{role} does not have access to {nav}.")
    elif nav == "CyberNova Horizon":
        if has_access(nav):
            show_horizon(fdf, filters, role)
        else:
            st.error(f"{role} does not have access to {nav}.")

main()
