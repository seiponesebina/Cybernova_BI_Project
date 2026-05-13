import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime, pathlib, random, base64

_BASE = pathlib.Path(__file__).parent
_LOGO_PNG = _BASE / "logo.png"
_PAGE_ICON = _LOGO_PNG.read_bytes() if _LOGO_PNG.exists() else "⬡"

# Sales views - imported after page_config so Streamlit doesn't complain
try:
    from sales_views import (inject_sales_css,
                              render_sales_analytics, render_sales_forecasting,
                              render_sales_data)
    _SALES_VIEWS_OK = True
except Exception as _sv_err:
    _SALES_VIEWS_OK = False

try:
    from marketing_views import (inject_marketing_css, render_marketing_drawer,
                                  render_marketing_analytics, render_marketing_forecasting,
                                  render_marketing_data)
    _MARKETING_VIEWS_OK = True
except Exception as _mv_err:
    _MARKETING_VIEWS_OK = False

try:
    from executive_views import (inject_executive_css, render_executive_drawer,
                                  render_executive_analytics, render_executive_forecasting,
                                  render_executive_data)
    _EXECUTIVE_VIEWS_OK = True
except Exception as _ev_err:
    _EXECUTIVE_VIEWS_OK = False

st.set_page_config(page_title="CyberNova BI Portal", layout="wide",
                   initial_sidebar_state="collapsed", page_icon=_PAGE_ICON)

ENRICH_PATH = str(_BASE / "data" / "output" / "cybernova_enriched_logs.csv")
FAST_CACHE_PATH = _BASE / "data" / "output" / "cybernova_enriched_logs.fast.pkl"
PARQUET_CACHE_PATH = _BASE / "data" / "output" / "cybernova_enriched_logs.fast.parquet"
LIVE_QUEUE_PATH = _BASE / "data" / "live_stream_queue.csv"
LIVE_REPLAY_SPEEDS = {
    "Slow": {"rows_per_tick": 12},
    "Normal": {"rows_per_tick": 24},
    "Fast": {"rows_per_tick": 48},
}
LIVE_REPLAY_MAX_VISIBLE_ROWS = 1200
LIVE_REPLAY_REFRESH_MS = 15000
LIVE_REFRESH_ENABLED = False
LIVE_KPI_FRAGMENT_SECONDS = 5
LIVE_CHART_FRAGMENT_SECONDS = 12

# ── LOGO ──────────────────────────────────────────────────────────────────────
def _load_logo():
    for name, mime in [("logo.png","image/png"),("cybernova_logo_transparent.svg","image/svg+xml")]:
        p = _BASE / name
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            return f"data:{mime};base64,{b64}", mime
    return "", ""

LOGO_SRC, LOGO_MIME = _load_logo()
def logo_img(h=58, extra=""):
    return f'<img src="{LOGO_SRC}" style="height:{h}px;width:auto;display:inline-block;{extra}" />' if LOGO_SRC else '<span style="font-size:22px;color:#22D3EE;font-weight:900;">CN</span>'

_SVG_PATHS = {
    "alert": '<path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>',
    "archive": '<path d="M21 8v13H3V8"/><path d="M1 3h22v5H1z"/><path d="M10 12h4"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 7h18s-3 0-3-7"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5z"/>',
    "bot": '<rect x="4" y="8" width="16" height="12" rx="2"/><path d="M12 2v6"/><path d="M8 13h.01"/><path d="M16 13h.01"/><path d="M9 17h6"/>',
    "briefcase": '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><path d="M2 13h20"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-7"/>',
    "check": '<path d="m20 6-11 11-5-5"/>',
    "chevron": '<path d="m6 9 6 6 6-6"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "diamond": '<path d="M6 3h12l4 6-10 12L2 9l4-6Z"/><path d="M2 9h20"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>',
    "filter": '<path d="M22 3H2l8 9v7l4 2v-9l8-9Z"/>',
    "flag": '<path d="M4 22V4"/><path d="M4 4h13l-1 5 1 5H4"/>',
    "folder": '<path d="M3 7h6l2 2h10v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 0 20"/><path d="M12 2a15 15 0 0 0 0 20"/>',
    "lightbulb": '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M8.2 14A6 6 0 1 1 15.8 14c-.8.7-1.3 1.6-1.5 2.6H9.7A4.8 4.8 0 0 0 8.2 14Z"/>',
    "logout": '<path d="M10 17l5-5-5-5"/><path d="M15 12H3"/><path d="M21 19V5a2 2 0 0 0-2-2h-7"/>',
    "map": '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z"/><path d="M9 3v15"/><path d="M15 6v15"/>',
    "money": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    "sync": '<path d="M21 12a9 9 0 0 0-15-6.7L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 15 6.7L21 16"/><path d="M21 21v-5h-5"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
}

def svg_icon(name: str, size: int = 15, color: str = "currentColor") -> str:
    path = _SVG_PATHS.get(name, _SVG_PATHS["chart"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true" style="display:inline-block;vertical-align:-3px;flex:0 0 auto;">{path}</svg>'
    )

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
ROLE_PASSWORDS = {"Sales Team Lead":"sales123","Marketing Lead":"marketing123",
                  "Executive Management":"executive123","Admin / Lecturer View":"admin123"}
ROLE_DASHBOARDS = {"Sales Team Lead":["Sales"],"Marketing Lead":["Marketing"],
                   "Executive Management":["Executive"],"Admin / Lecturer View":["Sales","Marketing","Executive"]}
ROLE_META = {"Sales Team Lead":("Alex M.","Sales Director"),
             "Marketing Lead":("Jordan K.","Marketing Lead"),
             "Executive Management":("C. Mokoena","Executive"),
             "Admin / Lecturer View":("Admin","All Access")}
DASH_CFG = {
    "Sales":     {"title":"CyberNova Pulse",   "sub":"Sales Command Center • Potential Customer Intelligence",       "accent":"#22D3EE","icon":"Pulse"},
    "Marketing": {"title":"CyberNova Reach",   "sub":"Marketing Intelligence Hub • Campaign Opportunity Intelligence","accent":"#14B8A6","icon":"Reach"},
    "Executive": {"title":"CyberNova Horizon", "sub":"Executive Insights Dashboard • SADC Expansion Intelligence",   "accent":"#A855F7","icon":"Horizon"},
}
COLOR_MAP = {"Core Market":"#22D3EE","Strategic Hub":"#14B8A6","High Growth":"#FFD84A","Emerging":"#7CFF4F","Stable":"#8A98A6"}
PANEL_DASHBOARD_TITLES = {
    "Sales": "Sales Pulse Dashboard",
    "Marketing": "Marketing Reach Dashboard",
    "Executive": "Executive Horizon Dashboard",
}

def allowed(role): return ROLE_DASHBOARDS.get(role,["Sales"])

# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    css_file = _BASE / "styling.css"
    extra_css = css_file.read_text(encoding="utf-8") if css_file.exists() else ""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
:root{
  --bg:#04090F; --panel:#071820; --card:rgba(9,20,36,0.88);
  --border:rgba(34,211,238,0.12); --border-a:rgba(34,211,238,0.45);
  --txt:#F0F4F8; --muted:#6B7FA3; --dim:#3A4A5E;
  --cyan:#22D3EE; --teal:#14B8A6; --green:#4ADE80; --yellow:#FBBF24;
  --orange:#F59E0B; --red:#F87171; --purple:#A855F7;
}
*{box-sizing:border-box;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{
  background:var(--bg)!important;color:var(--txt)!important;font-family:'Inter',sans-serif!important;
}
[data-testid="stSidebar"]{display:none!important;}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stHeader"]{visibility:hidden!important;height:0!important;}
div.block-container{padding:0 0 44px 0!important;max-width:100%!important;}
/* Remove default streamlit gaps */
div[data-testid="stVerticalBlock"]{gap:4px!important;}
div[data-testid="stVerticalBlock"]>div{padding-top:0!important;padding-bottom:0!important;}
div[data-testid="stHorizontalBlock"]{gap:8px!important;align-items:stretch!important;}
div[data-testid="stColumn"]{display:flex!important;flex-direction:column!important;}
div[data-testid="stColumn"]>div[data-testid="stVerticalBlock"]{flex:1!important;}
div[data-testid="stVerticalBlockBorderWrapper"]{height:100%!important;}
div[data-testid="element-container"]{height:100%!important;}
/* Card */
.cn-card{
  background:linear-gradient(145deg,rgba(12,24,44,0.92),rgba(8,18,34,0.88));
  border:1px solid var(--border);border-radius:14px;
  padding:8px 12px;margin-bottom:4px;
  box-shadow:0 2px 20px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.03);
  backdrop-filter:blur(12px);transition:border-color .25s,box-shadow .25s;
  position:relative;overflow:hidden;
}
.cn-card::before{content:'';position:absolute;top:0;left:0;right:0;
  height:1px;background:linear-gradient(90deg,transparent,rgba(34,211,238,0.25),transparent);}
.cn-card:hover{border-color:var(--border-a);box-shadow:0 4px 32px rgba(0,212,255,0.1),inset 0 1px 0 rgba(255,255,255,0.03);}
/* KPI */
.kpi-card{
  background:linear-gradient(145deg,rgba(12,24,44,0.92),rgba(8,18,34,0.88));
  border:1px solid var(--border);border-radius:12px;
  padding:8px 12px;
  box-shadow:0 2px 16px rgba(0,0,0,0.45);backdrop-filter:blur(12px);
  transition:border-color .2s,transform .15s,box-shadow .2s;cursor:default;
  height:100%;box-sizing:border-box;
  position:relative;overflow:visible;
}
.kpi-card:hover{border-color:var(--border-a);transform:translateY(-1px);box-shadow:0 0 26px rgba(34,211,238,.18),0 2px 16px rgba(0,0,0,.45);}
.kpi-hover-insight{display:none;position:absolute;z-index:20;left:8px;right:8px;top:calc(100% + 5px);padding:7px 8px;border-radius:9px;background:rgba(4,9,15,.98);border:1px solid rgba(34,211,238,.32);box-shadow:0 12px 26px rgba(0,0,0,.36),0 0 18px rgba(34,211,238,.12);color:#DDE7EE;font-size:10px;line-height:1.25;text-transform:none;letter-spacing:0;font-weight:600;}
.kpi-card:hover .kpi-hover-insight{display:block;}
.pipeline-card{position:relative;overflow:visible!important;}
.pipeline-card:hover{border-color:rgba(34,211,238,.45);box-shadow:0 0 26px rgba(34,211,238,.18),0 2px 16px rgba(0,0,0,.45);}
.pipeline-card:hover .kpi-hover-insight{display:block;}
.kpi-label{font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;}
.kpi-value{font-size:1.25rem;font-weight:800;color:#FFFFFF;line-height:1.1;margin-bottom:3px;}
.kpi-value-sm{font-size:1.15rem;font-weight:700;color:#FFFFFF;line-height:1.1;margin-bottom:4px;}
.kpi-delta{display:inline-flex;align-items:center;gap:3px;font-size:10px;font-weight:600;
  padding:1px 6px;border-radius:20px;margin-bottom:3px;}
.delta-up{background:rgba(74,222,128,0.12);color:var(--green);border:1px solid rgba(74,222,128,0.2);}
.delta-watch{background:rgba(251,191,36,0.12);color:var(--yellow);border:1px solid rgba(251,191,36,0.2);}
.delta-down{background:rgba(248,113,113,0.12);color:var(--red);border:1px solid rgba(248,113,113,0.2);}
.kpi-sub{font-size:10px;color:var(--muted);}
.marketing-kpi-card{display:flex;flex-direction:column;justify-content:flex-start;}
.marketing-kpi-card .kpi-label,
.marketing-kpi-card .kpi-value,
.marketing-kpi-card .kpi-delta,
.marketing-kpi-card .kpi-sub{
  max-width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.marketing-kpi-card .kpi-delta{display:block;width:max-content;max-width:100%;}
.pulse-wrap-compact{min-height:0;padding:2px 8px;margin-bottom:5px;}
.pulse-wrap-compact .pulse-item{padding:0 8px;}
.pulse-wrap-compact .pl{font-size:7.5px;margin-bottom:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;}
.pulse-wrap-compact .pv{font-size:12px;line-height:1.05;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;}
.pulse-updated{margin-left:auto;font-size:9px;color:#66727D;white-space:nowrap;}
.pulse-wrap-compact .pulse-updated{font-size:8px;}
.marketing-overview-tight-start{height:0;margin-top:-6px;margin-bottom:-2px;}
.marketing-overview-safe div[data-testid="element-container"]{height:auto!important;min-height:0!important;}
.marketing-overview-safe div[data-testid="stVerticalBlock"]{gap:10px!important;}
.marketing-overview-safe div[data-testid="stColumn"]{min-width:0!important;display:flex!important;flex-direction:column!important;}
.marketing-overview-safe div[data-testid="stColumn"]>div[data-testid="stVerticalBlock"]{height:auto!important;min-height:0!important;gap:9px!important;}
.marketing-overview-safe div[data-testid="stPlotlyChart"]{width:100%!important;min-width:0!important;overflow:hidden!important;margin-bottom:4px!important;}
.marketing-overview-safe .js-plotly-plot{max-width:100%!important;}
.marketing-overview-safe .cn-card{width:100%;min-width:0;overflow:hidden!important;padding:9px 11px!important;margin-bottom:9px!important;position:relative;z-index:1;transition:border-color .2s,box-shadow .2s,transform .15s;}
.marketing-overview-safe .cn-card:hover{border-color:rgba(20,184,166,.58)!important;box-shadow:0 0 30px rgba(20,184,166,.18),0 0 16px rgba(34,211,238,.10),0 2px 20px rgba(0,0,0,.50)!important;transform:translateY(-1px);}
.marketing-overview-safe .sec-label{min-height:20px;line-height:1.22;white-space:normal;overflow-wrap:anywhere;}
.marketing-kpi-card{min-height:82px!important;padding:8px 10px!important;justify-content:space-between!important;overflow:visible!important;z-index:4;}
.marketing-kpi-card.marketing-kpi-anchor{border-color:rgba(20,184,166,.55)!important;box-shadow:0 0 28px rgba(20,184,166,.18),0 2px 16px rgba(0,0,0,.45)!important;}
.marketing-kpi-card:hover{border-color:rgba(20,184,166,.62)!important;box-shadow:0 0 30px rgba(20,184,166,.22),0 0 18px rgba(34,211,238,.12),0 2px 16px rgba(0,0,0,.45)!important;}
.marketing-overview-safe .kpi-hover-insight{display:none;position:absolute;z-index:40;left:10px;right:10px;top:calc(100% + 7px);padding:9px 10px;border-radius:10px;background:rgba(4,9,15,.98);border:1px solid rgba(20,184,166,.38);box-shadow:0 14px 30px rgba(0,0,0,.42),0 0 20px rgba(20,184,166,.15);color:#DDE7EE;font-size:10.5px;line-height:1.35;font-weight:650;text-transform:none;letter-spacing:0;}
.marketing-overview-safe .kpi-card:hover .kpi-hover-insight{display:block;}
.mkt-insight-action{background:linear-gradient(135deg,rgba(20,184,166,.14),rgba(34,211,238,.06));border:1px solid rgba(20,184,166,.32);border-left:3px solid #14B8A6;border-radius:10px;padding:8px 12px;margin:6px 0 14px;box-shadow:0 0 22px rgba(20,184,166,.08);position:relative;z-index:2;clear:both;}
.mkt-insight-action .title{font-size:9px;font-weight:850;letter-spacing:.14em;text-transform:uppercase;color:#14B8A6;margin-bottom:3px;}
.mkt-insight-action .text{font-size:14px;line-height:1.25;font-weight:800;color:#F8FAFC;overflow-wrap:anywhere;}
.mkt-mini-table{width:100%;border-collapse:collapse;font-size:10px;color:#CBD5E1;table-layout:fixed;}
.mkt-mini-table th{color:#6B7FA3;font-size:7.5px;text-transform:uppercase;letter-spacing:.06em;font-weight:800;padding:3px 3px;border-bottom:1px solid rgba(20,184,166,.14);text-align:left;}
.mkt-mini-table td{padding:4px 3px;border-bottom:1px solid rgba(148,163,184,.08);vertical-align:top;overflow-wrap:anywhere;}
.mkt-mini-table th,.mkt-mini-table td{white-space:normal!important;min-width:0!important;}
.mkt-action-list{display:grid;gap:5px;margin-top:0;}
.mkt-action-line{display:flex;gap:7px;align-items:flex-start;color:#DDE7EE;font-size:10.5px;line-height:1.25;padding:5px 7px;border:1px solid rgba(20,184,166,.12);border-radius:8px;background:rgba(20,184,166,.045);}
.mkt-callout-main{font-size:14px;font-weight:850;color:#F8FAFC;line-height:1.2;margin:3px 0 3px;overflow-wrap:anywhere;}
.mkt-callout-sub{font-size:10px;color:#6B7FA3;line-height:1.25;}
.mkt-funnel-drop{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:3px 0;border-bottom:1px solid rgba(148,163,184,.08);font-size:9.5px;color:#CBD5E1;}
.mkt-funnel-drop b{color:#FBBF24;}
.executive-overview-tight-start{height:0;margin-top:-6px;margin-bottom:-2px;}
.executive-kpi-card{display:flex;flex-direction:column;justify-content:flex-start;}
.executive-kpi-card .kpi-label,
.executive-kpi-card .kpi-value,
.executive-kpi-card .kpi-delta,
.executive-kpi-card .kpi-sub{max-width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.executive-kpi-card .kpi-delta{display:block;width:max-content;max-width:100%;}
.executive-board-summary{display:none!important;padding:2px 10px!important;margin:2px 0 0!important;line-height:1.15;}
.executive-board-summary span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.executive-insight-below{margin-top:6px;}
.executive-drawer-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;align-items:stretch;}
.executive-drawer-grid .cn-card{height:100%;margin-bottom:0!important;}
.sales-action-panel .action-line{font-size:11px;color:#DDE7EE;margin:7px 0;line-height:1.35;}
.sales-action-panel .action-line b{color:#22D3EE;}
.sales-mini-table{width:100%;border-collapse:collapse;font-size:10px;color:#CBD5E1;}
.sales-mini-table th{color:#6B7FA3;font-size:9px;text-transform:uppercase;letter-spacing:.08em;font-weight:700;padding:4px 3px;border-bottom:1px solid rgba(34,211,238,.12);}
.sales-mini-table td{padding:5px 3px;border-bottom:1px solid rgba(148,163,184,.08);vertical-align:top;}
.sales-mini-table th,.sales-mini-table td{white-space:normal;overflow-wrap:anywhere;}
.sales-overview-contact .cn-card,.cn-card.sales-overview-contact{padding:6px 8px!important;margin-bottom:5px!important;}
.sales-overview-contact .sec-label{margin-bottom:3px!important;padding-bottom:3px!important;}
.sales-overview-contact .regional-live-card,.regional-live-card.sales-overview-contact{min-height:0!important;}
.sales-overview-contact .regional-table th{padding:3px 2px!important;font-size:8px!important;}
.sales-overview-contact .regional-table td{padding:4px 2px!important;font-size:9px!important;}
.sales-overview-contact .regional-market span{max-width:82px;display:inline-block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle;}
.sales-overview-map-note{font-size:9px;color:#6B7FA3;margin-bottom:2px;line-height:1.2;}
.trend-anchor{display:inline-flex;align-items:center;gap:5px;margin-bottom:4px;padding:2px 7px;border-radius:999px;background:rgba(74,222,128,.10);border:1px solid rgba(74,222,128,.24);color:#4ADE80;font-size:9px;font-weight:800;max-width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.sales-next-action{margin:8px 0 8px;padding:8px 0;border-top:1px solid rgba(34,211,238,.12);border-bottom:1px solid rgba(34,211,238,.12);font-size:20px;line-height:1.25;font-weight:850;color:#F8FAFC;}
.sales-next-action b{color:#4ADE80;}
.sales-insights-list{padding:8px 0 0;margin:0;color:#DDE7EE;font-size:11px;line-height:1.35;}
.sales-insights-list div{margin:4px 0;}
.sales-overview-safe div[data-testid="stColumn"]{min-width:0!important;}
.sales-overview-safe div[data-testid="stPlotlyChart"]{min-width:0!important;overflow:hidden!important;}
.sales-overview-safe .cn-card{overflow:hidden!important;}
.st-key-sales_regional_opportunity_map{background:linear-gradient(145deg,rgba(12,24,44,0.92),rgba(8,18,34,0.88));border:1px solid rgba(34,211,238,0.12);border-radius:14px;padding:6px 8px;margin-bottom:5px;box-shadow:0 2px 20px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.03);overflow:hidden;}
.st-key-sales_regional_opportunity_map:hover{border-color:rgba(34,211,238,0.45);box-shadow:0 4px 32px rgba(0,212,255,0.1),inset 0 1px 0 rgba(255,255,255,0.03);}
.sales-overview-map-card{min-height:366px;}
.sales-overview-side-card{min-height:0;}
.sales-priority{display:inline-flex;align-items:center;justify-content:center;min-width:22px;border-radius:999px;background:rgba(34,211,238,.12);border:1px solid rgba(34,211,238,.25);color:#22D3EE;font-weight:800;}
/* Section label */
.sec-label{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:var(--cyan);margin-bottom:4px;padding-bottom:4px;
  border-bottom:1px solid rgba(34,211,238,0.12);display:flex;align-items:center;gap:6px;}
/* Pulse strip */
.pulse-wrap{
  background:linear-gradient(90deg,rgba(34,211,238,0.06),rgba(20,184,166,0.04),rgba(34,211,238,0.03));
  border:1px solid rgba(34,211,238,0.18);border-radius:10px;
  padding:5px 12px;display:flex;gap:0;align-items:center;margin-bottom:6px;
}
.pulse-item{display:flex;flex-direction:column;align-items:center;padding:0 16px;
  border-right:1px solid rgba(34,211,238,0.1);}
.pulse-item:last-child{border-right:none;}
.pl{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px;}
.pv{font-size:15px;font-weight:700;color:var(--cyan);}
.live-dot{display:inline-block;width:6px;height:6px;background:var(--green);border-radius:50%;
  box-shadow:0 0 7px rgba(74,222,128,0.45);margin-right:6px;}
/* Chip */
.chip{display:inline-block;padding:2px 9px;border-radius:20px;font-size:10px;font-weight:500;
  background:rgba(34,211,238,0.06);border:1px solid rgba(34,211,238,0.15);
  color:var(--cyan);margin:0 4px 4px 0;}
/* Placeholder */
.ph-card{background:rgba(9,20,36,0.7);border:1px dashed rgba(34,211,238,0.15);
  border-radius:12px;padding:32px 20px;text-align:center;color:var(--muted);
  font-size:12px;min-height:110px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:8px;}
/* Right panel */
.rp-section{margin-bottom:16px;}
.rp-label{font-size:9px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
  color:var(--dim);margin-bottom:8px;padding-left:2px;}
.rp-dash-btn{
  width:100%;padding:9px 12px;border-radius:10px;margin-bottom:6px;cursor:pointer;
  background:rgba(9,20,36,0.6);border:1px solid rgba(34,211,238,0.1);
  display:flex;align-items:center;gap:10px;transition:all .2s;
}
.rp-dash-btn:hover{border-color:var(--border-a);background:rgba(34,211,238,0.06);}
.rp-dash-btn.active{
  background:linear-gradient(135deg,rgba(34,211,238,0.14),rgba(20,184,166,0.08));
  border-color:rgba(34,211,238,0.35);
  box-shadow:0 0 16px rgba(34,211,238,0.1);
}
/* Leaderboard table */
.lb-row{display:flex;align-items:center;padding:7px 0;border-bottom:1px solid rgba(34,211,238,0.06);font-size:12px;}
.lb-row:last-child{border-bottom:none;}
/* Status bar — fixed footer */
.status-bar{
  position:fixed;bottom:0;left:0;right:0;z-index:9999;
  background:linear-gradient(90deg,rgba(6,13,22,0.98),rgba(5,10,18,0.98));
  border-top:1px solid rgba(34,211,238,0.14);border-radius:0;
  padding:5px 20px;display:flex;gap:20px;align-items:center;
  flex-wrap:nowrap;
}
.si{font-size:11px;color:var(--muted);}
.si span{color:var(--txt);font-weight:600;}
.pill-ok{background:rgba(74,222,128,0.1);color:var(--green);border:1px solid rgba(74,222,128,0.25);
  border-radius:20px;padding:3px 10px;font-size:10px;font-weight:600;}
.pill-warn{background:rgba(248,113,113,0.1);color:var(--red);border:1px solid rgba(248,113,113,0.25);
  border-radius:20px;padding:3px 10px;font-size:10px;font-weight:600;}
/* Tabs */
.stTabs [data-baseweb="tab-list"]{
  background:rgba(7,16,28,0.8)!important;border-radius:10px!important;
  border:1px solid rgba(34,211,238,0.1)!important;padding:3px!important;gap:2px!important;
  margin-bottom:6px!important;
}
.stTabs [data-baseweb="tab"]{
  border-radius:8px!important;color:var(--muted)!important;
  font-size:12px!important;font-weight:500!important;padding:7px 18px!important;
  transition:all .2s!important;
}
.stTabs [aria-selected="true"]{
  background:rgba(34,211,238,0.1)!important;color:#FFFFFF!important;
  border-bottom:2px solid var(--cyan)!important;font-weight:600!important;
}
/* Inputs */
.stSelectbox>div>div,.stTextInput>div>input{
  background:rgba(9,20,36,0.9)!important;border:1px solid rgba(34,211,238,0.18)!important;
  color:var(--txt)!important;border-radius:8px!important;font-size:12px!important;
}
.stSelectbox>div>div:focus-within,.stTextInput>div>input:focus{
  border-color:var(--cyan)!important;box-shadow:0 0 0 2px rgba(34,211,238,0.12)!important;
}
.stDateInput>div>input{background:rgba(9,20,36,0.9)!important;border-color:rgba(34,211,238,0.18)!important;
  color:var(--txt)!important;font-size:12px!important;}
label,.stSelectbox label,.stTextInput label,.stDateInput label{color:var(--muted)!important;font-size:10px!important;
  font-weight:600!important;letter-spacing:.1em!important;text-transform:uppercase!important;}
.stButton>button{
  background:linear-gradient(135deg,rgba(20,184,166,0.2),rgba(34,211,238,0.12))!important;
  border:1px solid rgba(34,211,238,0.3)!important;color:var(--cyan)!important;
  border-radius:8px!important;font-weight:600!important;font-size:12px!important;
}
.stButton>button:hover{
  background:linear-gradient(135deg,rgba(20,184,166,0.35),rgba(34,211,238,0.22))!important;
  box-shadow:0 0 16px rgba(34,211,238,0.2)!important;
}
/* Logout button: last column inside hdr_col2 (itself the last outer column) */
[data-testid="stHorizontalBlock"]>[data-testid="column"]:last-child
  >[div]>[data-testid="stHorizontalBlock"]>[data-testid="column"]:last-child
  .stButton>button,
[data-testid="stHorizontalBlock"]>[data-testid="column"]:last-child
  >div>[data-testid="stHorizontalBlock"]>[data-testid="column"]:last-child
  .stButton>button{
  background:rgba(248,113,113,0.08)!important;
  border:1px solid rgba(248,113,113,0.35)!important;
  color:#F87171!important;
}
[data-testid="stHorizontalBlock"]>[data-testid="column"]:last-child
  >div>[data-testid="stHorizontalBlock"]>[data-testid="column"]:last-child
  .stButton>button:hover{
  background:rgba(248,113,113,0.2)!important;
  border-color:#F87171!important;
  box-shadow:0 0 16px rgba(248,113,113,0.2)!important;
}
/* Keep the dashboard visually stable during fragment updates. */
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
section.main,
div.block-container{
  opacity:1!important;
  filter:none!important;
  transition:none!important;
}
[data-testid="stStatusWidget"],
[data-testid="stSpinner"]{
  display:none!important;
}
</style>""", unsafe_allow_html=True)
    if extra_css:
        st.markdown(f"<style>{extra_css}</style>", unsafe_allow_html=True)

# ── DATA ──────────────────────────────────────────────────────────────────────
def _optimize_dashboard_frame(df):
    if df is None or df.empty:
        return df
    out = df.copy()
    for col in ["country", "service_name", "segment", "status_class", "risk_level", "market_status"]:
        if col in out.columns and out[col].dtype == object:
            out[col] = out[col].astype("category")
    for col in [
        "is_bot", "is_sadc", "is_warm_lead", "potential_customer_signal",
        "has_demo_request", "has_event_signup", "is_engaged_session",
        "has_ai_interest", "is_anomaly",
    ]:
        if col in out.columns:
            out[col] = _truthy_series(out, col)
    return out


@st.cache_resource(show_spinner=False)
def _load_data_cached(csv_mtime, fast_cache_mtime):
    try:
        csv_path = pathlib.Path(ENRICH_PATH)
        cache_needs_write = False
        parquet_needs_write = False
        if PARQUET_CACHE_PATH.exists() and PARQUET_CACHE_PATH.stat().st_mtime >= csv_path.stat().st_mtime:
            df = pd.read_parquet(PARQUET_CACHE_PATH)
        elif FAST_CACHE_PATH.exists() and FAST_CACHE_PATH.stat().st_mtime >= csv_path.stat().st_mtime:
            df = pd.read_pickle(FAST_CACHE_PATH)
            parquet_needs_write = True
        else:
            df = pd.read_csv(ENRICH_PATH, low_memory=False)
            cache_needs_write = True
            parquet_needs_write = True
        if "timestamp" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        if "date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = _optimize_dashboard_frame(df)
        if cache_needs_write:
            try:
                df.to_pickle(FAST_CACHE_PATH)
            except Exception:
                pass
        if parquet_needs_write:
            try:
                df.to_parquet(PARQUET_CACHE_PATH, index=False)
            except Exception:
                pass
        return df
    except Exception: return None


def load_data():
    csv_path = pathlib.Path(ENRICH_PATH)
    csv_mtime = csv_path.stat().st_mtime if csv_path.exists() else 0
    fast_cache_mtime = max(
        FAST_CACHE_PATH.stat().st_mtime if FAST_CACHE_PATH.exists() else 0,
        PARQUET_CACHE_PATH.stat().st_mtime if PARQUET_CACHE_PATH.exists() else 0,
    )
    return _load_data_cached(csv_mtime, fast_cache_mtime)

@st.cache_data(show_spinner=False)
def _load_live_queue_cached(queue_mtime):
    if not LIVE_QUEUE_PATH.exists():
        return None
    try:
        df = pd.read_csv(LIVE_QUEUE_PATH, low_memory=False)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df
    except Exception:
        return None

def load_live_queue():
    queue_mtime = LIVE_QUEUE_PATH.stat().st_mtime if LIVE_QUEUE_PATH.exists() else 0
    return _load_live_queue_cached(queue_mtime)

def _normalize_live_queue(live_df):
    if live_df is None or live_df.empty:
        return pd.DataFrame()
    live = live_df.copy()
    rename_map = {
        "service": "service_name",
        "campaign": "campaign_name",
        "opportunity_value": "estimated_deal_value",
        "bytes_sent": "bytes_transferred",
    }
    live = live.rename(columns={k: v for k, v in rename_map.items() if k in live.columns and v not in live.columns})
    if "service_name" not in live.columns and "uri" in live.columns:
        live["service_name"] = live["uri"].astype(str).str.replace("/", "", regex=False).str.replace(".php", "", regex=False).str.replace("-", " ", regex=False).str.title()
    if "potential_customer_signal" not in live.columns:
        live["potential_customer_signal"] = _truthy_series(live, "is_warm_lead")
    if "has_demo_request" not in live.columns:
        uri = live["uri"].astype(str) if "uri" in live.columns else pd.Series("", index=live.index)
        stage = live["funnel_stage"].astype(str) if "funnel_stage" in live.columns else pd.Series("", index=live.index)
        live["has_demo_request"] = uri.str.contains("demo", case=False, na=False) | stage.str.contains("demo", case=False, na=False)
    if "has_event_signup" not in live.columns:
        uri = live["uri"].astype(str) if "uri" in live.columns else pd.Series("", index=live.index)
        stage = live["funnel_stage"].astype(str) if "funnel_stage" in live.columns else pd.Series("", index=live.index)
        live["has_event_signup"] = uri.str.contains("event", case=False, na=False) | stage.str.contains("event", case=False, na=False)
    if "is_engaged_session" not in live.columns:
        stage = live["funnel_stage"].astype(str) if "funnel_stage" in live.columns else pd.Series("", index=live.index)
        live["is_engaged_session"] = (
            _truthy_series(live, "potential_customer_signal")
            | _truthy_series(live, "has_demo_request")
            | _truthy_series(live, "has_event_signup")
            | stage.str.contains("service|contact|demo|event|ai", case=False, na=False)
        )
    if "has_ai_interest" not in live.columns:
        service = live["service_name"].astype(str) if "service_name" in live.columns else pd.Series("", index=live.index)
        uri = live["uri"].astype(str) if "uri" in live.columns else pd.Series("", index=live.index)
        live["has_ai_interest"] = service.str.contains("AI|Assistant|Predictive", case=False, na=False) | uri.str.contains("ai", case=False, na=False)
    if "status_class" not in live.columns and "status_code" in live.columns:
        status_num = pd.to_numeric(live["status_code"], errors="coerce").fillna(0).astype(int)
        live["status_class"] = (status_num // 100).astype(str) + "xx"
    if "hour" not in live.columns and "timestamp" in live.columns:
        live["hour"] = pd.to_datetime(live["timestamp"], errors="coerce").dt.hour
    live["_source"] = "live_replay"
    for c in ["is_bot", "is_warm_lead", "potential_customer_signal", "has_demo_request", "has_event_signup", "is_engaged_session", "has_ai_interest"]:
        if c in live.columns:
            live[c] = _truthy_series(live, c)
    return live

def _combine_historical_live(historical_df, live_rows):
    if live_rows is None or live_rows.empty:
        return historical_df
    hist = historical_df if historical_df is not None else pd.DataFrame()
    live = _normalize_live_queue(live_rows)
    for col in live.columns:
        if col not in hist.columns:
            hist[col] = pd.NA
    for col in hist.columns:
        if col not in live.columns:
            live[col] = pd.NA
    live = live[list(hist.columns)]
    return pd.concat([hist, live], ignore_index=True, copy=False)

def _release_live_rows(queue_df=None):
    if not LIVE_QUEUE_PATH.exists():
        st.session_state.live_rows_released = 0
        return pd.DataFrame()
    speed = st.session_state.get("live_replay_speed", "Normal")
    cfg = LIVE_REPLAY_SPEEDS.get(speed, LIVE_REPLAY_SPEEDS["Normal"])
    old = int(st.session_state.get("live_rows_released", 0))
    if old >= LIVE_REPLAY_MAX_VISIBLE_ROWS:
        old = 0
        st.session_state.live_rows_released = 0
        st.session_state.live_replay_started_at = datetime.datetime.now().isoformat()
    rows_per_tick = int(cfg.get("rows_per_tick", 50))
    prev = min(LIVE_REPLAY_MAX_VISIBLE_ROWS, max(rows_per_tick, old + rows_per_tick))
    st.session_state.live_rows_released = max(old, prev)
    prev = int(st.session_state.live_rows_released)
    st.session_state.live_rows_added_session = max(0, prev)
    st.session_state.live_last_refresh = datetime.datetime.now().strftime("%H:%M:%S")
    try:
        source = queue_df if queue_df is not None else load_live_queue()
        live = source.head(prev).copy() if source is not None and not source.empty else pd.DataFrame()
    except Exception:
        st.session_state.live_rows_released = 0
        return pd.DataFrame()
    if live.empty:
        return live
    live = live.tail(LIVE_REPLAY_MAX_VISIBLE_ROWS).copy()
    if not live.empty and "timestamp" in live.columns:
        now = pd.Timestamp.now().floor("s")
        live["timestamp"] = pd.date_range(end=now, periods=len(live), freq="s")
        live["date"] = live["timestamp"].dt.normalize()
        live["time"] = live["timestamp"].dt.strftime("%H:%M:%S")
        live["hour"] = live["timestamp"].dt.hour
    return live


def _refresh_live_replay_cache():
    try:
        live_rows = _release_live_rows()
        live_norm = _normalize_live_queue(live_rows)
        if live_norm is not None and not live_norm.empty:
            st.session_state["_live_replay_df"] = live_norm
            return live_norm
    except Exception:
        return st.session_state.get("_live_replay_df", pd.DataFrame())
    return st.session_state.get("_live_replay_df", pd.DataFrame())


def _maybe_autorefresh_live():
    if not LIVE_REFRESH_ENABLED:
        return
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=LIVE_REPLAY_REFRESH_MS, key="live_feed_tick")
    except Exception:
        return

def mock_data():
    np.random.seed(42); n=3000
    _end = datetime.date.today()
    _start = _end - datetime.timedelta(days=89)
    dates = pd.date_range(str(_start), str(_end), periods=n)
    return pd.DataFrame({
        "timestamp":dates,"date":dates.date,"hour":np.random.randint(0,24,n),
        "country":np.random.choice(["South Africa","Zambia","Mozambique","Botswana","Angola","Zimbabwe","Namibia","Malawi"],n,p=[.36,.14,.12,.10,.09,.08,.06,.05]),
        "service_name":np.random.choice(["AI Solutions","Cybersecurity","Cloud & Data","Advisory & Training","Other"],n,p=[.38,.25,.20,.10,.07]),
        "is_bot":np.random.choice([True,False],n,p=[.2,.8]),
        "potential_customer_signal":np.random.choice([True,False],n,p=[.3,.7]),
        "has_demo_request":np.random.choice([True,False],n,p=[.1,.9]),
        "segment":np.random.choice(["Enterprise","SMB","Government","Individual"],n),
        "estimated_deal_value":np.random.uniform(5000,150000,n),
        "risk_level":np.random.choice(["Low","Medium","High"],n,p=[.6,.3,.1]),
        "city":np.random.choice(["Cape Town","Lusaka","Maputo","Gaborone","Luanda","Harare","Windhoek","Durban","Lilongwe"],n),
    })

def _truthy_series(df, col):
    if df is None or col not in df.columns:
        return pd.Series(False, index=df.index if df is not None else [])
    s = df[col]
    if s.dtype == bool:
        return s.fillna(False)
    return s.astype(str).str.lower().isin(["1", "true", "yes", "y"])

def _num_series(df, col):
    if df is None or col not in df.columns:
        return pd.Series(0, index=df.index if df is not None else [], dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(0)

def _human_df(df):
    if df is None or df.empty:
        return pd.DataFrame()
    return df[~_truthy_series(df, "is_bot")].copy() if "is_bot" in df.columns else df.copy()

def _fmt_money(value):
    value = float(value or 0)
    if value >= 1_000_000:
        return f"P{value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"P{value/1_000:.0f}K"
    return f"P{value:,.0f}"

def _top_value(df, col, fallback="--"):
    if df is None or df.empty or col not in df.columns:
        return fallback
    vc = df[col].dropna().astype(str).value_counts()
    return vc.index[0] if not vc.empty else fallback

def _date_series(df):
    if df is None or df.empty:
        return pd.Series(dtype="object")
    date_col = "date" if "date" in df.columns else "timestamp" if "timestamp" in df.columns else None
    if not date_col:
        return pd.Series([None] * len(df), index=df.index)
    return pd.to_datetime(df[date_col], errors="coerce").dt.date

def _today_reference_date(df):
    dates = _date_series(df)
    today = datetime.date.today()
    if not dates.empty and (dates == today).any():
        return today
    return dates.max() if not dates.empty and dates.notna().any() else today

def _today_slice(df):
    if df is None or df.empty:
        return pd.DataFrame()
    work = df
    today = datetime.date.today()
    dates = _date_series(work)
    day_df = work[dates == today]
    if day_df.empty and not dates.empty and dates.notna().any():
        day_df = work[dates == dates.max()]
    return day_df

def _live_today_df(df, key="global", rows_per_tick=4, max_rows=5000, preload_fraction=0.78):
    """Worldometer-style live feed: show today's current tally, then increment smoothly."""
    today_df = _today_slice(df)
    if today_df.empty:
        return today_df
    today_df = today_df.sort_values("timestamp" if "timestamp" in today_df.columns else today_df.columns[0]).reset_index(drop=True)
    cursor_key = f"_live_cursor_{key}"
    if cursor_key not in st.session_state:
        st.session_state[cursor_key] = min(len(today_df), max(int(len(today_df) * preload_fraction), int(rows_per_tick)))
    cursor = int(st.session_state.get(cursor_key, 0))
    next_cursor = min(len(today_df), cursor + max(1, int(rows_per_tick)))
    st.session_state[cursor_key] = next_cursor
    live_df = today_df.iloc[:next_cursor].tail(max_rows).copy()
    now = pd.Timestamp.now().floor("s")
    live_df["timestamp"] = pd.date_range(end=now, periods=len(live_df), freq="s")
    live_df["date"] = _today_reference_date(df)
    live_df["time"] = live_df["timestamp"].dt.strftime("%H:%M:%S")
    return live_df

def _kpi_stats(df):
    human = _human_df(df)
    total = len(human)
    potential = int(_truthy_series(human, "potential_customer_signal").sum()) if not human.empty else 0
    demos = int(_truthy_series(human, "has_demo_request").sum()) if not human.empty else 0
    engaged = int(_truthy_series(human, "is_engaged_session").sum()) if "is_engaged_session" in human.columns else max(0, int(total * 0.28))
    ai_sessions = int(_truthy_series(human, "has_ai_interest").sum()) if "has_ai_interest" in human.columns else (
        int(human["service_name"].astype(str).str.contains("AI", case=False, na=False).sum()) if "service_name" in human.columns else 0
    )
    opportunity = float(_num_series(human, "estimated_deal_value").sum())
    quality = int(round((1 - (_truthy_series(df, "is_bot").mean() if df is not None and len(df) else 0)) * 100))
    active_markets = int(human["country"].nunique()) if "country" in human.columns and not human.empty else 0
    risk_alerts = int((_num_series(human, "risk_score") >= 70).sum()) if "risk_score" in human.columns else int(_truthy_series(human, "is_anomaly").sum()) if "is_anomaly" in human.columns else 0
    return {
        "rows": len(df) if df is not None else 0,
        "human": total,
        "potential": potential,
        "demos": demos,
        "engaged": engaged,
        "engagement_rate": (engaged / total * 100) if total else 0,
        "ai_rate": (ai_sessions / total * 100) if total else 0,
        "opportunity": opportunity,
        "top_market": _top_value(human, "country", "--"),
        "top_service": _top_value(human, "service_name", "--"),
        "quality": quality,
        "active_markets": active_markets,
        "risk_alerts": risk_alerts,
    }

# ── STATE ─────────────────────────────────────────────────────────────────────
def init_state():
    # Compute default date range: last 7 days from today
    _today = datetime.date.today()
    _d_end = _today
    _d_start = _today - datetime.timedelta(days=6)
    d = {"authenticated":False,"current_role":None,"active_dashboard":"Sales","active_tab":"Overview",
         "selected_market":"All","date_start":_d_start,"date_end":_d_end,
         "svc_filter":"All Services","seg_filter":"All Segments","outcome_filter":"All",
         "status_filter":"All Status Codes",
         "s_cust":1248,"s_demos":312,"s_rev":82.6,
         "m_aud":3840,"m_visits":1240,"m_qual":78,
         "e_demand":9200,"e_ai":29,"e_alerts":3,"alert_count":2,
         "sales_drawer_open":True,
         "admin_drawer_open":False,
         "live_replay_speed":"Normal",
         "live_rows_released":0,
         "live_rows_added_session":0,
         "live_last_refresh":"--",
         "_sales_df_cache":None,
         "_marketing_df_cache":None,
         "_executive_df_cache":None}
    for k,v in d.items():
        if k not in st.session_state: st.session_state[k] = v

def logout():
    st.query_params.clear()
    keys_to_clear = [k for k in st.session_state.keys()]
    for k in keys_to_clear:
        del st.session_state[k]

def restore_from_query_params():
    """Restore auth session from URL query params - fixes browser back-button logout."""
    if st.session_state.get("authenticated"):
        return
    params = st.query_params
    role = params.get("role", "")
    if role in ROLE_PASSWORDS:
        st.session_state.authenticated    = True
        st.session_state.current_role     = role
        if not st.session_state.get("active_dashboard"):
            st.session_state.active_dashboard = allowed(role)[0]
        if not st.session_state.get("active_tab"):
            st.session_state.active_tab = "Overview"

def reset_filters_to_default():
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=6)
    updates = {
        "date_start": default_start,
        "date_end": today,
        "rp_ds": default_start,
        "rp_de": today,
        "selected_market": "All",
        "rp_mkt": "All",
        "svc_filter": "All Services",
        "rp_svc": "All Services",
        "seg_filter": "All Segments",
        "rp_seg": "All Segments",
        "outcome_filter": "All",
        "rp_out": "All",
        "status_filter": "All Status Codes",
        "rp_status": "All Status Codes",
    }
    for key, value in updates.items():
        st.session_state[key] = value

def _daily_stats(df):
    if df is None or df.empty:
        return {}, datetime.date.today()
    dates = _date_series(df)
    ref_day = _today_reference_date(df)
    out = {}
    for day in sorted(d for d in dates.dropna().unique() if d <= ref_day):
        out[day] = _kpi_stats(df[dates == day])
    return out, ref_day

def _baseline_stats(df):
    if df is None or df.empty:
        return {}, "7-day avg"
    dates = _date_series(df)
    ref_day = _today_reference_date(df)
    if df is not None and not df.empty:
        cache_key = f"_baseline_stats_{id(df)}"
        cached = st.session_state.get(cache_key)
        meta = (len(df), ref_day)
        if cached and cached.get("meta") == meta:
            return cached["stats"], cached["label"]
    yesterday = ref_day - datetime.timedelta(days=1)
    yesterday_df = df[dates == yesterday]
    if not yesterday_df.empty:
        result = (_kpi_stats(yesterday_df), "yesterday")
        st.session_state[cache_key] = {"meta": (len(df), ref_day), "stats": result[0], "label": result[1]}
        return result

    week_mask = (dates < ref_day) & (dates >= ref_day - datetime.timedelta(days=7))
    week_df = df[week_mask]
    if week_df.empty:
        return {}, "7-day avg"
    week_dates = dates[week_mask]
    week = [_kpi_stats(week_df[week_dates == day]) for day in week_dates.dropna().unique()]
    keys = ["rows", "human", "potential", "demos", "engaged", "engagement_rate", "ai_rate", "opportunity", "quality", "active_markets", "risk_alerts"]
    avg = {k: float(np.mean([s.get(k, 0) for s in week])) for k in keys}
    st.session_state[cache_key] = {"meta": (len(df), ref_day), "stats": avg, "label": "7-day avg"}
    return avg, "7-day avg"

def _metric_delta(current, baseline, key, mode="count"):
    base = float(baseline.get(key, 0) or 0) if baseline else 0
    cur = float(current.get(key, 0) or 0)
    if base <= 0:
        return "", ""
    diff = cur - base
    if abs(diff) < 1e-9:
        return "", ""
    cls = "up" if diff > 0 else "down"
    anchor = "▲" if diff > 0 else "▼"
    if mode == "rate":
        return f"{anchor} {diff:+.1f} pts", cls
    pct = diff / base * 100
    return f"{anchor} {pct:+.1f}%", cls

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def render_login():
    # ── SVG ICONS ──
    _ico_mark = """<svg width="34" height="34" viewBox="0 0 44 44" fill="none"><rect width="44" height="44" rx="11" fill="rgba(0,245,212,0.08)" stroke="rgba(0,245,212,0.28)" stroke-width="1"/><path d="M10 22L18 13L26 22L18 31Z" stroke="#00F5D4" stroke-width="1.6" fill="none"/><path d="M18 22L26 13L34 22L26 31Z" stroke="#76FF36" stroke-width="1.6" fill="none" opacity="0.72"/><circle cx="22" cy="22" r="2.5" fill="#00F5D4"/></svg>"""
    _ico_pulse = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="#76FF36" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>"""
    _ico_chart = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><rect x="3" y="12" width="4" height="9" rx="1" stroke="#00F5D4" stroke-width="2"/><rect x="10" y="6" width="4" height="15" rx="1" stroke="#00F5D4" stroke-width="2"/><rect x="17" y="9" width="4" height="12" rx="1" stroke="#00F5D4" stroke-width="2"/></svg>"""
    _ico_shield_sm = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 2L4 5v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V5l-8-3z" stroke="#76FF36" stroke-width="2" stroke-linejoin="round"/><path d="M9 12l2 2 4-4" stroke="#76FF36" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>"""
    _ico_role = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="4" stroke="#76FF36" stroke-width="2"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="#76FF36" stroke-width="2" stroke-linecap="round"/></svg>"""
    _ico_lock = """<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><rect x="3" y="11" width="18" height="11" rx="3" stroke="#76FF36" stroke-width="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="#76FF36" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="16" r="1.5" fill="#76FF36"/></svg>"""
    _ico_lock_sm = """<svg width="13" height="13" viewBox="0 0 24 24" fill="none"><rect x="3" y="11" width="18" height="11" rx="3" stroke="#F87171" stroke-width="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="#F87171" stroke-width="2" stroke-linecap="round"/></svg>"""
    _login_visual_path = _BASE / "Screenshot 2026-05-07 at 03.12.07.png"
    _login_visual_src = ""
    if _login_visual_path.exists():
        _login_visual_src = "data:image/png;base64," + base64.b64encode(_login_visual_path.read_bytes()).decode()

    st.markdown("""
<style>
div.block-container{padding:0!important;max-width:100%!important;}
[data-testid="stApp"]{background:#D7D7D7!important;}
section[data-testid="stMain"]{display:flex;align-items:center;min-height:100vh;}
section[data-testid="stMain"]>div{width:100%;}
[data-testid="stHeader"],[data-testid="stToolbar"],#MainMenu,footer{display:none!important;}
div[data-testid="stHorizontalBlock"]{gap:0!important;}

.login-left{
  height:682px;display:flex;align-items:center;justify-content:flex-end;overflow:hidden;
  background:transparent;
}
.login-left-image{
  height:682px;width:auto;max-width:100%;display:block;object-fit:contain;object-position:right center;
  border-radius:10px 0 0 10px;
}
.login-left-fallback{
  height:100%;display:flex;align-items:center;justify-content:center;padding:52px;
  background:linear-gradient(135deg,#1647D8 0%,#7C6EE6 48%,#2DD4BF 120%);
  color:white;font-size:32px;font-weight:800;line-height:1.16;
}

.login-form-head{
  height:238px;box-sizing:border-box;border-radius:0 10px 0 0;padding:34px 54px 0;
  background:
    linear-gradient(180deg,rgba(13,25,34,.98),rgba(8,17,24,.98))!important;
  border-top:1px solid rgba(0,255,209,.22);
  border-right:1px solid rgba(0,255,209,.16);
  box-shadow:18px 18px 42px rgba(0,0,0,.24);
}
.login-logo-pill{
  display:flex;align-items:center;justify-content:center;padding:0;border-radius:0;
  width:max-content;min-width:0;min-height:0;margin:0 auto 34px;
  background:transparent;color:#F5F7FA;font-size:14px;font-weight:800;
  border:0;
}
.login-title{font-size:30px;font-weight:800;color:#F5F7FA;letter-spacing:0;margin-bottom:10px;}
.login-subtitle{font-size:14px;color:#9AA7B0;line-height:1.45;}

div[data-testid="stForm"]{
  height:444px!important;min-height:444px!important;box-sizing:border-box!important;
  border:none!important;border-radius:0 0 10px 0!important;
  padding:12px 54px 44px!important;
  background:
    linear-gradient(180deg,rgba(8,17,24,.98),rgba(3,7,12,.99))!important;
  border-right:1px solid rgba(0,255,209,.16)!important;
  border-bottom:1px solid rgba(0,255,209,.16)!important;
  box-shadow:18px 24px 42px rgba(0,0,0,.26);
}
div[data-testid="stForm"] div[data-testid="stVerticalBlock"]{
  gap:18px!important;
}
div[data-testid="stForm"] label{
  color:#DDE7EE!important;font-size:13px!important;font-weight:750!important;
  letter-spacing:0!important;text-transform:none!important;margin-bottom:7px!important;
}
div[data-testid="stSelectbox"]>div>div,
div[data-testid="stTextInput"]>div{
  min-height:52px!important;border:1px solid rgba(34,211,238,.18)!important;border-radius:9px!important;
  background:#0B1620!important;color:#F5F7FA!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04)!important;
}
div[data-testid="stSelectbox"]>div>div{
  cursor:pointer!important;display:flex!important;align-items:center!important;
  padding:0 50px 0 18px!important;
  background:linear-gradient(180deg,#10202B 0%,#0B1620 100%)!important;
  position:relative!important;
}
div[data-testid="stSelectbox"]>div>div::after{
  content:"";position:absolute;right:18px;top:50%;width:8px;height:8px;
  border-right:2px solid #22D3EE;border-bottom:2px solid #22D3EE;
  transform:translateY(-65%) rotate(45deg);pointer-events:none;opacity:.9;
}
div[data-testid="stSelectbox"] svg{display:none!important;}
div[data-testid="stSelectbox"] div,
div[data-testid="stSelectbox"] span,
div[data-testid="stTextInput"] input{
  color:#F5F7FA!important;font-size:14px!important;font-weight:600!important;
}
div[data-testid="stSelectbox"] span{
  line-height:52px!important;display:flex!important;align-items:center!important;
}
div[data-testid="stTextInput"] input{
  min-height:50px!important;
  padding:0 18px!important;
  background:#FFFFFF!important;
  color:#0B1620!important;
  -webkit-text-fill-color:#0B1620!important;
}
div[data-testid="stTextInput"] input::placeholder{color:#66727D!important;}
div[data-testid="stSelectbox"]>div>div:focus-within,
div[data-testid="stTextInput"]>div:focus-within{
  border-color:rgba(34,211,238,.44)!important;
  box-shadow:0 0 0 3px rgba(34,211,238,.10), inset 0 1px 0 rgba(255,255,255,.05)!important;
}
div[data-testid="stFormSubmitButton"]>button{
  height:52px!important;margin-top:118px!important;border-radius:9px!important;
  border:1px solid rgba(34,211,238,.30)!important;
  background:linear-gradient(180deg,#101B26 0%,#081018 100%)!important;
  color:#F5F7FA!important;font-size:15px!important;font-weight:800!important;
  box-shadow:0 8px 20px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.08)!important;
}
div[data-testid="stFormSubmitButton"]>button:hover{
  border-color:rgba(0,255,209,.42)!important;
  background:linear-gradient(180deg,#122433 0%,#09141D 100%)!important;
  filter:none!important;transform:none!important;
}
.login-error{
  background:#FEF2F2;border:1px solid #FECACA;color:#B91C1C;border-radius:8px;
  padding:9px 12px;font-size:12px;margin-top:12px;display:flex;gap:8px;align-items:center;
}
@media(max-width:980px){
  .login-left{display:none;}
  .login-form-head{border-radius:10px 10px 0 0;}
  div[data-testid="stForm"]{border-radius:0 0 10px 10px!important;}
  div[data-testid="stForm"],.login-form-head{box-shadow:0 18px 42px rgba(15,23,42,.16);}
}
</style>
""", unsafe_allow_html=True)

    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    _, shell_col, _ = st.columns([0.42, 5.7, 0.42])
    with shell_col:
        left_col, right_col = st.columns([0.82, 1.0], gap=None)
        with left_col:
            _visual = (
                f'<img class="login-left-image" src="{_login_visual_src}" alt="CyberNova dashboard preview"/>'
                if _login_visual_src else
                '<div class="login-left-fallback">CyberNova BI<br/>Made Clear</div>'
            )
            st.markdown(f"""
<div class="login-left">
  {_visual}
</div>
""", unsafe_allow_html=True)
        with right_col:
            _logo = logo_img(h=124) if LOGO_SRC else _ico_mark
            st.markdown(f"""
<div class="login-form-head">
  <div class="login-logo-pill">{_logo}</div>
  <div class="login-title">Login to Your Account</div>
  <div class="login-subtitle">Select your portal role and enter your access password.</div>
  {f'<div class="login-error">{_ico_lock_sm}<span>Invalid password for selected role.</span></div>' if st.session_state.get("login_error") else ''}
</div>
""", unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                role = st.selectbox("Role", list(ROLE_PASSWORDS.keys()))
                pwd = st.text_input("Password", type="password", placeholder="Enter your password")
                sub = st.form_submit_button("Log in", use_container_width=True)
                if sub:
                    if ROLE_PASSWORDS.get(role, "") == pwd:
                        st.session_state.authenticated = True
                        st.session_state.current_role = role
                        st.session_state.active_dashboard = allowed(role)[0]
                        st.session_state.active_tab = "Overview"
                        st.session_state.login_error = False
                        st.query_params["role"] = role
                        st.rerun()
                    else:
                        st.session_state.login_error = True
                        st.rerun()
    return

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
def render_header():
    v    = st.session_state
    dash = v.active_dashboard
    cfg  = DASH_CFG[dash]
    title_html = cfg["title"].replace("CyberNova", '<span class="cn-brand-glow">CyberNova</span>', 1)
    role = v.current_role or ""
    uname, _ = ROLE_META.get(role, ("Alex",""))
    fname = uname.split()[0]
    now   = datetime.datetime.now().strftime("%H:%M")

    hdr_col1, hdr_col2 = st.columns([8, 2])
    with hdr_col1:
        st.markdown(f"""
<div class="app-shell-header">

  <div style="display:flex;align-items:center;gap:14px;">
    {logo_img(h=36)}
    <div>
      <div style="font-size:10px;color:#6B7FA3;margin-bottom:1px;">
        Welcome Back, {fname} &nbsp;/&nbsp;
        <span style="color:#22D3EE;">{now}</span>
        &nbsp;<span style="color:#4ADE80;">Live</span>
      </div>
      <div class="header-dashboard-title" style="color:{cfg['accent']};">
        {title_html}
      </div>
      <div style="font-size:10px;color:#6B7FA3;margin-top:1px;">{cfg['sub']}</div>
    </div>
  </div>

  <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
    <div class="header-chip">
      {dash} View &nbsp;{svg_icon("chevron", 12, "#6B7FA3")}
    </div>
    <div class="header-chip">
      Live data active
    </div>
    <span style="background:rgba(74,222,128,0.1);color:#4ADE80;
      border:1px solid rgba(74,222,128,0.25);border-radius:20px;
      padding:4px 12px;font-size:11px;font-weight:600;">
      Operational
    </span>
  </div>
</div>""", unsafe_allow_html=True)
    with hdr_col2:
        btn_left, btn_right = st.columns(2, gap="small", vertical_alignment="center")
        with btn_left:
            _drawer_label = "Close" if st.session_state.get("admin_drawer_open") else "Filters"
            if st.button(_drawer_label, key="admin_drawer_toggle", use_container_width=True):
                st.session_state.admin_drawer_open = not st.session_state.get("admin_drawer_open", False)
                st.rerun()
        with btn_right:
            if st.button("Logout", key="header_logout", use_container_width=True):
                logout()
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN DRAWER - dashboard switcher + filters
# ═══════════════════════════════════════════════════════════════════════════════
def render_admin_drawer():
    v    = st.session_state
    role = v.current_role or ""
    uname, utitle = ROLE_META.get(role,("User","-"))
    if st.button("Close Filters", key="drawer_close_filters", use_container_width=True):
        st.session_state.admin_drawer_open = False
        st.rerun()

    # ── Profile ──
    st.markdown(f"""
<div style="background:linear-gradient(145deg,rgba(12,24,44,0.92),rgba(8,18,34,0.88));
  border:1px solid rgba(34,211,238,0.12);border-radius:12px;
  padding:12px 14px;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
  <div style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#22D3EE,#14B8A6);
    display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#02070A;flex-shrink:0;">
    {uname[0]}
  </div>
  <div>
    <div style="font-size:12px;font-weight:600;color:#F0F4F8;">{uname}</div>
    <div style="font-size:10px;color:#6B7FA3;">{utitle}</div>
    <div style="font-size:9px;color:#4ADE80;margin-top:1px;">{svg_icon("check", 10, "#4ADE80")} Online</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Dashboard Switcher ──
    st.markdown('<div class="rp-label">Dashboard</div>', unsafe_allow_html=True)
    for d in allowed(role):
        cfg    = DASH_CFG[d]
        active = v.active_dashboard == d
        panel_title = PANEL_DASHBOARD_TITLES.get(d, cfg["title"])
        if active:
            st.markdown(
                f'<div class="rp-active-dashboard" style="--dash-accent:{cfg["accent"]};">'
                f'<span class="rp-active-icon">{cfg["icon"]}</span>'
                f'<span>{panel_title}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            continue
        if st.button(f"{cfg['icon']}  {panel_title}", key=f"rp_dash_{d}", use_container_width=True):
            v.active_dashboard = d
            v.active_tab = "Overview"
            st.rerun()

    st.markdown('<div style="height:1px;background:rgba(34,211,238,0.08);margin:12px 0;"></div>', unsafe_allow_html=True)

    # ── Filters ──
    st.markdown('<div class="rp-label">Global Filters</div>', unsafe_allow_html=True)
    v.date_start = st.date_input("Start Date", v.date_start, key="rp_ds")
    v.date_end   = st.date_input("End Date",   v.date_end,   key="rp_de")

    mkts = ["All","South Africa","Zambia","Mozambique","Botswana","Angola","Zimbabwe","Namibia","Malawi"]
    idx  = mkts.index(v.selected_market) if v.selected_market in mkts else 0
    v.selected_market = st.selectbox("Market", mkts, index=idx, key="rp_mkt")

    svcs = ["All Services","AI Solutions","Cybersecurity","Cloud & Data","Advisory & Training"]
    v.svc_filter = st.selectbox("Service", svcs, key="rp_svc")

    segs = ["All Segments","Enterprise","SMB","Government","Individual"]
    v.seg_filter = st.selectbox("Segment", segs, key="rp_seg")

    outs = ["All","Potential Customer","Demo Request","Engaged","Bounce"]
    v.outcome_filter = st.selectbox("Visit Outcome", outs, key="rp_out")

    status_options = ["All Status Codes", "200", "304", "404", "500"]
    if v.get("status_filter") not in status_options:
        v.status_filter = "All Status Codes"
    v.status_filter = st.selectbox("HTTP Status Code", status_options, key="rp_status")

    c1,c2 = st.columns(2)
    with c1:
        if st.button("Apply", use_container_width=True, key="rp_apply"): st.rerun()
    with c2:
        st.button("Reset", use_container_width=True, key="rp_reset", on_click=reset_filters_to_default)

    st.markdown('<div style="height:1px;background:rgba(34,211,238,0.08);margin:12px 0;"></div>', unsafe_allow_html=True)

    # ── Live Sync ──
    st.markdown(f"""
<div style="background:rgba(9,20,36,0.6);border:1px solid rgba(34,211,238,0.08);
  border-radius:10px;padding:10px 12px;">
  <div style="font-size:9px;color:#3A4A5E;text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px;">Data Intelligence</div>
  <div style="font-size:11px;color:#6B7FA3;margin-bottom:5px;display:flex;align-items:center;gap:7px;">{svg_icon("sync", 13, "#6B7FA3")} Live data active</div>
  <div style="font-size:11px;color:#6B7FA3;margin-bottom:5px;display:flex;align-items:center;gap:7px;">{svg_icon("shield", 13, "#6B7FA3")} 96.4% data quality</div>
  <div style="font-size:11px;color:#F87171;display:flex;align-items:center;gap:7px;">{svg_icon("alert", 13, "#F87171")} {v.alert_count} alert(s) active</div>
</div>""", unsafe_allow_html=True)

    if st.button("Logout", use_container_width=True, key="rp_logout"):
        logout(); st.rerun()

    st.markdown("""
<div style="margin-top:12px;font-size:9px;color:#1E2D3D;text-align:center;padding:0 4px;line-height:1.5;">
  Prototype v1.0  -  Review only  -  Not for production use
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT CHIPS
# ═══════════════════════════════════════════════════════════════════════════════
def render_chips(df):
    v = st.session_state
    noise = int(_truthy_series(df, "is_bot").sum()) if df is not None and "is_bot" in df.columns else 0
    period = f"{v.date_start} to {v.date_end}" if v.get("date_start") and v.get("date_end") else "Selected period"
    quality = _kpi_stats(df)["quality"]
    st.markdown(f"""
<div style="margin-bottom:4px;">
  <span class="chip">Period: {period}</span>
  <span class="chip">Market: {v.selected_market}</span>
  <span class="chip">Service: {v.svc_filter}</span>
  <span class="chip">Segment: {v.seg_filter}</span>
  <span class="chip">Outcome: {v.outcome_filter}</span>
  <span class="chip">Status: {v.get("status_filter", "All Status Codes")}</span>
  <span class="chip">Bot/Crawler Traffic Excluded: {noise:,}</span>
  <span class="chip">Quality: {quality}%</span>
  <span class="chip">Revenue: estimated opportunity, not booked sales</span>
</div>""", unsafe_allow_html=True)

@st.fragment(run_every=LIVE_KPI_FRAGMENT_SECONDS)
def render_live_pulse(compact=False):
    v    = st.session_state
    dash = v.get("active_dashboard","Sales")
    now  = datetime.datetime.now().strftime("%H:%M:%S")
    cache_key = {
        "Sales": "_sales_df_cache",
        "Marketing": "_marketing_df_cache",
        "Executive": "_executive_df_cache",
    }.get(dash, "_sales_df_cache")
    live_today = _live_today_df(v.get(cache_key), f"pulse_{dash.lower()}")
    stats = _kpi_stats(live_today)
    if dash == "Sales":
        items = [("Potential Customers", f"{stats['potential']:,}", "#22D3EE"),
                 ("Demo Requests", f"{stats['demos']:,}", "#14B8A6"),
                 ("Opportunity Value", _fmt_money(stats["opportunity"]), "#4ADE80"),
                 ("Top Market", stats["top_market"], "#FBBF24"),
                 ("Today Rows", f"{len(live_today):,}", "#14B8A6")]
    elif dash == "Marketing":
        items = [("Active Audience", f"{stats['human']:,}", "#22D3EE"),
                 ("Top Market", stats["top_market"], "#FBBF24"),
                 ("Top Service", stats["top_service"], "#14B8A6"),
                 ("Engaged Sessions", f"{stats['engaged']:,}", "#4ADE80"),
                 ("Audience Quality", f"{stats['quality']}%", "#A855F7")]
    else:
        items = [("Strategic Demand", f"{stats['human']:,}", "#22D3EE"),
                 ("Potential Customers", f"{stats['potential']:,}", "#4ADE80"),
                 ("AI Traction", f"{stats['ai_rate']:.1f}%", "#14B8A6"),
                 ("Risk Alerts", str(stats["risk_alerts"]), "#F87171"),
                 ("Active Markets", str(stats["active_markets"]), "#FBBF24")]

    html = "".join(f'<div class="pulse-item"><div class="pl">{l}</div><div class="pv" style="color:{c};">{val}</div></div>'
                   for l,val,c in items)
    pulse_class = "pulse-wrap pulse-wrap-compact" if compact else "pulse-wrap"
    update_html = (
        f'<div class="pulse-updated">Updated {now} &middot; today stream</div>'
        if compact else
        f'<div class="pulse-updated">Updated {now}<br>today stream</div>'
    )
    st.markdown(f"""
<div class="{pulse_class}">
  <div style="display:flex;align-items:center;font-size:9px;font-weight:700;letter-spacing:.14em;
    text-transform:uppercase;color:#3A4A5E;padding-right:16px;border-right:1px solid rgba(34,211,238,0.1);">
    <span class="live-dot"></span>LIVE
  </div>
  {html}
  {update_html}
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SHARED SADC MAP
# ═══════════════════════════════════════════════════════════════════════════════
MAP_NODES = [
    {"city":"Cape Town","country":"South Africa","lat":-33.9,"lon":18.4,"status":"Core Market","customers":450,"demos":98,"conv":"21.8%","revenue":"P18.2M","ai":34,"risk":"Low","action":"Scale outreach","visitors":4200,"eng":"31%","invest":"Invest"},
    {"city":"Durban","country":"South Africa","lat":-29.9,"lon":30.9,"status":"High Growth","customers":112,"demos":28,"conv":"25%","revenue":"P6.1M","ai":28,"risk":"Low","action":"Expand campaign","visitors":1100,"eng":"27%","invest":"Invest"},
    {"city":"Lusaka","country":"Zambia","lat":-15.4,"lon":28.3,"status":"Strategic Hub","customers":180,"demos":41,"conv":"22.8%","revenue":"P9.5M","ai":41,"risk":"Low","action":"Deepen AI push","visitors":1800,"eng":"28%","invest":"Invest"},
    {"city":"Maputo","country":"Mozambique","lat":-25.9,"lon":32.6,"status":"Strategic Hub","customers":140,"demos":29,"conv":"20.7%","revenue":"P7.2M","ai":37,"risk":"Medium","action":"Strengthen brand","visitors":1400,"eng":"25%","invest":"Monitor"},
    {"city":"Gaborone","country":"Botswana","lat":-24.7,"lon":25.9,"status":"Stable","customers":95,"demos":18,"conv":"18.9%","revenue":"P4.8M","ai":22,"risk":"Low","action":"Maintain","visitors":950,"eng":"22%","invest":"Monitor"},
    {"city":"Harare","country":"Zimbabwe","lat":-17.8,"lon":31.0,"status":"High Growth","customers":120,"demos":31,"conv":"25.8%","revenue":"P6.8M","ai":31,"risk":"Medium","action":"Monitor closely","visitors":1100,"eng":"27%","invest":"Monitor"},
    {"city":"Luanda","country":"Angola","lat":-8.8,"lon":13.2,"status":"Emerging","customers":72,"demos":14,"conv":"19.4%","revenue":"P3.1M","ai":18,"risk":"Medium","action":"Pilot campaign","visitors":720,"eng":"24%","invest":"Review"},
    {"city":"Windhoek","country":"Namibia","lat":-22.6,"lon":17.1,"status":"Emerging","customers":55,"demos":11,"conv":"20%","revenue":"P2.3M","ai":15,"risk":"Low","action":"Explore","visitors":550,"eng":"20%","invest":"Review"},
    {"city":"Lilongwe","country":"Malawi","lat":-13.9,"lon":33.8,"status":"Emerging","customers":48,"demos":8,"conv":"16.7%","revenue":"P1.6M","ai":12,"risk":"Low","action":"Seed market","visitors":480,"eng":"18%","invest":"Review"},
]

def _live_map_nodes(df):
    df_m = pd.DataFrame(MAP_NODES)
    if df is None or df.empty or "country" not in df.columns:
        df_m["live_rows"] = 0
        df_m["last_seen"] = "--"
        return df_m

    human = _human_df(df)
    if human.empty:
        df_m["live_rows"] = 0
        df_m["last_seen"] = "--"
        return df_m

    work = human.copy()
    work["_pc_signal"] = _truthy_series(work, "potential_customer_signal").astype(int)
    work["_demo_signal"] = _truthy_series(work, "has_demo_request").astype(int)
    work["_ai_signal"] = _truthy_series(work, "has_ai_interest").astype(int) if "has_ai_interest" in work.columns else (
        work["service_name"].astype(str).str.contains("AI", case=False, na=False).astype(int) if "service_name" in work.columns else 0
    )
    work["_deal_value"] = _num_series(work, "estimated_deal_value")
    work["_engaged"] = _truthy_series(work, "is_engaged_session").astype(int) if "is_engaged_session" in work.columns else (
        _num_series(work, "distinct_pages_session").gt(1).astype(int) if "distinct_pages_session" in work.columns else 0
    )
    if "timestamp" in work.columns:
        work["_ts"] = pd.to_datetime(work["timestamp"], errors="coerce")
    else:
        work["_ts"] = pd.NaT

    agg = work.groupby("country").agg(
        visitors=("country", "size"),
        customers=("_pc_signal", "sum"),
        demos=("_demo_signal", "sum"),
        revenue=("_deal_value", "sum"),
        ai=("_ai_signal", "sum"),
        engaged=("_engaged", "sum"),
        last_seen=("_ts", "max"),
    ).reset_index()

    df_m = df_m.drop(columns=[c for c in ["visitors", "customers", "demos", "revenue", "ai", "eng"] if c in df_m.columns])
    df_m = df_m.merge(agg, on="country", how="left")
    for col in ["visitors", "customers", "demos", "revenue", "ai", "engaged"]:
        df_m[col] = pd.to_numeric(df_m[col], errors="coerce").fillna(0)
    df_m["live_rows"] = df_m["visitors"].astype(int)
    df_m["customers"] = df_m["customers"].astype(int)
    df_m["demos"] = df_m["demos"].astype(int)
    conv_pct = (df_m["demos"] / df_m["customers"].replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
    eng_pct = (df_m["engaged"] / df_m["visitors"].replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
    ai_pct = (df_m["ai"] / df_m["visitors"].replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
    df_m["conv"] = conv_pct.round(1).astype(str) + "%"
    df_m["eng"] = eng_pct.round(1).astype(str) + "%"
    df_m["ai"] = ai_pct.round(0).astype(int)
    df_m["revenue"] = df_m["revenue"].apply(_fmt_money)
    df_m["last_seen"] = pd.to_datetime(df_m["last_seen"], errors="coerce").dt.strftime("%H:%M:%S").fillna("--")
    return df_m

def render_sadc_map(mode="sales", height=400, df=None):
    df_m = _live_map_nodes(df)
    max_customers = max(1, int(df_m["customers"].max()))
    df_m["sz"] = 10 + (df_m["customers"] / max_customers * 46)
    if mode=="sales":
        title,sub = "Potential Customer Hotzones","Static SADC market geography for the selected view"
        hover=[f"<b>{r['city']}, {r['country']}</b><br>Status: {r['status']}<br>Live rows: {int(r['live_rows']):,}<br>Potential Customers: {int(r['customers']):,}<br>Demo Requests: {int(r['demos']):,}<br>Conversion: {r['conv']}<br>Opportunity Value: {r['revenue']}<br>AI Interest: {r['ai']}%<br>Last Signal: {r['last_seen']}<br>Action: {r['action']}" for _,r in df_m.iterrows()]
    elif mode=="marketing":
        title,sub = "Campaign Hotzones","Static SADC market geography for campaign planning"
        hover=[f"<b>{r['city']}, {r['country']}</b><br>Status: {r['status']}<br>Live Visitors: {int(r['visitors']):,}<br>Engagement: {r['eng']}<br>Potential Customers: {int(r['customers']):,}<br>AI Interest: {r['ai']}%<br>Last Signal: {r['last_seen']}<br>Campaign Action: {r['action']}" for _,r in df_m.iterrows()]
    else:
        title,sub = "Regional Expansion Priority Map","Static SADC market geography for leadership review"
        hover=[f"<b>{r['city']}, {r['country']}</b><br>Status: {r['status']}<br>Live Rows: {int(r['live_rows']):,}<br>Potential Customers: {int(r['customers']):,}<br>Opportunity Value: {r['revenue']}<br>AI Interest: {r['ai']}%<br>Last Signal: {r['last_seen']}<br>Recommendation: <b>{r['invest']}</b>" for _,r in df_m.iterrows()]

    fig = go.Figure()
    for status, grp in df_m.groupby("status"):
        col = COLOR_MAP[status]
        fig.add_trace(go.Scattermap(
            lat=grp.lat, lon=grp.lon, mode="markers", name=status,
            marker=dict(
                size=grp["sz"], color=col, opacity=0.9, sizemode="area",
            ),
            text=[hover[df_m.index.get_loc(i)] for i in grp.index],
            hoverinfo="text",
        ))
    fig.update_layout(
        map=dict(style="carto-darkmatter", center=dict(lat=-22, lon=28), zoom=4.2),
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="rgba(7,14,26,0.95)", bordercolor="rgba(34,211,238,0.3)",
                        font=dict(color="#F0F4F8", size=11, family="Inter")),
        legend=dict(bgcolor="rgba(9,20,36,0.9)", bordercolor="rgba(34,211,238,0.2)",
                    borderwidth=1, font=dict(color="#F0F4F8", size=10, family="Inter"),
                    orientation="v", x=0.01, y=0.98),
    )
    st.markdown(f'<div class="cn-card"><div class="sec-label">{title}</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

# ── CHART LAYOUT HELPER ───────────────────────────────────────────────────────
def _compact_regional_opportunity_map(df):
    df_m = _live_map_nodes(df)
    max_customers = max(1, int(df_m["customers"].max()))
    df_m["sz"] = 9 + (df_m["customers"] / max_customers * 34)

    fig = go.Figure(go.Scattergeo(
        lat=df_m["lat"],
        lon=df_m["lon"],
        mode="markers+text",
        marker=dict(size=df_m["sz"], color="#22D3EE", opacity=0.84, line=dict(color="rgba(240,244,248,.45)", width=1)),
        text=df_m["country"].str.replace("South Africa", "SA", regex=False).str.replace("Mozambique", "Moz", regex=False),
        textposition="top center",
        textfont=dict(color="#CBD5E1", size=8, family="Inter"),
        customdata=df_m[["customers", "demos", "revenue", "last_seen"]],
        hovertemplate="<b>%{text}</b><br>Potential customers: %{customdata[0]:,}<br>Demo requests: %{customdata[1]:,}<br>Value: %{customdata[2]}<br>Last signal: %{customdata[3]}<extra></extra>",
        showlegend=False,
    ))
    fig.update_geos(
        scope="africa",
        projection_type="natural earth",
        lataxis_range=[-36, -6],
        lonaxis_range=[10, 37],
        showland=True,
        landcolor="rgba(15,23,42,.92)",
        showocean=True,
        oceancolor="rgba(3,7,18,.90)",
        showcountries=True,
        countrycolor="rgba(34,211,238,.18)",
        coastlinecolor="rgba(34,211,238,.12)",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        height=318,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(
            bgcolor="rgba(7,14,26,0.95)",
            bordercolor="rgba(34,211,238,0.3)",
            font=dict(color="#F0F4F8", size=10, family="Inter"),
        ),
    )

    summary = df_m.sort_values(["customers", "demos"], ascending=False).head(5)
    top = summary.iloc[0] if len(summary) else None
    anchor = f"{top['country']} leads with {int(top['demos']):,} demos" if top is not None else "No live market trend yet"

    with st.container(key="sales_regional_opportunity_map"):
        st.markdown(f"""
<div class="sec-label">Regional Opportunity Map</div>
<div class="trend-anchor">{svg_icon("trend", 11, "#4ADE80")} Trend anchor: {anchor}</div>
<div class="sales-overview-map-note">Live regional follow-up demand. Bubble size reflects potential customers.</div>
""", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def _regional_opportunity_board(df):
    df_m = _live_map_nodes(df)
    work = df_m.copy()
    work["_revenue_num"] = (
        work["revenue"].astype(str)
        .str.replace("P", "", regex=False)
        .str.replace("M", "", regex=False)
        .str.replace("K", "", regex=False)
        .astype(float)
    )
    summary = (
        work.groupby("country", as_index=False)
        .agg(customers=("customers", "sum"), demos=("demos", "sum"), revenue_num=("_revenue_num", "sum"))
        .sort_values(["customers", "demos"], ascending=False)
        .head(5)
    )
    rows = ""
    for _, r in summary.iterrows():
        revenue = f"P{float(r['revenue_num']):.1f}M"
        rows += f"""
<tr>
  <td>{r['country']}</td>
  <td style="text-align:right;">{int(r['customers']):,}</td>
  <td style="text-align:right;">{int(r['demos']):,}</td>
  <td style="text-align:right;">{revenue}</td>
</tr>"""
    st.markdown(f"""
<div class="cn-card sales-overview-contact sales-overview-side-card">
  <div class="sec-label">Top 5 Countries</div>
  <table class="sales-mini-table">
    <thead><tr><th>Country</th><th style="text-align:right;">Customers</th><th style="text-align:right;">Demos</th><th style="text-align:right;">Value</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>""", unsafe_allow_html=True)

def _cl(fig, h=145):
    fig.update_layout(
        height=h,
        margin=dict(l=40, r=12, t=8, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,17,24,0.44)",
        font=dict(color="#CBD5E1", size=11, family="Inter"),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(7,14,26,0.95)",
            bordercolor="rgba(45,212,191,0.28)",
            font=dict(color="#F0F4F8", size=11, family="Inter"),
        ),
        xaxis=dict(
            gridcolor="rgba(148,163,184,0.10)", color="#94A3B8", showgrid=True,
            zeroline=False,
            showspikes=True, spikesnap="cursor",
            spikecolor="rgba(45,212,191,0.22)", spikethickness=1,
            tickfont=dict(size=10, color="#CBD5E1"),
            title_font=dict(size=10, color="#94A3B8"),
            automargin=True,
        ),
        yaxis=dict(
            gridcolor="rgba(148,163,184,0.10)", color="#94A3B8", showgrid=True,
            zeroline=False,
            tickfont=dict(size=10, color="#CBD5E1"),
            title_font=dict(size=10, color="#94A3B8"),
            automargin=True,
        ),
        showlegend=False,
    )
    fig.update_traces(marker_line_width=0, selector=dict(type="bar"))
    fig.update_traces(line=dict(width=2.4), selector=dict(type="scatter"))

def ph(title, icon="chart", note="Coming in next build"):
    st.markdown(
        f'<div class="ph-card">'
        f'<div style="font-size:22px;opacity:.55;color:#8A98A6;">{svg_icon(icon, 22, "currentColor")}</div>'
        f'<div style="font-size:12px;font-weight:600;">{title}</div>'
        f'<div style="font-size:10px;color:#2A3A4E;">{note}</div></div>',
        unsafe_allow_html=True,
    )

def ph_grid(cards, n=3):
    for i in range(0,len(cards),n):
        row=cards[i:i+n]
        cols=st.columns(len(row))
        for col,(t,ic) in zip(cols,row):
            with col: ph(t,ic)

# ═══════════════════════════════════════════════════════════════════════════════
# SALES OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
_GROWTH_FALLBACK = {
    "mo":      ["Jan","Feb","Mar","Apr","May","Jun"],
    "pc_vals": [820, 940, 1050, 1180, 1248, None],
    "dr_vals": [210, 245, 275,  295,  312,  None],
    "target":  [900, 950, 1000, 1100, 1200, 1300],
    "prev":    [760, 820, 940,  1050, 1180, 1248],
}

def _sales_growth(df):
    mo = pc_vals = dr_vals = target = prev = None
    if df is not None and "date" in df.columns and len(df) > 0:
        try:
            df2 = df.copy()
            df2["_month"] = pd.to_datetime(df2["date"], errors="coerce").dt.to_period("M")
            _human = _human_df(df2)
            _grp = _human.groupby("_month")
            if "potential_customer_signal" in df2.columns:
                _human["_pc_signal"] = _truthy_series(_human, "potential_customer_signal").astype(int)
                _pc = _human.groupby("_month")["_pc_signal"].sum().tail(6)
            else:
                _pc = _grp.size().tail(6)
            # Need at least 3 months of data for a meaningful trend - otherwise fall back
            if len(_pc) < 3:
                raise ValueError("Insufficient monthly data")
            if "has_demo_request" in df2.columns:
                _human["_demo_signal"] = _truthy_series(_human, "has_demo_request").astype(int)
                _dr = _human.groupby("_month")["_demo_signal"].sum().reindex(_pc.index, fill_value=0).tail(6)
            else:
                _dr = (_pc * 0.25).astype(int)
            # Format periods as readable short month labels (e.g. "Jan 25")
            mo      = [pd.Period(p).to_timestamp().strftime("%b %y") for p in _pc.index]
            pc_vals = [int(v) for v in _pc.tolist()]
            dr_vals = [int(v) for v in _dr.tolist()]
            target  = [max(v, 900) + 100 * i for i, v in enumerate(pc_vals)]
            prev    = [int(v * 0.88) for v in pc_vals[1:]] + [None] if len(pc_vals) > 1 else list(pc_vals)
        except Exception:
            pass

    if mo is None:
        mo      = _GROWTH_FALLBACK["mo"]
        pc_vals = _GROWTH_FALLBACK["pc_vals"]
        dr_vals = _GROWTH_FALLBACK["dr_vals"]
        target  = _GROWTH_FALLBACK["target"]
        prev    = _GROWTH_FALLBACK["prev"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=mo, y=pc_vals, name="Potential Customers",
        line=dict(color="#22D3EE", width=2.5),
        mode="lines+markers",
        marker=dict(size=7, symbol="circle", color="#22D3EE",
                    line=dict(color="rgba(255,255,255,0.25)", width=1.5)),
        fill="tozeroy", fillcolor="rgba(34,211,238,0.06)",
        hovertemplate="Customers: <b>%{y}</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=mo, y=dr_vals, name="Demo Requests",
        line=dict(color="#4ADE80", width=2),
        mode="lines+markers",
        marker=dict(size=6, symbol="circle", color="#4ADE80",
                    line=dict(color="rgba(255,255,255,0.2)", width=1)),
        fill="tozeroy", fillcolor="rgba(74,222,128,0.04)",
        hovertemplate="Demos: <b>%{y}</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=mo, y=target, name="Target",
        line=dict(color="#A855F7", width=1.5, dash="dash"), mode="lines",
        hovertemplate="Target: <b>%{y}</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=mo, y=prev, name="Prev. Period",
        line=dict(color="#3A4A5E", width=1.5, dash="dot"), mode="lines",
        hovertemplate="Prev: <b>%{y}</b><extra></extra>",
    ))
    _cl(fig, 118)
    fig.update_xaxes(type="category")
    fig.update_layout(yaxis_title="Website visits from target markets")
    st.markdown('<div class="cn-card"><div class="sec-label">Sales Growth / Sessions Trend</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _pipeline_funnel(df):
    if df is not None and len(df) > 0:
        try:
            human = _human_df(df)
            n = len(human)
            awareness = n * 6
            engaged   = n * 2
            qualified = int(_truthy_series(human, "potential_customer_signal").sum()) if "potential_customer_signal" in human.columns else n
            proposal  = int(_truthy_series(human, "has_demo_request").sum()) * 2 if "has_demo_request" in human.columns else max(1, qualified // 2)
            won       = max(1, proposal // 2)
            conv      = round(won / awareness * 100, 1) if awareness > 0 else 2.6
        except Exception:
            awareness, engaged, qualified, proposal, won, conv = 7624, 3210, 1248, 512, 198, 2.6
    else:
        awareness, engaged, qualified, proposal, won, conv = 7624, 3210, 1248, 512, 198, 2.6

    stages = ["Awareness", "Engaged", "Qualified", "Proposal", "Won"]
    counts = [int(awareness), int(engaged), int(qualified), int(proposal), int(won)]
    colors = ["#38BDF8", "#2DD4BF", "#FBBF24", "#F59E0B", "#4ADE80"]
    retained = [100] + [
        round((counts[i] / counts[i - 1] * 100), 1) if counts[i - 1] else 0
        for i in range(1, len(counts))
    ]
    dropoffs = [
        (f"{stages[i - 1]} to {stages[i]}", round(100 - retained[i], 1))
        for i in range(1, len(stages))
    ]
    biggest_drop = max(dropoffs, key=lambda x: x[1]) if dropoffs else ("the funnel", 0)

    fig = go.Figure(go.Funnel(
        y=stages,
        x=counts,
        textinfo="none",
        marker=dict(
            color=colors,
            line=dict(color="rgba(5,12,18,0.80)", width=1.5),
        ),
        connector=dict(line=dict(color="rgba(148,163,184,0.18)", width=1.2)),
        opacity=0.94,
        hovertemplate="<b>%{label}</b><br>Volume: %{value:,}<br>Retained from previous: %{percentPrevious:.1%}<extra></extra>",
    ))
    fig.update_layout(
        height=128,
        margin=dict(l=70, r=10, t=4, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#6B7FA3", size=10, family="Inter"),
        hoverlabel=dict(bgcolor="rgba(7,14,26,0.95)", bordercolor="rgba(34,211,238,0.3)",
                        font=dict(color="#F0F4F8", size=11, family="Inter")),
        funnelmode="stack",
        showlegend=False,
        yaxis=dict(tickfont=dict(color="#CBD5E1", size=11, family="Inter")),
    )
    st.markdown(f'<div class="cn-card pipeline-card"><div class="sec-label">Pipeline Health</div><div style="font-size:10px;color:#6B7FA3;margin-bottom:4px;">Conversion: <b style="color:#4ADE80;">{conv}%</b> | Won: <b style="color:#4ADE80;">{won:,}</b></div><div class="kpi-hover-insight">Biggest drop-off is between {biggest_drop[0]} ({biggest_drop[1]}%). Focus follow-up here first.</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _service_donut(df):
    if df is not None and "service_name" in df.columns and "estimated_deal_value" in df.columns and len(df) > 0:
        try:
            human = _human_df(df)
            human["_deal_value_num"] = _num_series(human, "estimated_deal_value")
            rev = human.groupby("service_name")["_deal_value_num"].sum().sort_values(ascending=False).head(6)
            total = rev.sum()
            labels = rev.index.tolist()
            values = (rev / 1e6).round(2).values.tolist()
            total_str = f"P{total/1e6:.1f}M"
        except Exception:
            labels = ["AI Solutions","Cybersecurity","Cloud & Data","Advisory & Training","Other"]
            values = [31.4, 20.7, 16.5, 8.3, 5.7]
            total_str = "P82.6M"
    else:
        labels = ["AI Solutions","Cybersecurity","Cloud & Data","Advisory & Training","Other"]
        values = [31.4, 20.7, 16.5, 8.3, 5.7]
        total_str = "P82.6M"

    total_value = float(sum(values) or 1)
    top_label = labels[0] if labels else "Top service"
    top_share = round(values[0] / total_value * 100, 1) if values else 0
    palette = ["#38BDF8", "#2DD4BF", "#FBBF24", "#F59E0B", "#7C6EE6", "#64748B"]
    pull_vals = [0.035] + [0] * (len(labels) - 1)
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.64,
        pull=pull_vals,
        marker=dict(
            colors=palette[:len(labels)],
            line=dict(color="rgba(7,14,26,0.92)", width=2),
        ),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>Value: P%{value:.1f}M<br>Share: %{percent}<extra></extra>",
        direction="clockwise",
        sort=True,
    ))
    fig.add_annotation(text=f"<b>{total_str}</b>", x=0.5, y=0.58,
                       font=dict(size=18, color="#F8FAFC", family="Inter"), showarrow=False)
    fig.add_annotation(text="estimated value", x=0.5, y=0.43,
                       font=dict(size=9, color="#6B7FA3", family="Inter"), showarrow=False)
    fig.update_layout(
        height=118,
        margin=dict(l=0, r=0, t=6, b=6),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hoverlabel=dict(bgcolor="rgba(7,14,26,0.95)", bordercolor="rgba(34,211,238,0.3)",
                        font=dict(color="#F0F4F8", size=11, family="Inter")),
    )
    st.markdown(f'<div class="cn-card"><div class="sec-label">Services Customers Are Interested In</div><div style="font-size:10px;color:#6B7FA3;margin-bottom:4px;">Based on filtered lead activity. Top: <b style="color:#38BDF8;">{top_label}</b> | Share: <b style="color:#2DD4BF;">{top_share}%</b></div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _live_country_leaderboard(df):
    """Data-driven country leaderboard table from filtered df."""
    _ISO = {"South Africa":"za","Zambia":"zm","Mozambique":"mz","Botswana":"bw",
            "Angola":"ao","Zimbabwe":"zw","Namibia":"na","Malawi":"mw",
            "Democratic Republic of the Congo":"cd"}

    countries = ["South Africa","Zambia","Mozambique","Botswana"]

    # Pre-compute total for % share
    if df is not None and "is_bot" in df.columns and "potential_customer_signal" in df.columns:
        _total_human = _human_df(df)
        total_cust = int(_truthy_series(_total_human, "potential_customer_signal").sum())
        if total_cust == 0:
            total_cust = max(1, len(_total_human))
    elif df is not None:
        total_cust = max(1, len(df))
    else:
        total_cust = 1

    rows_data = []
    for c in countries:
        if df is not None and "country" in df.columns:
            cdf = df[df["country"] == c]
            human = _human_df(cdf)
            cust = int(_truthy_series(human, "potential_customer_signal").sum()) if ("potential_customer_signal" in human.columns and len(human) > 0) else len(human)
            if "estimated_deal_value" in human.columns and len(human) > 0:
                rev_val = _num_series(human, "estimated_deal_value").sum() / 1e6
                rev_s = f"P{rev_val:.1f}M"
            else:
                rev_s = f"P{cust * 0.066:.1f}M"
        else:
            _mock = {"South Africa":(450,"P18.2M"),"Zambia":(180,"P9.5M"),"Mozambique":(140,"P7.2M"),
                     "Botswana":(95,"P4.8M"),"Angola":(72,"P3.1M"),"Namibia":(55,"P2.3M"),
                     "Zimbabwe":(88,"P4.2M"),"Malawi":(42,"P1.6M")}
            v = _mock.get(c, (0,"P0.0M"))
            cust, rev_s = v[0], v[1]

        iso  = _ISO.get(c, "za")
        flag = f'<img src="https://flagcdn.com/20x15/{iso}.png" alt="{c}" style="height:13px;width:auto;border-radius:1px;margin-right:6px;vertical-align:middle;" />'
        trend     = "+" if cust > 50 else "▼"
        trend_col = "#76FF36" if trend == "+" else "#F87171"
        rows_data.append((flag, c, cust, rev_s, trend, trend_col))

    # Sort by customer count descending
    rows_data.sort(key=lambda x: x[2], reverse=True)

    rows_html = ""
    for flag, name, cust, rev, trend, tcol in rows_data:
        rows_html += f"""
<tr>
  <td class="regional-market">{flag}<span>{name}</span></td>
  <td class="regional-value live-count">{cust:,}</td>
  <td class="regional-muted live-count">{rev}</td>
  <td class="regional-trend" style="color:{tcol};">{trend}</td>
</tr>"""

    st.markdown(f"""
<div class="cn-card regional-live-card sales-overview-contact">
  <div class="sec-label">Regional Live Leaderboard</div>
  <table class="regional-table">
    <thead>
      <tr>
        <th style="text-align:left;">Country</th>
        <th style="text-align:right;">Customers</th>
        <th style="text-align:right;">Value</th>
        <th style="text-align:center;">Trend</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>""", unsafe_allow_html=True)

def _warm_leads_breakdown(df):
    human = _human_df(df)
    uri = human["uri"].astype(str).str.lower() if "uri" in human.columns else pd.Series("", index=human.index)
    demo = human[uri.str.contains("/scheduledemo.php", na=False)]
    event = human[uri.str.contains("/event.php", na=False)]

    def _row(label, subdf, color):
        count = len(subdf)
        top_country = _top_value(subdf, "country", "--") if count else "--"
        top_service = _top_value(subdf, "service_name", "--") if count else "--"
        value = _fmt_money(_num_series(subdf, "estimated_deal_value").sum()) if count else "P0"
        return f"""
<tr>
  <td><b style="color:{color};">{label}</b></td>
  <td style="text-align:right;">{count:,}</td>
  <td>{top_country}</td>
  <td>{top_service}</td>
  <td style="text-align:right;">{value}</td>
</tr>"""

    st.markdown(f"""
<div class="cn-card sales-overview-contact">
  <div class="sec-label">Warm Leads Breakdown</div>
  <table class="sales-mini-table">
    <thead><tr><th>Lead type</th><th style="text-align:right;">Count</th><th>Country</th><th>Service interest</th><th style="text-align:right;">Value</th></tr></thead>
    <tbody>
      {_row("Demo Requests", demo, "#4ADE80")}
      {_row("Event Signups", event, "#FBBF24")}
    </tbody>
  </table>
</div>""", unsafe_allow_html=True)

def _sales_action_panel(df):
    human = _human_df(df)
    stats = _kpi_stats(human)
    top_market = stats.get("top_market", "--")
    top_service = stats.get("top_service", "--")
    demo_count = int(_truthy_series(human, "has_demo_request").sum()) if "has_demo_request" in human.columns else 0
    recommendations = [
        f"Call <b>{demo_count:,}</b> demo request leads first.",
        f"<b>{top_market}</b> has the strongest opportunity in this filtered view.",
        f"Lead with <b>{top_service}</b>; it is the strongest current service interest.",
        "Check event signups after demo requests; they are next-best follow-up signals.",
    ]
    st.markdown(f"""
<div class="cn-card sales-action-panel">
  <div class="sec-label">What To Do Next</div>
  {''.join(f'<div class="action-line">{svg_icon("check", 13, "#4ADE80")} {item}</div>' for item in recommendations)}
</div>""", unsafe_allow_html=True)

def _sales_next_action(df):
    human = _human_df(df)
    stats = _kpi_stats(human)
    demo_count = int(_truthy_series(human, "has_demo_request").sum()) if "has_demo_request" in human.columns else 0
    top_market = stats.get("top_market", "the top market")
    top_service = stats.get("top_service", "the strongest service")
    st.markdown(
        f'<div class="sales-next-action">What To Do Next: <b>Call demo request leads first</b> '
        f'({demo_count:,} waiting), then focus {top_market} with {top_service} as the first pitch.</div>',
        unsafe_allow_html=True,
    )

def _sales_insights_under_trend(df):
    human = _human_df(df)
    stats = _kpi_stats(human)
    demo_count = int(_truthy_series(human, "has_demo_request").sum()) if "has_demo_request" in human.columns else 0
    event_count = int(_truthy_series(human, "has_event_signup").sum()) if "has_event_signup" in human.columns else 0
    st.markdown(f"""
<div class="sales-insights-list">
  <div>{svg_icon("check", 12, "#4ADE80")} Demo queue: <b>{demo_count:,}</b> leads should be handled before general browsing traffic.</div>
  <div>{svg_icon("map", 12, "#22D3EE")} Market focus: <b>{stats.get("top_market", "--")}</b> is currently the strongest filtered region.</div>
  <div>{svg_icon("target", 12, "#FBBF24")} Event signups: <b>{event_count:,}</b> are second-priority follow-up signals.</div>
</div>""", unsafe_allow_html=True)

def _sales_srs_evidence_panels(df):
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-label" style="margin-top:4px;">SRS Evidence Checks</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap="small")
    with c1:
        processed = len(df) if df is not None else 0
        bot_count = int(_truthy_series(df, "is_bot").sum()) if df is not None and "is_bot" in df.columns else 0
        dropped = int(_truthy_series(df, "invalid_status_flag").sum()) if df is not None and "invalid_status_flag" in df.columns else 0
        clean = max(0, processed - dropped)
        quality = round(float(pd.to_numeric(df["data_quality_score"], errors="coerce").mean()), 1) if df is not None and "data_quality_score" in df.columns and len(df) else _kpi_stats(df)["quality"]
        st.markdown(f"""
<div class="cn-card">
  <div class="sec-label">ETL Quality Panel</div>
  <table class="sales-mini-table">
    <tbody>
      <tr><td>Records processed</td><td style="text-align:right;">{processed:,}</td></tr>
      <tr><td>Records cleaned</td><td style="text-align:right;">{clean:,}</td></tr>
      <tr><td>Records dropped / excluded</td><td style="text-align:right;">{dropped:,}</td></tr>
      <tr><td>Bot/Crawler Traffic Excluded</td><td style="text-align:right;">{bot_count:,}</td></tr>
      <tr><td>Data quality percentage</td><td style="text-align:right;">{quality}%</td></tr>
    </tbody>
  </table>
</div>""", unsafe_allow_html=True)
    with c2:
        if df is None or df.empty or not {"country", "segment"}.issubset(df.columns):
            st.markdown('<div class="cn-card"><div class="sec-label">Country By Segment</div><div style="font-size:11px;color:#6B7FA3;">Country and segment fields are not available in this filtered view.</div></div>', unsafe_allow_html=True)
        else:
            pivot = pd.crosstab(df["country"], df["segment"]).reset_index().head(10)
            st.markdown('<div class="cn-card"><div class="sec-label">Country By Segment</div>', unsafe_allow_html=True)
            st.dataframe(pivot, use_container_width=True, hide_index=True, height=220)
            st.markdown('</div>', unsafe_allow_html=True)

    if df is None or df.empty or not {"country", "service_name"}.issubset(df.columns):
        st.info("Descriptive statistics are unavailable because country or service fields are missing.")
        return
    stat_col = "estimated_deal_value" if "estimated_deal_value" in df.columns else "response_time_ms" if "response_time_ms" in df.columns else None
    if stat_col is None:
        st.info("Descriptive statistics are unavailable because no numeric value column was found.")
        return
    desc = df.copy()
    desc["_stat_value"] = pd.to_numeric(desc[stat_col], errors="coerce")
    stats_tbl = (
        desc.groupby(["country", "service_name"])["_stat_value"]
        .agg(mean="mean", median="median", std="std", count="count")
        .reset_index()
        .sort_values("count", ascending=False)
        .head(12)
    )
    for col in ["mean", "median", "std"]:
        stats_tbl[col] = stats_tbl[col].round(2)
    with st.expander("Descriptive Statistics by Country and Service", expanded=False):
        st.dataframe(stats_tbl, use_container_width=True, hide_index=True)

def _sales_kpis(df):
    # Derive all values from today's live stream; filters do not apply to KPI cards.
    human_df = _human_df(df)
    stats = _kpi_stats(df)
    baseline, baseline_label = _baseline_stats(st.session_state.get("_sales_df_cache"))

    pot_cust = int(_truthy_series(human_df, "potential_customer_signal").sum()) if len(human_df) > 0 else 0
    demo_req = int(_truthy_series(human_df, "has_demo_request").sum()) if len(human_df) > 0 else 0
    pot_rev_m = round(_num_series(human_df, "estimated_deal_value").sum() / 1e6, 1) if len(human_df) > 0 else 0.0
    if "country" in human_df.columns and len(human_df) > 0:
        vc = human_df["country"].value_counts()
        top_market = vc.index[0] if len(vc) > 0 else "South Africa"
        top_pct = int(vc.iloc[0] / len(human_df) * 100) if len(vc) > 0 else 36
    else:
        top_market, top_pct = "South Africa", 36

    iso_map = {"South Africa":"za","Zambia":"zm","Mozambique":"mz","Botswana":"bw",
               "Angola":"ao","Zimbabwe":"zw","Namibia":"na","Malawi":"mw",
               "Democratic Republic of the Congo":"cd"}
    iso = iso_map.get(top_market, "za")
    flag_img = f'<img src="https://flagcdn.com/20x15/{iso}.png" alt="{top_market}" style="height:16px;width:auto;border-radius:2px;margin-right:5px;vertical-align:middle;" />'

    target_m = 95
    pipeline_pct = min(99, int(pot_rev_m / target_m * 100)) if pot_rev_m else 0
    base_pipeline = min(99, int(float(baseline.get("opportunity", 0) or 0) / 1e6 / target_m * 100)) if baseline else 0
    pipeline_delta, pipeline_cls = _metric_delta({"pipeline": pipeline_pct}, {"pipeline": base_pipeline}, "pipeline", "rate")
    potential_delta, potential_cls = _metric_delta(stats, baseline, "potential")
    demo_delta, demo_cls = _metric_delta(stats, baseline, "demos")
    opp_delta, opp_cls = _metric_delta(stats, baseline, "opportunity")

    kpis = [
        ("People Waiting for a Demo", f"{demo_req:,}", "Follow these up first", demo_delta, demo_cls, "anchor", "Immediate action queue: schedule calls before reviewing lower-intent activity."),
        ("Potential Customers Today", f"{pot_cust:,}", "Showed strong buying signals", potential_delta, potential_cls, "", "Filtered visitors with stronger buying behaviour than general browsing."),
        ("Sales Progress This Month", f"{pipeline_pct}%", f"P{pot_rev_m}M of P{target_m}M target", pipeline_delta, pipeline_cls, "", "Estimated progress against the monthly opportunity target."),
        ("Estimated Revenue if Leads Convert", f"P{pot_rev_m}M", "Estimated value, not booked sales", opp_delta, opp_cls, "", "Potential value if current filtered leads move through the funnel."),
        ("Hottest Market Right Now", f"{flag_img}{top_market}", f"{top_pct}% contribution", "", "", "", "Best region for immediate follow-up under the active filters."),
    ]
    cols = st.columns(5, gap="small")
    cls_map = {"up":"delta-up","watch":"delta-watch","down":"delta-down"}
    for col, (lbl, val, sub, chg, cls, extra, insight) in zip(cols, kpis):
        with col:
            delta = f'<div class="kpi-delta {cls_map.get(cls,"")}">{chg}</div>' if chg else '<div style="height:20px;"></div>'
            anchor_style = "border-color:rgba(74,222,128,0.55);box-shadow:0 0 24px rgba(74,222,128,0.16), inset 0 1px 0 rgba(255,255,255,0.04);" if extra == "anchor" else ""
            st.markdown(f'<div class="kpi-card" style="{anchor_style};min-height:78px;display:flex;flex-direction:column;justify-content:space-between;"><div class="kpi-label">{lbl}</div><div class="kpi-value live-count">{val}</div>{delta}<div class="kpi-sub">{sub}</div><div class="kpi-hover-insight">{insight}</div></div>', unsafe_allow_html=True)

def render_sales_overview(df):
    st.session_state["_sales_df_cache"] = st.session_state.get("_live_replay_df") if st.session_state.get("_live_replay_df") is not None else st.session_state.get("_live_unfiltered_df", df)

    # ── Row 1: KPI cards ──
    try:
        @st.fragment(run_every=LIVE_KPI_FRAGMENT_SECONDS)
        def _live_sales_kpis():
            _df = _refresh_live_replay_cache()
            if _df is not None and not _df.empty:
                st.session_state["_sales_df_cache"] = _df
            else:
                _df = st.session_state.get("_sales_df_cache")
            if _df is not None:
                _live_today = _live_today_df(_df, "sales_kpi_cards")
                _sales_kpis(_live_today)
        _live_sales_kpis()
    except Exception:
        _sales_kpis(df)
    st.markdown('<div style="height:1px;background:linear-gradient(90deg,rgba(34,211,238,0.18),rgba(34,211,238,0.06),transparent);margin:8px 0;"></div>', unsafe_allow_html=True)
    _sales_next_action(df)

    # ── Row 2: Map (left 55%) | 2×2 chart grid (right 45%) ──
    st.markdown('<div class="sales-overview-safe">', unsafe_allow_html=True)
    col_map, col_board_trend, col_other = st.columns([1.1, 0.9, 1.0], gap="small")
    with col_map:
        try:
            @st.fragment(run_every=LIVE_CHART_FRAGMENT_SECONDS)
            def _live_sales_mini_map():
                _df = _refresh_live_replay_cache()
                if _df is None or _df.empty:
                    _df = st.session_state.get("_sales_df_cache")
                _compact_regional_opportunity_map(_live_today_df(_df, "sales_regional_mini_map"))
            _live_sales_mini_map()
        except Exception:
            _compact_regional_opportunity_map(df)
    with col_board_trend:
        try:
            @st.fragment(run_every=LIVE_CHART_FRAGMENT_SECONDS)
            def _live_regional_board():
                _df = _refresh_live_replay_cache()
                if _df is None or _df.empty:
                    _df = st.session_state.get("_sales_df_cache")
                _regional_opportunity_board(_live_today_df(_df, "sales_regional_board"))
            _live_regional_board()
        except Exception:
            _regional_opportunity_board(df)
        _sales_growth(df)
    with col_other:
        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
        _pipeline_funnel(df)
        _service_donut(df)
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MARKETING OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
def _opportunity_matrix():
    countries=["South Africa","Zambia","Mozambique","Botswana","Angola","Zimbabwe","Namibia","Malawi"]
    fig=go.Figure(go.Scatter(x=[4200,1800,1400,950,720,1100,550,480],y=[31,28,25,22,24,27,20,18],
        mode="markers+text",text=countries,textposition="top center",
        textfont=dict(color="#F0F4F8",size=9),
        marker=dict(size=[450/5,180/5,140/5,95/5,72/5,120/5,55/5,48/5],
                    color=["#22D3EE","#14B8A6","#14B8A6","#8A98A6","#4ADE80","#FBBF24","#4ADE80","#4ADE80"],opacity=0.8),
        hovertemplate="<b>%{text}</b><br>Visitors: %{x:,}<br>Engagement: %{y}%<extra></extra>"))
    _cl(fig,145); fig.update_layout(xaxis_title="Visitors",yaxis_title="Engagement %")
    st.markdown('<div class="cn-card"><div class="sec-label">Market Opportunity Matrix</div><div style="font-size:9px;color:#6B7FA3;margin-bottom:6px;">Bubble size = Potential Customers</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _marketing_entry_page(df):
    human = _human_df(df)
    for col in ["landing_page", "entry_page", "page_title", "path", "url_path", "service_name"]:
        value = _top_value(human, col, "")
        if value:
            return value
    return "General Website"

def _marketing_country_summary(df):
    human = _human_df(df)
    if human.empty or "country" not in human.columns:
        return pd.DataFrame(
            [("Botswana", 59, 55.7, 18), ("South Africa", 48, 51.2, 15), ("Zambia", 34, 44.8, 9), ("Zimbabwe", 28, 42.5, 8), ("Mozambique", 22, 38.4, 6)],
            columns=["country", "visitors", "engagement_rate", "opportunity"],
        )
    work = human.copy()
    work["_engaged"] = _truthy_series(work, "is_engaged_session")
    work["_potential"] = _truthy_series(work, "potential_customer_signal")
    work["_demo"] = _truthy_series(work, "has_demo_request")
    summary = work.groupby("country").agg(
        visitors=("country", "size"),
        engaged=("_engaged", "sum"),
        potential=("_potential", "sum"),
        demos=("_demo", "sum"),
    ).reset_index()
    summary["engagement_rate"] = (summary["engaged"] / summary["visitors"].replace(0, np.nan) * 100).fillna(0)
    summary["opportunity"] = (summary["potential"] * 2 + summary["demos"] * 4 + summary["engaged"] * 0.35).round(1)
    return summary.sort_values(["opportunity", "engagement_rate", "visitors"], ascending=False).head(5)

def _marketing_action_label(row):
    engagement = float(row.get("engagement_rate", 0) or 0)
    opportunity = float(row.get("opportunity", 0) or 0)
    if engagement >= 45 or opportunity >= 15:
        return "Prioritise"
    if engagement >= 30:
        return "Maintain"
    if opportunity >= 5:
        return "Watch"
    return "Low priority"

def _market_priority_table(df):
    summary = _marketing_country_summary(df)
    rows = ""
    for _, row in summary.iterrows():
        rows += (
            f'<tr><td><b>{row["country"]}</b></td><td>{int(row["visitors"]):,}</td>'
            f'<td>{float(row["engagement_rate"]):.1f}%</td><td>{float(row["opportunity"]):.0f}</td>'
            f'<td><span style="color:#14B8A6;font-weight:800;">{_marketing_action_label(row)}</span></td></tr>'
        )
    body = rows or '<tr><td colspan="5">No country data is available for this filtered view.</td></tr>'
    st.markdown(f"""
<div class="cn-card">
  <div class="sec-label">Market Priority Table</div>
  <table class="mkt-mini-table">
    <thead><tr><th>Country</th><th>Visitors</th><th>Engagement Rate</th><th>Opportunity</th><th>Recommended Action</th></tr></thead>
    <tbody>{body}</tbody>
  </table>
</div>""", unsafe_allow_html=True)

def _visitors_vs_engagement(df):
    summary = _marketing_country_summary(df).sort_values("visitors", ascending=True)
    if summary.empty:
        st.markdown('<div class="cn-card"><div class="sec-label">Visitors vs Engagement by Market</div><div class="mkt-callout-sub">No country data is available for this filtered view.</div></div>', unsafe_allow_html=True)
        return
    fig = go.Figure()
    fig.add_trace(go.Bar(y=summary["country"], x=summary["visitors"], orientation="h", name="Visitors", marker_color="rgba(20,184,166,.72)", hovertemplate="<b>%{y}</b><br>Visitors: %{x:,}<extra></extra>"))
    fig.add_trace(go.Scatter(y=summary["country"], x=summary["engagement_rate"], mode="markers+lines", name="Engagement rate %", xaxis="x2", marker=dict(size=9, color="#FBBF24"), line=dict(color="#FBBF24", width=2), hovertemplate="<b>%{y}</b><br>Engagement: %{x:.1f}%<extra></extra>"))
    _cl(fig, 158)
    fig.update_layout(
        margin=dict(l=82, r=38, t=16, b=42),
        xaxis=dict(title="Visitors", automargin=True),
        xaxis2=dict(title="Engagement %", overlaying="x", side="top", range=[0, max(60, float(summary["engagement_rate"].max()) + 10)], color="#FBBF24", automargin=True),
        yaxis=dict(automargin=True),
        legend=dict(orientation="h", y=-0.34, x=0),
    )
    st.markdown('<div class="cn-card"><div class="sec-label">Visitors vs Engagement by Market</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _promo_gap():
    svcs=["AI Solutions","Cybersecurity","Cloud & Data","Advisory","Other"]
    fig=go.Figure()
    fig.add_trace(go.Bar(x=svcs,y=[35,28,22,10,5],name="Visit Share %",marker_color="#3A4A5E",hovertemplate="<b>%{x}</b><br>Visit Share: %{y}%<extra></extra>"))
    fig.add_trace(go.Bar(x=svcs,y=[42,24,18,12,4],name="Conversion Share %",marker_color="#22D3EE",hovertemplate="<b>%{x}</b><br>Conversion: %{y}%<extra></extra>"))
    _cl(fig,158)
    fig.update_layout(
        barmode="group", bargap=0.24,
        margin=dict(l=38, r=14, t=16, b=46),
        xaxis=dict(tickangle=0, tickfont=dict(size=9), automargin=True),
        yaxis=dict(title="Share %", automargin=True),
    )
    st.markdown('<div class="cn-card"><div class="sec-label">Service Promotion Gap</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _content_funnel(df=None):
    human = _human_df(df)
    total = len(human)
    landing = total if total else 8500
    service = int((_num_series(human, "distinct_pages_session") >= 2).sum()) if total and "distinct_pages_session" in human.columns else int(landing * 0.45)
    ai_contact = int((_truthy_series(human, "has_ai_interest") | _truthy_series(human, "potential_customer_signal")).sum()) if total else int(service * 0.43)
    demo_event = int((_truthy_series(human, "has_demo_request") | _truthy_series(human, "has_event_signup")).sum()) if total else int(ai_contact * 0.32)
    labels = ["Landing Page", "Service Page", "AI/Contact Interest", "Demo/Event Action"]
    vals = [landing, min(service, landing), min(ai_contact, service), min(demo_event, ai_contact)]
    drops = [0 if a <= 0 else max(0, (a - b) / a * 100) for a, b in zip(vals, vals[1:])]
    largest_idx = int(np.argmax(drops)) if drops else 0
    largest = f"{labels[largest_idx]} to {labels[largest_idx + 1]}" if len(labels) > largest_idx + 1 else "No strong drop-off"
    fig=go.Figure(go.Funnel(y=labels,x=vals,
        textinfo="none",
        marker=dict(color=["#38BDF8","#2DD4BF","#7C6EE6","#4ADE80"],line=dict(color="rgba(5,12,18,0.78)",width=1.5)),
        hovertemplate="<b>%{y}</b><br>%{x:,}<br>%{percentInitial:.1%}<extra></extra>"))
    fig.update_layout(height=154,margin=dict(l=106,r=12,t=4,b=4),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#CBD5E1",size=10),yaxis=dict(tickfont=dict(color="#CBD5E1",size=9),automargin=True))
    st.markdown('<div class="cn-card"><div class="sec-label">Content Journey Funnel</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _activity_heatmap():
    np.random.seed(7)
    z=np.random.randint(10,180,(7,24)); z[1:5,8:18]+=100
    fig=go.Figure(go.Heatmap(z=z,x=[f"{h:02d}:00" for h in range(24)],y=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
        colorscale=[[0,"rgba(15,23,42,0.85)"],[0.45,"rgba(45,212,191,0.34)"],[1,"#38BDF8"]],
        xgap=1, ygap=1,
        hovertemplate="<b>%{y} %{x}</b><br>Activity: %{z}<extra></extra>",showscale=False))
    fig.update_layout(height=145,margin=dict(l=42,r=12,t=8,b=44),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(8,17,24,0.44)",font=dict(color="#CBD5E1",size=10),xaxis=dict(tickangle=-45,color="#CBD5E1",tickfont=dict(size=9),automargin=True),yaxis=dict(color="#CBD5E1",tickfont=dict(size=10),automargin=True))
    st.markdown('<div class="cn-card"><div class="sec-label">Human Activity Timing</div><div style="font-size:9px;color:#6B7FA3;margin-bottom:6px;">Best: Tue–Thu, 09:00–17:00</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _best_time_campaigns(df=None):
    human = _human_df(df)
    window = "Tue-Thu, 09:00-17:00"
    if not human.empty and "timestamp" in human.columns:
        ts = pd.to_datetime(human["timestamp"], errors="coerce")
        if ts.notna().any():
            work = human.loc[ts.notna()].copy()
            work["_dow"] = ts.loc[ts.notna()].dt.day_name().str.slice(0, 3)
            work["_hour"] = ts.loc[ts.notna()].dt.hour
            if not work.empty:
                hour = int(work["_hour"].mode().iloc[0])
                day = str(work["_dow"].mode().iloc[0])
                window = f"{day}, {hour:02d}:00-{min(23, hour + 3):02d}:00"
    st.markdown(f"""
<div class="cn-card">
  <div class="sec-label">Best Time to Run Campaigns</div>
  <div class="mkt-callout-main">Best campaign window: {window}</div>
</div>""", unsafe_allow_html=True)

def _campaign_insight(df):
    human = _human_df(df)
    if human.empty:
        text = "Campaign activity is being monitored. No strong recommendation available yet."
    else:
        stats = _kpi_stats(human)
        top_market = stats.get("top_market") or "the top market"
        entry_page = _marketing_entry_page(human)
        text = f"{top_market} has the strongest engagement right now - prioritise campaigns there."
        if "service_name" in human.columns and len(human):
            work = human.copy()
            work["_action"] = _truthy_series(work, "potential_customer_signal") | _truthy_series(work, "has_demo_request")
            svc = work.groupby("service_name").agg(visits=("service_name", "size"), actions=("_action", "sum")).reset_index()
            svc["action_rate"] = (svc["actions"] / svc["visits"].replace(0, np.nan) * 100).fillna(0)
            svc["visit_share"] = (svc["visits"] / max(1, len(work)) * 100).fillna(0)
            candidates = svc[(svc["action_rate"] >= svc["action_rate"].median()) & (svc["visit_share"] <= svc["visit_share"].median())]
            if not candidates.empty:
                row = candidates.sort_values(["action_rate", "actions"], ascending=False).iloc[0]
                text = f"{row['service_name']} is converting well but has lower visit share - promote it more this week."
            elif entry_page != "--":
                text = f"Most visitors enter through {entry_page} - guide them faster to service pages."
    st.markdown(f'<div class="mkt-insight-action"><div class="title">Campaign Insight</div><div class="text">{text}</div></div>', unsafe_allow_html=True)

def _recommended_campaign_actions(df):
    stats = _kpi_stats(_human_df(df))
    top_market = stats.get("top_market", "the strongest market")
    top_service = stats.get("top_service", "the strongest service")
    actions = [
        f"Prioritise {top_market} campaigns.",
        f"Promote {top_service} more this week.",
        "Improve service-page calls to action.",
    ]
    rows = "".join(f'<div class="mkt-action-line">{svg_icon("check", 13, "#4ADE80")}<span>{action}</span></div>' for action in actions)
    st.markdown(f'<div class="cn-card"><div class="sec-label">Recommended Campaign Actions</div><div class="mkt-action-list">{rows}</div></div>', unsafe_allow_html=True)

def _mkt_right():
    st.markdown("""
<div class="cn-card">
  <div class="sec-label">Best Campaign Market</div>
  <div style="font-size:18px;font-weight:800;color:#14B8A6;">South Africa</div>
  <div style="font-size:10px;color:#6B7FA3;margin-top:4px;">31% engagement  -  Highest quality audience</div>
</div>
<div class="cn-card">
  <div class="sec-label">Campaign Signals</div>
  <div style="font-size:11px;margin-bottom:5px;color:#F0F4F8;"><span style="color:#4ADE80;">●</span> AI Solutions - <b>High Intent</b></div>
  <div style="font-size:11px;margin-bottom:5px;color:#F0F4F8;"><span style="color:#FBBF24;">●</span> Cybersecurity - <b>Under-Promoted</b></div>
  <div style="font-size:11px;color:#F0F4F8;"><span style="color:#22D3EE;">●</span> Cloud & Data - <b>Growing</b></div>
</div>
<div class="cn-card">
  <div class="sec-label">Audience Quality</div>
  <div style="font-size:28px;font-weight:800;color:#14B8A6;text-align:center;padding:6px 0;">78%</div>
  <div style="font-size:10px;color:#6B7FA3;text-align:center;">Human audience quality score</div>
</div>""", unsafe_allow_html=True)

def _mkt_kpis(df=None):
    live_today = _live_today_df(df if df is not None else st.session_state.get("_marketing_df_cache"), "marketing_kpi_cards")
    stats = _kpi_stats(live_today)
    baseline, baseline_label = _baseline_stats(st.session_state.get("_marketing_df_cache"))
    engaged_delta, engaged_cls = _metric_delta(stats, baseline, "engaged")
    engagement_delta, engagement_cls = _metric_delta(stats, baseline, "engagement_rate", "rate")
    quality_delta, quality_cls = _metric_delta(stats, baseline, "quality", "rate")
    visitors_sub = "lower than yesterday" if engaged_cls == "down" and engaged_delta else f"today vs {baseline_label}"
    kpis=[
        ("Meaningful Actions Taken Today", f"{stats['engagement_rate']:.1f}%", "Visitors did something valuable", engagement_delta, engagement_cls, "anchor", "This is the primary campaign signal: it measures visitors who took a valuable action, not just page views."),
        ("Audience Quality Score", f"{stats['quality']}%", "How relevant our traffic is", quality_delta, quality_cls, "", "Higher quality means less bot/noise traffic and a better audience fit for campaigns."),
        ("Best Market to Target Now", stats["top_market"], "Highest current campaign opportunity", "", "", "", "Use this market first when choosing campaign geography for the active filters."),
        ("Visitors Today", f"{stats['engaged']:,}", visitors_sub, engaged_delta, engaged_cls, "", "This is the current engaged visitor volume under the selected filters."),
        ("Best Entry Page", _marketing_entry_page(live_today), "Where visitors start most often", "", "", "", "Campaign traffic should guide visitors from this entry point into service and contact actions."),
    ]
    cols=st.columns(5,gap="small")
    cls_map={"up":"delta-up","watch":"delta-watch","down":"delta-down"}
    for col,(lbl,val,sub,chg,cls,extra,insight) in zip(cols,kpis):
        with col:
            delta=f'<div class="kpi-delta {cls_map.get(cls,"")}">{chg}</div>' if chg else '<div style="height:20px;"></div>'
            anchor = " marketing-kpi-anchor" if extra == "anchor" else ""
            st.markdown(f'<div class="kpi-card marketing-kpi-card{anchor}"><div class="kpi-label" title="{lbl}">{lbl}</div><div class="kpi-value live-count" title="{val}" style="color:#14B8A6;">{val}</div>{delta}<div class="kpi-sub" title="{sub}">{sub}</div><div class="kpi-hover-insight">{insight}</div></div>', unsafe_allow_html=True)

def render_marketing_overview(df):
    st.session_state["_marketing_df_cache"] = st.session_state.get("_live_replay_df") if st.session_state.get("_live_replay_df") is not None else st.session_state.get("_live_unfiltered_df", df)
    st.markdown('<div class="marketing-overview-tight-start"></div>', unsafe_allow_html=True)
    st.markdown('<div class="marketing-overview-safe">', unsafe_allow_html=True)

    # ── Row 1: KPI cards + live pulse (side by side) ──
    try:
        @st.fragment(run_every=LIVE_KPI_FRAGMENT_SECONDS)
        def _live_marketing_kpis():
            _df = _refresh_live_replay_cache()
            if _df is not None and not _df.empty:
                st.session_state["_marketing_df_cache"] = _df
            _mkt_kpis(st.session_state.get("_marketing_df_cache"))
        _live_marketing_kpis()
    except Exception:
        _mkt_kpis(df)
    _campaign_insight(df)

    # ── Row 2: Map (left 55%) | 2×2 chart grid (right 45%) ──
    left, center, right = st.columns([1.0, 1.12, 1.0], gap="small")
    with left:
        _market_priority_table(df)
        _best_time_campaigns(df)
    with center:
        _visitors_vs_engagement(df)
        _content_funnel(df)
    with right:
        _promo_gap()
        _recommended_campaign_actions(df)
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
def _strategic_growth():
    mo=["Jan","Feb","Mar","Apr","May","Jun"]
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=mo,y=[72,76,79,82,82.6,None],name="Revenue (Pula M)",line=dict(color="#22D3EE",width=2),mode="lines+markers",marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=mo,y=[28,32,35,38,40,None],name="AI Solutions",line=dict(color="#A855F7",width=2),mode="lines+markers",marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=mo,y=[44,44,44,44,42.6,None],name="Services",line=dict(color="#14B8A6",width=2),mode="lines+markers",marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=mo,y=[80,83,85,90,95,100],name="Target",line=dict(color="#A855F7",width=1.5,dash="dash"),mode="lines"))
    fig.add_trace(go.Scatter(x=mo,y=[68,72,76,79,82,82.6],name="Prev. Month",line=dict(color="#3A4A5E",width=1.5,dash="dot"),mode="lines"))
    _cl(fig,145)
    st.markdown('<div class="cn-card"><div class="sec-label">Strategic Growth Trend</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _ai_traction():
    mo=["Jan","Feb","Mar","Apr"]
    fig=go.Figure()
    fig.add_trace(go.Bar(x=mo,y=[22,25,27,29],name="AI Interest %",marker_color="rgba(34,211,238,0.7)"))
    fig.add_trace(go.Scatter(x=mo,y=[25,25,28,30],name="Target %",mode="lines+markers",line=dict(color="#A855F7",width=2,dash="dash"),marker=dict(size=5)))
    _cl(fig,145); fig.update_layout(barmode="group",bargap=0.3,yaxis_title="% Sessions")
    st.markdown('<div class="cn-card"><div class="sec-label">AI Assistant Traction</div><span style="background:rgba(168,85,247,0.12);color:#A855F7;border:1px solid rgba(168,85,247,0.25);border-radius:20px;padding:2px 9px;font-size:9px;font-weight:700;">Target Achievement: 97%</span>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _forecast_90():
    np.random.seed(5)
    ad=list(range(-60,1)); fwd=list(range(0,91))
    av=[1100+i*2.5+np.random.randint(-18,18) for i in range(61)]
    fb=av[-1]; fv=[fb+i*3.2 for i in range(91)]
    fu=[v+55+i*0.7 for i,v in enumerate(fv)]; fl=[v-55-i*0.7 for i,v in enumerate(fv)]
    tg=[1300+i*4 for i in range(91)]
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=ad,y=av,name="Actual",line=dict(color="#22D3EE",width=2),mode="lines"))
    fig.add_trace(go.Scatter(x=fwd,y=fv,name="Forecast",line=dict(color="#22D3EE",width=2,dash="dash"),mode="lines"))
    fig.add_trace(go.Scatter(x=fwd+fwd[::-1],y=fu+fl[::-1],fill="toself",fillcolor="rgba(34,211,238,0.06)",line=dict(width=0),name="Confidence"))
    fig.add_trace(go.Scatter(x=fwd,y=tg,name="Target Aim",line=dict(color="#A855F7",width=1.5,dash="dash"),mode="lines"))
    _cl(fig,145)
    st.markdown(f'<div class="cn-card"><div class="sec-label">90-Day Forecast</div><div style="font-size:9px;color:#FBBF24;margin-bottom:6px;display:flex;align-items:center;gap:6px;">{svg_icon("alert", 13, "#FBBF24")} Rule-based linear forecast, not predictive AI.</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar": True})
    st.markdown('</div>', unsafe_allow_html=True)

def _exec_right():
    st.markdown("""
<div class="cn-card">
  <div class="sec-label">Regional Priority</div>
  <div style="font-size:14px;font-weight:700;color:#A855F7;">South Africa + Zambia</div>
  <div style="font-size:10px;color:#6B7FA3;margin-top:4px;">Core + Strategic Hub anchors</div>
  <div style="font-size:11px;color:#4ADE80;margin-top:6px;font-weight:600;">Done Invest - protect lead</div>
</div>
<div class="cn-card">
  <div class="sec-label">Strategic Signals</div>
  <div style="font-size:11px;margin-bottom:5px;color:#F0F4F8;"><span style="color:#4ADE80;">●</span> AI Solutions - <b>Accelerating</b></div>
  <div style="font-size:11px;margin-bottom:5px;color:#F0F4F8;"><span style="color:#22D3EE;">●</span> SADC Expansion - <b>On Track</b></div>
  <div style="font-size:11px;color:#F0F4F8;"><span style="color:#F87171;">●</span> Zimbabwe - <b>Monitor</b></div>
</div>
<div class="cn-card">
  <div class="sec-label">Risk Outlook</div>
  <div style="font-size:28px;font-weight:800;color:#FBBF24;text-align:center;padding:6px 0;
    text-shadow:0 0 20px rgba(251,191,36,0.3);">MEDIUM</div>
  <div style="font-size:10px;color:#6B7FA3;text-align:center;">3 markets need executive attention</div>
</div>""", unsafe_allow_html=True)

def _exec_kpis(df=None):
    live_today = _live_today_df(df if df is not None else st.session_state.get("_executive_df_cache"), "executive_kpi_cards")
    stats = _kpi_stats(live_today)
    baseline, baseline_label = _baseline_stats(st.session_state.get("_executive_df_cache"))
    growth = min(99, int(stats["potential"] / max(1, stats["human"]) * 100)) if stats["human"] else 0
    base_growth = min(99, int(float(baseline.get("potential", 0) or 0) / max(1, float(baseline.get("human", 0) or 0)) * 100)) if baseline else 0
    growth_delta, growth_cls = _metric_delta({"growth": growth}, {"growth": base_growth}, "growth", "rate")
    potential_delta, potential_cls = _metric_delta(stats, baseline, "potential")
    ai_delta, ai_cls = _metric_delta(stats, baseline, "ai_rate", "rate")
    market_delta, market_cls = _metric_delta(stats, baseline, "active_markets")
    risk_delta, risk_cls = _metric_delta(stats, baseline, "risk_alerts")
    kpis=[
        ("Growth Direction", f"+{growth}%", f"today vs {baseline_label}", growth_delta, growth_cls),
        ("Potential Customers", f"{stats['potential']:,}", f"today vs {baseline_label}", potential_delta, potential_cls),
        ("AI Assistant Traction", f"{stats['ai_rate']:.1f}%", f"today vs {baseline_label}", ai_delta, ai_cls),
        ("Active SADC Markets", str(stats["active_markets"]), f"today vs {baseline_label}", market_delta, market_cls),
        ("Strategic Risk Alerts", str(stats["risk_alerts"]), f"today vs {baseline_label}", risk_delta, risk_cls)]
    cols=st.columns(5,gap="small")
    cls_map={"up":"delta-up","watch":"delta-watch","down":"delta-down"}
    for col,(lbl,val,sub,chg,cls) in zip(cols,kpis):
        with col:
            delta=f'<div class="kpi-delta {cls_map.get(cls,"")}">{chg}</div>' if chg else '<div style="height:20px;"></div>'
            st.markdown(f'<div class="kpi-card executive-kpi-card"><div class="kpi-label" title="{lbl}">{lbl}</div><div class="kpi-value live-count" title="{val}" style="color:#A855F7;">{val}</div>{delta}<div class="kpi-sub" title="{sub}">{sub}</div></div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="executive-board-summary" style="background:linear-gradient(90deg,rgba(168,85,247,0.07),rgba(34,211,238,0.04));
  border:1px solid rgba(168,85,247,0.18);border-radius:8px;padding:4px 12px;margin:4px 0;">
  <span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:#A855F7;">Board Summary — </span>
  <span style="font-size:11px;color:#F0F4F8;">Live simulation. Opportunity value is modelled, not audited revenue.</span>
</div>""", unsafe_allow_html=True)

def render_executive_overview(df):
    st.session_state["_executive_df_cache"] = st.session_state.get("_live_replay_df") if st.session_state.get("_live_replay_df") is not None else st.session_state.get("_live_unfiltered_df", df)
    st.markdown('<div class="executive-overview-tight-start"></div>', unsafe_allow_html=True)

    # ── Row 1: KPI cards + live pulse (side by side) ──
    try:
        @st.fragment(run_every=LIVE_KPI_FRAGMENT_SECONDS)
        def _live_executive_kpis():
            _df = _refresh_live_replay_cache()
            if _df is not None and not _df.empty:
                st.session_state["_executive_df_cache"] = _df
            _exec_kpis(st.session_state.get("_executive_df_cache"))
        _live_executive_kpis()
    except Exception:
        _exec_kpis(df)
    st.markdown('<div style="height:1px;background:linear-gradient(90deg,rgba(34,211,238,0.18),rgba(34,211,238,0.06),transparent);margin:20px 0;"></div>', unsafe_allow_html=True)

    # ── Row 2: Map (left 55%) | 2×2 chart grid (right 45%) ──
    col_map, col_right = st.columns([0.8, 1.4], gap="small")
    with col_map:
        render_sadc_map("executive", 400)
    with col_right:
        c1, c2, c3 = st.columns(3, gap="small")
        with c1: _strategic_growth()
        with c2: _ai_traction()
        with c3: _forecast_90()
        st.markdown('<div class="executive-insight-below">', unsafe_allow_html=True)
        if _EXECUTIVE_VIEWS_OK:
            st.markdown(render_executive_drawer(), unsafe_allow_html=True)
        else:
            _exec_right()
        st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS / FORECASTING / DATA TABS
# ═══════════════════════════════════════════════════════════════════════════════
def render_analytics_tab(dash):
    CARDS={"Sales":[("Funnel by Market","chart"),("Funnel by Service","chart"),("Repeat Visitor Conversion","sync"),
                    ("Potential Customer Segment Quality","diamond"),("Sales Insight Assistant","bot"),("Sales Hotzones Map","map"),
                    ("Top Service Demand","chart"),("Potential Customers by Country","globe"),("Demo Intent by Hour","clock"),("Conversion Rate by Stage","target")],
           "Marketing":[("Audience Segments Over Time","chart"),("Country Engagement Breakdown","globe"),
                        ("Landing Page Performance","file"),("SADC Reach Map + Ranking","map"),("Service Promotion Gap Detail","chart"),("Marketing Insight Assistant","bot")],
           "Executive":[("Regional Target Table","file"),("Market Contribution Analysis","chart"),
                        ("AI Assistant by Market","bot"),("Risk / Anomaly Trend","alert"),("Executive Insight Assistant","globe")]}
    ph_grid(CARDS.get(dash,[]))

def render_forecasting_tab(dash):
    CARDS={"Sales":[("Forecast Summary","file"),("Forecast Confidence","target"),("30-Day Potential Customer Forecast","chart"),
                    ("Demo Request Forecast","chart"),("AI-to-Demo What-If Analysis","bot"),("Forecast vs Target","flag"),
                    ("Sales Readiness Recommendations","lightbulb"),("Market Outlook","map"),("Risk Outlook","alert"),("Alert Center","bell")],
           "Marketing":[("Audience Growth Forecast","chart"),("Engaged Sessions Forecast","chart"),
                        ("Campaign What-If Scenario","bot"),("Campaign Target Tracker","flag"),("Campaign Recommendation","lightbulb")],
           "Executive":[("90-Day Potential Customer Forecast","chart"),("Regional Expansion Forecast","map"),
                        ("AI Traction Forecast","bot"),("Risk / Anomaly Outlook","alert"),("Investment Recommendation","lightbulb"),("Forecast vs Target","flag")]}
    ph_grid(CARDS.get(dash,[]))

def render_data_tab(dash,df):
    CARDS={"Sales":[("Sales Action Queue","check"),("Potential Customers Table","file"),("Evidence Snapshot","folder"),
                    ("Export Center","download"),("Data Quality Summary","search"),("Methodology & Assumptions","book"),
                    ("Potential Revenue by Region","money"),("New Potential Customers Trend","chart"),("Top Customers by Revenue","briefcase")],
           "Marketing":[("Campaign Opportunity Table","file"),("Filtered Audience Data","folder"),("Evidence Pack CSV","download"),
                        ("Weekly PDF Report","file"),("Monthly PDF Report","file"),("Methodology Note","book"),("Landing Page Export","file"),("Campaign Performance Export","chart")],
           "Executive":[("Executive Decision Brief","file"),("Regional Priority Table","map"),("Risk Evidence Table","alert"),
                        ("Executive Summary CSV","download"),("Filtered Data CSV","folder"),("Weekly PDF Report","file"),("Monthly PDF Report","file"),("Methodology Note","book")]}
    ph_grid(CARDS.get(dash,[]))
    if df is not None:
        st.markdown('<div class="cn-card"><div class="sec-label">Quick Export</div>', unsafe_allow_html=True)
        h=_human_df(df)
        st.download_button("Download Filtered Data (CSV)",h.head(5000).to_csv(index=False).encode(),f"cybernova_{dash.lower()}.csv","text/csv",use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── STATUS BAR ────────────────────────────────────────────────────────────────
def render_status_bar():
    sync=datetime.datetime.now().strftime("%H:%M:%S")
    v=st.session_state
    st.markdown(f"""
<div class="status-bar">
  <div class="si">Data Sync <span>{sync}</span></div>
  <div class="si">AI Insights <span>12 new</span></div>
  <div class="si">Alerts <span class="pill-warn">{v.alert_count} active</span></div>
  <div class="si">Status <span class="pill-ok">Operational</span></div>
  <div style="margin-left:auto;font-size:10px;color:#2A3A4E;">CyberNova BI Portal  -  Prototype v1.0</div>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    inject_css()
    init_state()
    restore_from_query_params()

    if not st.session_state.authenticated:
        render_login()
        return

    # Inject dashboard-specific CSS
    if st.session_state.get("active_dashboard") == "Sales" and _SALES_VIEWS_OK:
        inject_sales_css()
    if st.session_state.get("active_dashboard") == "Marketing" and _MARKETING_VIEWS_OK:
        inject_marketing_css()
    if st.session_state.get("active_dashboard") == "Executive" and _EXECUTIVE_VIEWS_OK:
        inject_executive_css()

    # ── Layout: conditional admin drawer ──
    drawer_open = st.session_state.get("admin_drawer_open", False)

    if drawer_open:
        main_col, drawer_col = st.columns([4.2, 1.1], gap="small")
        with drawer_col:
            render_admin_drawer()
    else:
        main_col = st.container()

    with main_col:
        render_header()

        df = load_data()
        if df is None:
            st.toast("Using mock data - CSV not found")
            df = mock_data()

        live_rows = pd.DataFrame()
        try:
            if not LIVE_QUEUE_PATH.exists():
                st.warning("Live stream queue not found. Generate live data first.")
            else:
                live_rows = _release_live_rows()
                live_norm = _normalize_live_queue(live_rows)
                if live_norm is not None and not live_norm.empty:
                    st.session_state["_live_replay_df"] = live_norm
                _maybe_autorefresh_live()
        except Exception as live_err:
            live_rows = pd.DataFrame()
            st.warning(f"Live feed paused safely: {live_err}")

        st.session_state["_live_unfiltered_df"] = df

        # Apply date filter
        if "date" in df.columns or "timestamp" in df.columns:
            date_col = "date" if "date" in df.columns else "timestamp"
            d_start = st.session_state.get("date_start")
            d_end = st.session_state.get("date_end")
            if d_start and d_end:
                if pd.api.types.is_datetime64_any_dtype(df[date_col]):
                    df_dates = df[date_col]
                else:
                    df_dates = pd.to_datetime(df[date_col], errors="coerce")
                mask = (df_dates.dt.date >= d_start) & (df_dates.dt.date <= d_end)
                df_date_filtered = df[mask]
                if not df_date_filtered.empty:
                    df = df_date_filtered

        mkt = st.session_state.selected_market
        if mkt != "All" and "country" in df.columns:
            df_f = df[df["country"]==mkt]
            if df_f.empty: df_f = df
        else:
            df_f = df

        svc = st.session_state.get("svc_filter", "All Services")
        if svc != "All Services" and "service_name" in df_f.columns:
            svc_terms = {
                "AI Solutions": ["AI", "Assistant", "Predictive"],
                "Cybersecurity": ["Cyber", "Security", "Risk"],
                "Cloud & Data": ["Cloud", "Data", "Digital Transformation"],
                "Advisory & Training": ["Advisory", "Training", "Events"],
            }.get(svc, [svc])
            mask = pd.Series(False, index=df_f.index)
            for term in svc_terms:
                mask = mask | df_f["service_name"].astype(str).str.contains(term, case=False, na=False)
            if mask.any():
                df_f = df_f[mask]

        seg = st.session_state.get("seg_filter", "All Segments")
        if seg != "All Segments" and "segment" in df_f.columns:
            seg_mask = df_f["segment"].astype(str).str.contains(seg, case=False, na=False)
            if seg_mask.any():
                df_f = df_f[seg_mask]

        outcome = st.session_state.get("outcome_filter", "All")
        if outcome != "All":
            if outcome == "Potential Customer" and "potential_customer_signal" in df_f.columns:
                df_f = df_f[_truthy_series(df_f, "potential_customer_signal")]
            elif outcome == "Demo Request" and "has_demo_request" in df_f.columns:
                df_f = df_f[_truthy_series(df_f, "has_demo_request")]
            elif outcome == "Engaged" and "is_engaged_session" in df_f.columns:
                df_f = df_f[_truthy_series(df_f, "is_engaged_session")]
            elif outcome == "Bounce" and "distinct_pages_session" in df_f.columns:
                df_f = df_f[_num_series(df_f, "distinct_pages_session") <= 1]

        status_filter = st.session_state.get("status_filter", "All Status Codes")
        if status_filter != "All Status Codes" and "status_code" in df_f.columns:
            status_num = pd.to_numeric(df_f["status_code"], errors="coerce")
            df_f = df_f[status_num == int(status_filter)]

        render_chips(df_f)

        dash = st.session_state.active_dashboard
        tab_options = ["Overview", "Analytics", "Forecasting", "Data & Export"]
        active_tab = st.session_state.get("active_tab", "Overview")
        if active_tab not in tab_options:
            active_tab = "Overview"
        selected_tab = st.radio(
            "Dashboard section",
            tab_options,
            index=tab_options.index(active_tab),
            horizontal=True,
            label_visibility="collapsed",
            key="active_tab",
        )

        if selected_tab == "Overview":
            if dash=="Sales":       render_sales_overview(df_f)
            elif dash=="Marketing": render_marketing_overview(df_f)
            else:                   render_executive_overview(df_f)
        elif selected_tab == "Analytics":
            if dash=="Sales" and _SALES_VIEWS_OK:
                render_sales_analytics(df_f)
                _sales_srs_evidence_panels(df_f)
            elif dash=="Marketing" and _MARKETING_VIEWS_OK:
                render_marketing_analytics(df_f)
            elif dash=="Executive" and _EXECUTIVE_VIEWS_OK:
                render_executive_analytics(df_f)
            else:
                render_analytics_tab(dash)
        elif selected_tab == "Forecasting":
            if dash=="Sales" and _SALES_VIEWS_OK:
                render_sales_forecasting(df_f)
            elif dash=="Marketing" and _MARKETING_VIEWS_OK:
                render_marketing_forecasting(df_f)
            elif dash=="Executive" and _EXECUTIVE_VIEWS_OK:
                render_executive_forecasting(df_f)
            else:
                render_forecasting_tab(dash)
        else:
            d_start = st.session_state.get("date_start")
            d_end = st.session_state.get("date_end")
            if dash=="Sales" and _SALES_VIEWS_OK:
                _sales_srs_evidence_panels(df_f)
                render_sales_data(df_f)
            elif dash=="Marketing" and _MARKETING_VIEWS_OK:
                render_marketing_data(df_f, d_start, d_end)
            elif dash=="Executive" and _EXECUTIVE_VIEWS_OK:
                render_executive_data(df_f, d_start, d_end)
            else:
                render_data_tab(dash, df_f)

        render_status_bar()

if __name__ == "__main__":
    main()
