"""
sales_views.py - CyberNova BI Portal  -  Sales Dashboard
Imported by cybernovaapp.py. Provides 4 tab renderers + CSS injection.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

try:
    from exports import (
        build_weekly_report_pdf,
        build_monthly_report_pdf,
        build_methodology_pdf,
        build_kpi_summary,
        dataframe_to_csv_bytes,
        filter_last_n_days,
        period_label,
    )
    _EXPORTS_OK = True
except Exception:
    _EXPORTS_OK = False

# ── COLOR CONSTANTS ──────────────────────────────────────────────────────────
_CYAN   = "#22D3EE"
_TEAL   = "#14B8A6"
_GREEN  = "#7CFF4F"
_YELLOW = "#FFD84A"
_ORANGE = "#F59E0B"
_RED    = "#F87171"
_PURPLE = "#A855F7"
_GRAY   = "#8A98A6"
_WHITE  = "#F8FAFC"

_BG_PANEL     = "#071820"
_BG_CARD      = "rgba(8,22,28,0.78)"
_BG_CARD_STR  = "rgba(10,28,36,0.92)"
_BORDER_SOFT  = "rgba(77,255,225,0.14)"
_BORDER_ACT   = "rgba(0,255,209,0.55)"

_COLOR_MAP = {
    "Core Market":  _CYAN,
    "Strategic Hub": _TEAL,
    "High Growth":  _YELLOW,
    "Emerging":     _GREEN,
    "Stable":       _GRAY,
}

_STAGE_COLORS = {
    "Engaged":  _TEAL,
    "Qualified": _GREEN,
    "Proposal": _ORANGE,
    "Won":      _CYAN,
    "Risk":     _RED,
}

MAP_NODES = [
    {"city":"Cape Town",  "country":"South Africa", "lat":-33.9, "lon":18.4,  "status":"Core Market",   "customers":450, "demos":98,  "conv":"21.8%","revenue":"P18.2M","ai":34,"risk":"Low"},
    {"city":"Durban",     "country":"South Africa", "lat":-29.9, "lon":30.9,  "status":"High Growth",   "customers":112, "demos":28,  "conv":"25%",  "revenue":"P6.1M", "ai":28,"risk":"Low"},
    {"city":"Lusaka",     "country":"Zambia",        "lat":-15.4, "lon":28.3,  "status":"Strategic Hub", "customers":180, "demos":41,  "conv":"22.8%","revenue":"P9.5M", "ai":41,"risk":"Low"},
    {"city":"Maputo",     "country":"Mozambique",    "lat":-25.9, "lon":32.6,  "status":"Strategic Hub", "customers":140, "demos":29,  "conv":"20.7%","revenue":"P7.2M", "ai":37,"risk":"Medium"},
    {"city":"Gaborone",   "country":"Botswana",      "lat":-24.7, "lon":25.9,  "status":"Stable",        "customers":95,  "demos":18,  "conv":"18.9%","revenue":"P4.8M", "ai":22,"risk":"Low"},
    {"city":"Harare",     "country":"Zimbabwe",      "lat":-17.8, "lon":31.0,  "status":"High Growth",   "customers":120, "demos":31,  "conv":"25.8%","revenue":"P6.8M", "ai":31,"risk":"Medium"},
    {"city":"Luanda",     "country":"Angola",        "lat":-8.8,  "lon":13.2,  "status":"Emerging",      "customers":72,  "demos":14,  "conv":"19.4%","revenue":"P3.1M", "ai":18,"risk":"Medium"},
    {"city":"Windhoek",   "country":"Namibia",       "lat":-22.6, "lon":17.1,  "status":"Emerging",      "customers":55,  "demos":11,  "conv":"20%",  "revenue":"P2.3M", "ai":15,"risk":"Low"},
    {"city":"Lilongwe",   "country":"Malawi",        "lat":-13.9, "lon":33.8,  "status":"Emerging",      "customers":48,  "demos":8,   "conv":"16.7%","revenue":"P1.6M", "ai":12,"risk":"Low"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CSS INJECTION
# ═══════════════════════════════════════════════════════════════════════════════
def inject_sales_css():
    st.markdown("""
<style>
/* ── Base cyber card ─────────────────────────────────────────────────────── */
.cyber-card {
  background: rgba(8,22,28,0.78);
  border: 1px solid rgba(77,255,225,0.14);
  border-radius: 18px;
  padding: 20px 22px;
  margin-bottom: 12px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: transform .22s, border-color .22s, box-shadow .22s;
  position: relative;
  overflow: visible;
}
.cyber-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,255,209,0.18), transparent);
}
.cyber-card:hover {
  transform: translateY(-2px);
  border-color: rgba(0,255,209,0.55);
  box-shadow: 0 0 28px rgba(34,211,238,0.13);
}
.cyber-card.anchor {
  border-color: rgba(0,255,209,0.42);
  box-shadow: 0 0 32px rgba(34,211,238,0.18), inset 0 0 20px rgba(34,211,238,0.04);
}
.cyber-card.anchor::before {
  background: linear-gradient(90deg, transparent, rgba(0,255,209,0.35), transparent);
}
/* ── Section title ───────────────────────────────────────────────────────── */
.sv-title {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: #22D3EE;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(77,255,225,0.12);
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  overflow-wrap: anywhere;
}
/* ── KPI grid ────────────────────────────────────────────────────────────── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 14px;
}
.sv-kpi-card {
  min-height: 132px;
  background: rgba(8,22,28,0.78);
  border: 1px solid rgba(77,255,225,0.14);
  border-radius: 16px;
  padding: 18px 20px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: transform .2s, border-color .2s;
  cursor: default;
}
.sv-kpi-card:hover {
  transform: translateY(-2px);
  border-color: rgba(0,255,209,0.45);
}
.kpi-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: #8A98A6;
  margin-bottom: 8px;
}
.kpi-value {
  font-size: 2rem;
  font-weight: 800;
  color: #FFFFFF;
  line-height: 1;
  margin-bottom: 6px;
}
.kpi-delta-up {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(124,255,79,0.12);
  color: #7CFF4F;
  border: 1px solid rgba(124,255,79,0.22);
}
.kpi-delta-watch {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(255,216,74,0.12);
  color: #FFD84A;
  border: 1px solid rgba(255,216,74,0.22);
}
.kpi-delta-down {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  background: rgba(248,113,113,0.12);
  color: #F87171;
  border: 1px solid rgba(248,113,113,0.22);
}
/* ── Live pulse strip ────────────────────────────────────────────────────── */
.live-pulse-strip {
  width: 100%;
  background: linear-gradient(90deg, rgba(34,211,238,0.06), rgba(20,184,166,0.04), rgba(34,211,238,0.03));
  border: 1px solid rgba(77,255,225,0.14);
  border-radius: 10px;
  padding: 9px 16px;
  display: flex;
  gap: 0;
  align-items: center;
  margin-bottom: 12px;
}
.live-pulse-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px;
  border-right: 1px solid rgba(77,255,225,0.1);
}
.live-pulse-item:last-child { border-right: none; }
.pl { font-size: 9px; color: #8A98A6; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 3px; }
.pv { font-size: 16px; font-weight: 700; color: #22D3EE; }
/* ── Stage pills ─────────────────────────────────────────────────────────── */
.stage-pill {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 600;
}
.stage-pill-engaged   { background: rgba(20,184,166,0.15);  color: #14B8A6; border: 1px solid rgba(20,184,166,0.3); }
.stage-pill-qualified { background: rgba(124,255,79,0.12);  color: #7CFF4F; border: 1px solid rgba(124,255,79,0.25); }
.stage-pill-proposal  { background: rgba(245,158,11,0.12);  color: #F59E0B; border: 1px solid rgba(245,158,11,0.25); }
.stage-pill-won       { background: rgba(34,211,238,0.12);  color: #22D3EE; border: 1px solid rgba(34,211,238,0.25); }
.stage-pill-risk      { background: rgba(248,113,113,0.12); color: #F87171; border: 1px solid rgba(248,113,113,0.25); }
/* ── Country table ───────────────────────────────────────────────────────── */
.country-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.country-table th {
  font-size: 9px; font-weight: 700; letter-spacing: .12em;
  text-transform: uppercase; color: #8A98A6; padding: 8px 10px;
  border-bottom: 1px solid rgba(77,255,225,0.12);
  position: sticky; top: 0;
  background: rgba(8,22,28,0.95);
  z-index: 2;
}
.country-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid rgba(77,255,225,0.06);
  align-items: center;
  transition: background .15s;
}
.country-row:hover { background: rgba(20,184,166,0.07); border-radius: 8px; }
/* ── Insight card ────────────────────────────────────────────────────────── */
.insight-card {
  background: rgba(8,22,28,0.78);
  border: 1px solid rgba(77,255,225,0.14);
  border-left: 3px solid #22D3EE;
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 8px;
  backdrop-filter: blur(12px);
}
/* ── Export button card ──────────────────────────────────────────────────── */
.export-btn-card {
  background: rgba(8,22,28,0.78);
  border: 1px solid rgba(77,255,225,0.14);
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: border-color .2s, transform .15s;
  min-width: 0;
  overflow: hidden;
}
.export-btn-card:hover {
  border-color: rgba(0,255,209,0.45);
  transform: translateY(-1px);
}
/* ── Quality bar ─────────────────────────────────────────────────────────── */
.quality-bar-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.quality-bar-track {
  flex: 1; height: 6px;
  background: rgba(77,255,225,0.08);
  border-radius: 3px;
  overflow: hidden;
}
.quality-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width .4s;
}
/* ── Forecast signal card ────────────────────────────────────────────────── */
.forecast-signal-card {
  background: rgba(8,22,28,0.78);
  border: 1px solid rgba(77,255,225,0.14);
  border-radius: 12px;
  padding: 10px 14px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}
/* ── Alert item ──────────────────────────────────────────────────────────── */
.alert-item {
  background: rgba(248,113,113,0.05);
  border: 1px solid rgba(248,113,113,0.2);
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #F8FAFC;
}
.alert-item.warn {
  background: rgba(255,216,74,0.05);
  border-color: rgba(255,216,74,0.2);
}
/* Sales tab layout safety: override global app height/stretch rules inside these tabs. */
.st-key-sales_analytics_scope div[data-testid="element-container"],
.st-key-sales_forecasting_scope div[data-testid="element-container"],
.st-key-sales_data_scope div[data-testid="element-container"] {
  height: auto !important;
  min-height: 0 !important;
}
.st-key-sales_analytics_scope div[data-testid="stVerticalBlock"],
.st-key-sales_forecasting_scope div[data-testid="stVerticalBlock"],
.st-key-sales_data_scope div[data-testid="stVerticalBlock"] {
  gap: 12px !important;
}
.st-key-sales_analytics_scope div[data-testid="stColumn"],
.st-key-sales_forecasting_scope div[data-testid="stColumn"],
.st-key-sales_data_scope div[data-testid="stColumn"] {
  min-width: 0 !important;
}
.st-key-sales_analytics_scope div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
.st-key-sales_forecasting_scope div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
.st-key-sales_data_scope div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
  height: auto !important;
  min-height: 0 !important;
}
.st-key-sales_analytics_scope .cyber-card,
.st-key-sales_forecasting_scope .cyber-card,
.st-key-sales_data_scope .cyber-card {
  width: 100%;
  min-width: 0;
  padding: 16px 18px;
  margin-bottom: 12px;
  overflow: visible;
}
.st-key-sales_analytics_scope div[data-testid="stPlotlyChart"],
.st-key-sales_forecasting_scope div[data-testid="stPlotlyChart"],
.st-key-sales_data_scope div[data-testid="stPlotlyChart"] {
  width: 100% !important;
  min-width: 0 !important;
  overflow: hidden !important;
}
.st-key-sales_analytics_scope .js-plotly-plot,
.st-key-sales_forecasting_scope .js-plotly-plot,
.st-key-sales_data_scope .js-plotly-plot {
  max-width: 100% !important;
}
.st-key-sales_data_scope .stDownloadButton button {
  white-space: normal !important;
  min-height: 42px;
  line-height: 1.2 !important;
  padding: 8px 10px !important;
}
.st-key-sales_analytics_scope [data-testid="stMarkdownContainer"],
.st-key-sales_forecasting_scope [data-testid="stMarkdownContainer"],
.st-key-sales_data_scope [data-testid="stMarkdownContainer"] {
  min-width: 0 !important;
  overflow-wrap: anywhere;
}
.st-key-sales_forecasting_scope .sv-kpi-card {
  min-height: 104px;
  padding: 12px 13px;
}
.st-key-sales_forecasting_scope .kpi-value {
  font-size: 1.38rem;
}
.st-key-sales_forecasting_scope .forecast-signal-card,
.st-key-sales_forecasting_scope .alert-item,
.st-key-sales_data_scope .export-btn-card,
.st-key-sales_data_scope .quality-bar-row {
  max-width: 100%;
  min-width: 0;
}
.st-key-sales_forecasting_scope div[role="slider"],
.st-key-sales_forecasting_scope .stSlider {
  min-width: 0 !important;
  max-width: 100% !important;
}
.st-key-sales_analytics_scope table,
.st-key-sales_data_scope table {
  table-layout: fixed;
  width: 100%;
}
.st-key-sales_data_scope .dataframe,
.st-key-sales_data_scope div[data-testid="stDataFrame"] {
  max-width: 100% !important;
  overflow: auto !important;
}
@media (max-width: 1100px) {
  .st-key-sales_analytics_scope .cyber-card,
  .st-key-sales_forecasting_scope .cyber-card,
  .st-key-sales_data_scope .cyber-card {
    padding: 12px 13px;
  }
  .sv-kpi-card {
    min-height: 112px;
    padding: 13px 14px;
  }
  .kpi-value {
    font-size: 1.45rem;
  }
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _chart_layout(fig, h=210):
    """Apply consistent dark chart layout."""
    fig.update_layout(
        height=h,
        margin=dict(l=50, r=26, t=24, b=70),
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
            gridcolor="rgba(148,163,184,0.10)", color="#94A3B8", showgrid=True, zeroline=False,
            showspikes=True, spikesnap="cursor",
            spikecolor="rgba(45,212,191,0.22)", spikethickness=1,
            tickfont=dict(size=10, color="#CBD5E1"),
            title_font=dict(size=10, color="#94A3B8"),
            automargin=True,
        ),
        yaxis=dict(
            gridcolor="rgba(148,163,184,0.10)", color="#94A3B8", showgrid=True, zeroline=False,
            tickfont=dict(size=10, color="#CBD5E1"),
            title_font=dict(size=10, color="#94A3B8"),
            automargin=True,
        ),
        legend=dict(
            bgcolor="rgba(7,16,28,0.72)",
            bordercolor="rgba(148,163,184,0.16)",
            borderwidth=1,
            font=dict(color="#CBD5E1", size=10, family="Inter"),
            orientation="h",
            y=-0.24,
            x=0,
        ),
    )
    fig.update_traces(marker_line_width=0, selector=dict(type="bar"))
    fig.update_traces(line=dict(width=2.4), selector=dict(type="scatter"))


_ICON_SVG = {
    "chart": '<path d="M3 3v18h18"/><path d="M8 17V9"/><path d="M13 17V5"/><path d="M18 17v-6"/>',
    "trend": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-7"/>',
    "sync": '<path d="M21 12a9 9 0 0 0-15-6.7L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 15 6.7L21 16"/><path d="M21 21v-5h-5"/>',
    "quality": '<path d="M6 3h12l4 6-10 12L2 9l4-6Z"/><path d="M2 9h20"/>',
    "bot": '<rect x="4" y="8" width="16" height="12" rx="2"/><path d="M12 2v6"/><path d="M8 13h.01"/><path d="M16 13h.01"/><path d="M9 17h6"/>',
    "map": '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z"/><path d="M9 3v15"/><path d="M15 6v15"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 0 20"/><path d="M12 2a15 15 0 0 0 0 20"/>',
    "clock": '<circle cx="12" cy="13" r="8"/><path d="M12 9v5l3 2"/><path d="M5 3 2 6"/><path d="m22 6-3-3"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "flag": '<path d="M4 22V4"/><path d="M4 4h13l-1 5 1 5H4"/>',
    "lightbulb": '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M8.2 14A6 6 0 1 1 15.8 14c-.8.7-1.3 1.6-1.5 2.6H9.7A4.8 4.8 0 0 0 8.2 14Z"/>',
    "signal": '<path d="M5 13a10 10 0 0 1 14 0"/><path d="M8.5 16.5a5 5 0 0 1 7 0"/><path d="M12 20h.01"/><path d="M12 4v4"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 7h18s-3 0-3-7"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    "check": '<path d="m20 6-11 11-5-5"/>',
    "file": '<path d="M9 3h6v4H9z"/><path d="M9 5H5v16h14V5h-4"/><path d="M8 12h8"/><path d="M8 16h8"/>',
    "folder": '<path d="M3 7h6l2 2h10v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/>',
    "download": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5z"/>',
    "money": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/>',
    "award": '<path d="M8 21h8"/><path d="M12 17v4"/><path d="M7 4h10v6a5 5 0 0 1-10 0V4Z"/><path d="M5 5H3v3a3 3 0 0 0 4 2.8"/><path d="M19 5h2v3a3 3 0 0 1-4 2.8"/>',
    "alert": '<path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>',
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.4 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.6 1.9Z"/>',
    "activity": '<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9"/><path d="M16 3.1a4 4 0 0 1 0 7.8"/>',
    "hot": '<path d="M8.5 14.5A3.5 3.5 0 1 0 12 11c0-2.5 1-4.7 3-6 1 2.5 3 4.4 3 8a6 6 0 1 1-12 0c0-1.4.5-2.8 1.5-3.9.1 2 .5 3.6 1 5.4Z"/>',
    "message": '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/>',
}


def _svg_for_icon(icon):
    path = _ICON_SVG.get(icon)
    if not path:
        return f"{icon} " if icon else ""
    return (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-2px;margin-right:7px;">{path}</svg>'
    )


def _card_start(title, icon=""):
    prefix = _svg_for_icon(icon)
    st.markdown(
        f'<div class="cyber-card"><div class="sv-title">{prefix}{title}</div>',
        unsafe_allow_html=True,
    )


def _card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def _truthy_col(df, col):
    if df is None or col not in df.columns:
        return pd.Series(False, index=df.index if df is not None else [])
    s = df[col]
    if s.dtype == bool:
        return s.fillna(False)
    return s.astype(str).str.lower().isin(["1", "true", "yes", "y"])


def _money_pula(value):
    value = float(value or 0)
    if value >= 1_000_000:
        return f"P{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"P{value / 1_000:.0f}K"
    return f"P{value:,.0f}"


def _summary_table(rows):
    body = "".join(
        f'<tr><td>{label}</td><td>{value}</td></tr>'
        for label, value in rows
    )
    return f'<table class="summary-stat-table"><tbody>{body}</tbody></table>'


def _sales_summary_statistics(df):
    _card_start("Summary Statistics", "chart")
    work = df if df is not None and not df.empty else pd.DataFrame()
    human = work[~_truthy_col(work, "is_bot")] if not work.empty and "is_bot" in work.columns else work
    potential = int(_truthy_col(human, "potential_customer_signal").sum()) if not human.empty else 0
    demos = int(_truthy_col(human, "has_demo_request").sum()) if not human.empty else 0
    opportunity = pd.to_numeric(human.get("estimated_deal_value", pd.Series(dtype="float64")), errors="coerce").fillna(0).sum()
    top_market = human["country"].dropna().astype(str).value_counts().index[0] if not human.empty and "country" in human.columns and not human["country"].dropna().empty else "--"
    rows = [
        ("Filtered rows", f"{len(work):,}"),
        ("Human rows", f"{len(human):,}"),
        ("Potential customers", f"{potential:,}"),
        ("Demo requests", f"{demos:,}"),
        ("Opportunity value", _money_pula(opportunity)),
        ("Top market", top_market),
    ]
    st.markdown(_summary_table(rows), unsafe_allow_html=True)
    _card_end()


def _pill(stage):
    cls_map = {
        "Engaged":  "stage-pill-engaged",
        "Qualified": "stage-pill-qualified",
        "Proposal": "stage-pill-proposal",
        "Won":      "stage-pill-won",
        "Risk":     "stage-pill-risk",
    }
    cls = cls_map.get(stage, "stage-pill-engaged")
    return f'<span class="stage-pill {cls}">{stage}</span>'


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SALES DRAWER CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

def build_sales_insights(df):
    """Derive insight values from filtered df."""
    try:
        if df is not None and len(df) > 0:
            human = df[~df["is_bot"]].copy() if "is_bot" in df.columns else df.copy()
        else:
            human = pd.DataFrame()

        # Priority market
        if "country" in human.columns and len(human) > 0:
            if "potential_customer_signal" in human.columns:
                priority_market = human.groupby("country")["potential_customer_signal"].sum().idxmax()
            else:
                priority_market = human["country"].value_counts().index[0]
        else:
            priority_market = "South Africa"

        # Risk level
        if "risk_level" in human.columns and len(human) > 0:
            risk_counts = human["risk_level"].value_counts()
            high_pct = risk_counts.get("High", 0) / len(human)
            risk_level = "High" if high_pct > 0.15 else "Medium" if high_pct > 0.05 else "Low"
        else:
            risk_level = "Low"

        risk_color = {"Low":"#76FF36","Medium":"#FFD84A","High":"#F87171"}.get(risk_level, "#76FF36")

        # Top service
        if "service_name" in human.columns and len(human) > 0:
            top_service = human["service_name"].value_counts().index[0]
        else:
            top_service = "AI Solutions"

        # Conversion rate
        if "potential_customer_signal" in human.columns and len(human) > 0:
            conv = round(float(human["potential_customer_signal"].mean()) * 100, 1)
        else:
            conv = 24.9

        return {
            "priority_market": priority_market,
            "top_service": top_service,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "conv_rate": conv,
            "action": f"Focus on {top_service} in {priority_market} - highest conversion opportunity."
        }
    except Exception:
        return {"priority_market":"South Africa","top_service":"AI Solutions",
                "risk_level":"Low","risk_color":"#76FF36","conv_rate":24.9,
                "action":"Scale outreach in South Africa and Zambia."}


def render_sales_drawer() -> str:
    """Returns HTML string for the 3 insight cards. Reads df from session state."""
    df = st.session_state.get("_sales_df_cache")
    ins = build_sales_insights(df) if df is not None else build_sales_insights(None)

    _ISO = {"South Africa":"za","Zambia":"zm","Mozambique":"mz","Botswana":"bw","Angola":"ao",
            "Zimbabwe":"zw","Namibia":"na","Malawi":"mw","Democratic Republic of the Congo":"cd"}
    iso = _ISO.get(ins["priority_market"], "za")
    flag_html = f'<img src="https://flagcdn.com/20x15/{iso}.png" style="height:13px;border-radius:1px;margin-right:4px;vertical-align:middle;" />'

    return f"""
<div class="cn-card" style="margin-bottom:10px;">
  <div class="sec-label">Regional Priority</div>
  <div style="font-size:18px;font-weight:800;color:#22D3EE;margin-bottom:4px;">{flag_html}{ins["priority_market"]}</div>
  <div style="font-size:10px;color:#6B7FA3;">Largest opportunity pool</div>
  <div style="font-size:11px;color:#4ADE80;font-weight:600;margin-top:6px;">{ins["action"]}</div>
</div>

<div class="cn-card" style="margin-bottom:10px;">
  <div class="sec-label">Strategic Signals</div>
  <div style="font-size:11px;margin-bottom:5px;color:#F5F7FA;"><span style="color:#76FF36;">●</span> {ins["top_service"]} - <b>High Intent</b></div>
  <div style="font-size:11px;margin-bottom:5px;color:#F5F7FA;"><span style="color:#00F5D4;">●</span> Digital Transformation - <b>Accelerating</b></div>
  <div style="font-size:11px;color:#F5F7FA;"><span style="color:#FFD84A;">●</span> Budget Confidence - <b>Positive</b></div>
</div>

<div class="cn-card">
  <div class="sec-label">Sales Risk Outlook</div>
  <div style="font-size:28px;font-weight:800;color:{ins["risk_color"]};text-align:center;padding:6px 0;
    text-shadow:0 0 20px {ins["risk_color"]}44;">{ins["risk_level"].upper()}</div>
  <div style="font-size:10px;color:#6B7FA3;text-align:center;">Conversion rate: {ins["conv_rate"]}%</div>
</div>"""


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ANALYTICS TAB
# ═══════════════════════════════════════════════════════════════════════════════

# ── A. Funnel by Market ──────────────────────────────────────────────────────
def _funnel_by_market():
    countries = ["South Africa", "Zambia", "Mozambique", "Botswana", "Angola", "DRC"]
    awareness = [7600, 3000, 2400, 1600, 1200, 640]
    engaged   = [3200, 1260, 1010, 670, 504, 269]
    qualified = [1248, 491, 394, 261, 196, 104]
    proposal  = [512,  201, 161, 107, 80,  42]
    won       = [198,   78,  63,  42, 32,  16]

    stages = [
        ("Awareness", awareness, _CYAN,   "rgba(34,211,238,0.7)"),
        ("Engaged",   engaged,   _TEAL,   "rgba(20,184,166,0.7)"),
        ("Qualified", qualified, _YELLOW, "rgba(255,216,74,0.7)"),
        ("Proposal",  proposal,  _ORANGE, "rgba(245,158,11,0.7)"),
        ("Won",       won,       _GREEN,  "rgba(124,255,79,0.7)"),
    ]
    conv_rates = [w / a * 100 for w, a in zip(won, awareness)]
    target = 3.0

    fig = go.Figure()
    for name, vals, color, fill_color in stages:
        fig.add_trace(go.Bar(
            name=name,
            y=countries,
            x=vals,
            orientation="h",
            marker_color=fill_color,
            hovertemplate=(
                "<b>%{y}</b><br>"
                f"Stage: {name}<br>"
                "Count: %{x:,}<extra></extra>"
            ),
        ))

    _chart_layout(fig, 320)
    fig.update_layout(
        barmode="stack",
        margin=dict(l=104, r=22, t=18, b=64),
        xaxis_title="Visits / opportunities",
        yaxis=dict(autorange="reversed", tickfont=dict(size=10, color="#CBD5E1"), automargin=True),
    )

    _card_start("Funnel by Market", "chart")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    avg_conv = sum(conv_rates) / len(conv_rates)
    gap = avg_conv - target
    gap_color = _GREEN if gap >= 0 else _RED
    gap_sign = "+" if gap >= 0 else ""
    st.markdown(
        f'<div style="font-size:10px;color:#8A98A6;margin-top:4px;">'
        f'Overall Conv: <b style="color:{_CYAN};">{avg_conv:.1f}%</b> &nbsp; - &nbsp; '
        f'Target: <b style="color:{_PURPLE};">3.0%</b> &nbsp; - &nbsp; '
        f'Gap: <b style="color:{gap_color};">{gap_sign}{gap:.1f} pts</b></div>',
        unsafe_allow_html=True,
    )
    _card_end()


# ── B. Funnel by Service ─────────────────────────────────────────────────────
def _funnel_by_service():
    services = ["Strategic Hub", "High Growth", "Emerging", "Core Market", "Stable"]
    conv     = [3.8, 3.2, 2.4, 2.1, 1.8]
    colors   = ["rgba(20,184,166,0.75)", "rgba(255,216,74,0.75)",
                "rgba(124,255,79,0.75)", "rgba(34,211,238,0.75)", "rgba(138,152,166,0.75)"]
    target   = 3.0

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=services,
        x=conv,
        orientation="h",
        marker_color=colors,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Conv Rate: %{x:.1f}%<br>"
            f"Target: {target}%<br>"
            "vs Target: %{{customdata:.1f}} pts<extra></extra>"
        ),
        customdata=[c - target for c in conv],
    ))
    fig.add_vline(x=target, line_dash="dash", line_color=_PURPLE, line_width=1.5,
                  annotation_text="Target 3.0%", annotation_font_color=_PURPLE,
                  annotation_font_size=9)
    _chart_layout(fig, 300)
    fig.update_layout(
        margin=dict(l=104, r=44, t=18, b=50),
        xaxis_title="Conversion rate %",
        yaxis=dict(autorange="reversed", tickfont=dict(size=10, color="#CBD5E1"), automargin=True),
        showlegend=False,
    )
    fig.add_annotation(x=conv[0], y=services[0], text="Best top", showarrow=False,
                       font=dict(color=_GREEN, size=9), xanchor="left", xshift=6)

    _card_start("Funnel by Service", "chart")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


# ── C. Repeat Visitor Conversion ─────────────────────────────────────────────
def _repeat_visitor_conv():
    months = ["Jan", "Feb", "Mar", "Apr"]
    new_vis    = [2.0, 2.2, 2.1, 2.4]
    repeat_vis = [3.8, 4.2, 4.5, 4.8]
    target     = [3.5, 3.5, 3.5, 3.5]
    prev_month = [3.4, 3.9, 4.1, 4.4]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=new_vis, name="New Visitors",
        line=dict(color=_GRAY, width=2), mode="lines+markers",
        marker=dict(size=6, color=_GRAY, line=dict(color="rgba(255,255,255,0.2)", width=1)),
        fill="tozeroy", fillcolor="rgba(138,152,166,0.04)",
        hovertemplate="New: <b>%{y:.1f}%</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=months, y=repeat_vis, name="Repeat Visitors",
        line=dict(color=_CYAN, width=2.5), mode="lines+markers",
        marker=dict(size=7, color=_CYAN, line=dict(color="rgba(255,255,255,0.25)", width=1.5)),
        fill="tozeroy", fillcolor="rgba(34,211,238,0.06)",
        hovertemplate="Repeat: <b>%{y:.1f}%</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=months, y=target, name="Target",
        line=dict(color=_PURPLE, width=1.5, dash="dash"), mode="lines",
        hovertemplate="Target: <b>%{y:.1f}%</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=months, y=prev_month, name="Prev Month",
        line=dict(color="#3A4A5E", width=1.5, dash="dot"), mode="lines",
        hovertemplate="Prev: <b>%{y:.1f}%</b><extra></extra>"))

    _chart_layout(fig, h=230)
    fig.update_layout(yaxis_title="Conv Rate %")

    _card_start("Repeat Visitor Conversion", "sync")
    st.markdown(
        '<span style="background:rgba(34,211,238,0.12);color:#22D3EE;border:1px solid '
        'rgba(34,211,238,0.25);border-radius:20px;padding:2px 9px;font-size:10px;font-weight:700;">'
        'Repeat: 4.8%  -  Lift 2.4x</span>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


# ── D. Segment Quality Bubble ─────────────────────────────────────────────────
def _segment_quality_bubble():
    segments  = ["Strategic Hub", "High Growth", "Emerging", "Core Market", "Stable"]
    volumes   = [180, 232, 175, 450, 95]
    conv_r    = [22.8, 24.0, 19.0, 21.8, 18.9]
    quality   = [92, 78, 61, 47, 32]
    colors    = [_TEAL, _YELLOW, _GREEN, _CYAN, _GRAY]
    fill_c    = ["rgba(20,184,166,0.7)", "rgba(255,216,74,0.7)",
                 "rgba(124,255,79,0.7)", "rgba(34,211,238,0.7)", "rgba(138,152,166,0.7)"]

    border_colors = ["rgba(34,211,238,0.5)", "rgba(255,216,74,0.5)",
                     "rgba(124,255,79,0.5)", "rgba(20,184,166,0.5)", "rgba(138,152,166,0.4)"]
    fig = go.Figure()
    for i, (seg, vol, cr, qs, fc, bc) in enumerate(zip(segments, volumes, conv_r, quality, fill_c, border_colors)):
        fig.add_trace(go.Scatter(
            x=[vol], y=[cr],
            mode="markers+text",
            name=seg,
            text=[seg],
            textposition="top center",
            textfont=dict(color="#F8FAFC", size=9, family="Inter"),
            marker=dict(
                size=qs / 2.0,
                color=fc,
                line=dict(color=bc, width=2),
                opacity=0.88,
            ),
            hovertemplate=(
                f"<b>{seg}</b><br>"
                f"Volume: {vol:,}<br>"
                f"Conv Rate: {cr}%<br>"
                f"Quality Score: {qs}/100<extra></extra>"
            ),
        ))

    _chart_layout(fig, h=230)
    fig.update_layout(xaxis_title="Potential Customers", yaxis_title="Conversion Rate %", showlegend=False)

    _card_start("Segment Quality Bubble", "quality")
    c_left, c_right = st.columns([3, 1])
    with c_left:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    with c_right:
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        for seg, qs, col in zip(segments, quality, colors):
            bar_pct = int(qs)
            st.markdown(
                f'<div style="margin-bottom:6px;">'
                f'<div style="font-size:9px;color:#8A98A6;margin-bottom:2px;">{seg}</div>'
                f'<div style="display:flex;align-items:center;gap:6px;">'
                f'<div style="flex:1;height:5px;background:rgba(77,255,225,0.08);border-radius:3px;">'
                f'<div style="width:{bar_pct}%;height:100%;background:{col};border-radius:3px;"></div></div>'
                f'<span style="font-size:10px;color:{col};font-weight:700;width:22px;">{qs}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    _card_end()


# ── E. Sales Insight Assistant ────────────────────────────────────────────────
def _sales_insight_assistant():
    insights = [
        ("dot", "South Africa is the largest opportunity pool - 450 potential customers, P18.2M pipeline.", _GREEN),
        ("dot", "Zambia shows strong growth momentum (+31% MoM) - high-priority emerging hub.", _YELLOW),
        ("dot", "Biggest funnel drop-off: Qualified to Proposal stage (-59% fallthrough rate).", _RED),
        ("dot", "Repeat visitors convert 2.4× higher than new visitors - prioritise returning traffic.", _GREEN),
        ("lightbulb", "Recommended: Prioritise high-intent repeat visitors and accelerate proposal-stage follow-ups.", _CYAN),
    ]
    rows_html = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;'
        f'border-bottom:1px solid rgba(77,255,225,0.06);">'
        f'<span style="flex-shrink:0;color:{col};">'
        f'{f"<span style=\'display:inline-block;width:7px;height:7px;border-radius:50%;background:{col};margin-top:6px;\'></span>" if icon == "dot" else _svg_for_icon(icon)}'
        f'</span>'
        f'<span style="font-size:12px;color:#F8FAFC;line-height:1.5;">{text}</span>'
        f'</div>'
        for icon, text, col in insights
    )

    st.markdown(
        f"""
<div class="insight-card">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
    <div style="color:#22D3EE;">{_svg_for_icon("bot")}</div>
    <div>
      <div style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#22D3EE;">
        CyberNova Intelligence  -  Sales Insights
      </div>
      <div style="font-size:9px;color:#8A98A6;">Intelligence summary - Updated live</div>
    </div>
  </div>
  {rows_html}
  <div style="margin-top:12px;">
    <button style="background:linear-gradient(135deg,rgba(20,184,166,0.25),rgba(34,211,238,0.15));
      border:1px solid rgba(34,211,238,0.35);color:#22D3EE;border-radius:8px;padding:6px 16px;
      font-size:11px;font-weight:600;cursor:pointer;">Ask CyberNova to</button>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


# ── F. Mini Hotzones Map ──────────────────────────────────────────────────────
def _mini_hotzones_map():
    df_m = pd.DataFrame(MAP_NODES)
    df_m["sz"] = df_m["customers"] / 6.5

    fig = go.Figure()
    for status, grp in df_m.groupby("status"):
        hover = [
            f"<b>{r['city']}, {r['country']}</b><br>"
            f"Status: {r['status']}<br>"
            f"Potential Customers: {r['customers']}<br>"
            f"Demo Requests: {r['demos']}<br>"
            f"Conversion: {r['conv']}<br>"
            f"Revenue: {r['revenue']}"
            for _, r in grp.iterrows()
        ]
        fig.add_trace(go.Scattermap(
            lat=grp.lat, lon=grp.lon, mode="markers", name=status,
            marker=dict(size=grp["sz"], color=_COLOR_MAP[status], opacity=0.88, sizemode="area"),
            text=hover, hoverinfo="text",
        ))

    fig.update_layout(
        map=dict(style="carto-darkmatter", center=dict(lat=-20, lon=26), zoom=2.5),
        height=280,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(9,20,36,0.85)", bordercolor="rgba(77,255,225,0.18)",
                    borderwidth=1, font=dict(color="#F8FAFC", size=9), orientation="v", x=0.01, y=0.98),
    )

    _card_start("Regional Opportunity Map", "map")
    st.markdown(
        '<div style="font-size:10px;color:#8A98A6;margin-bottom:6px;">'
        'Use this map to explore where potential customers are coming from.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


# ── G. Top Service Demand ─────────────────────────────────────────────────────
def _top_service_demand():
    services = ["Strategic Hub", "High Growth", "Emerging", "Core Market", "Stable"]
    counts   = [180, 232, 175, 450, 95]
    changes  = ["+18%", "+22%", "+14%", "+22%", "+8%"]
    colors   = ["rgba(20,184,166,0.75)", "rgba(255,216,74,0.75)",
                "rgba(124,255,79,0.75)", "rgba(34,211,238,0.75)", "rgba(138,152,166,0.75)"]
    change_colors = [_GREEN, _GREEN, _GREEN, _GREEN, _YELLOW]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=services,
        x=counts,
        orientation="h",
        marker_color=colors,
        text=changes,
        textposition="outside",
        textfont=dict(color="#7CFF4F", size=9),
        hovertemplate="<b>%{y}</b><br>Potential Customers: %{x}<extra></extra>",
    ))

    _chart_layout(fig, 300)
    fig.update_layout(
        margin=dict(l=104, r=52, t=18, b=50),
        xaxis_title="Potential customers",
        yaxis=dict(autorange="reversed", tickfont=dict(size=10, color="#CBD5E1"), automargin=True),
        showlegend=False,
    )

    _card_start("Top Service Demand", "trend")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


# ── H. Customers by Country ───────────────────────────────────────────────────
def _customers_by_country():
    rows_data = [
        ("🇿🇦", "South Africa", 450, "+22%", "21.8%", "P18.2M", _GREEN),
        ("🇿🇲", "Zambia",        180, "+14%", "22.8%", "P9.5M",  _GREEN),
        ("🇲🇿", "Mozambique",    140, "+18%", "20.7%", "P7.2M",  _GREEN),
        ("🇧🇼", "Botswana",       95, "+8%",  "18.9%", "P4.8M",  _YELLOW),
        ("🇦🇴", "Angola",          72, "+31%", "19.4%", "P3.1M",  _GREEN),
        ("🇨🇩", "DRC",             38, "+9%",  "15.2%", "P1.4M",  _YELLOW),
    ]

    header = (
        '<div style="display:flex;padding:6px 10px;border-bottom:1px solid rgba(77,255,225,0.14);">'
        '<span style="flex:2;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8A98A6;">Country</span>'
        '<span style="flex:1;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8A98A6;text-align:right;">Customers</span>'
        '<span style="flex:1;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8A98A6;text-align:right;">vs 30d</span>'
        '<span style="flex:1;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8A98A6;text-align:right;">Conv Rate</span>'
        '<span style="flex:1;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8A98A6;text-align:right;">Revenue</span>'
        '</div>'
    )
    rows_html = "".join(
        f'<div class="country-row" style="padding:8px 10px;">'
        f'<span style="flex:2;font-size:12px;color:#F8FAFC;font-weight:500;">{flag} {country}</span>'
        f'<span style="flex:1;font-size:12px;color:#22D3EE;text-align:right;font-weight:600;">{cust:,}</span>'
        f'<span style="flex:1;font-size:11px;color:{chg_col};text-align:right;font-weight:600;">{chg}</span>'
        f'<span style="flex:1;font-size:12px;color:#F8FAFC;text-align:right;">{conv}</span>'
        f'<span style="flex:1;font-size:12px;color:#7CFF4F;text-align:right;font-weight:600;">{rev}</span>'
        f'</div>'
        for flag, country, cust, chg, conv, rev, chg_col in rows_data
    )

    _card_start("Potential Customers by Country", "globe")
    st.markdown(
        f'<div style="overflow-y:auto;max-height:280px;">{header}{rows_html}</div>',
        unsafe_allow_html=True,
    )
    _card_end()


# ── I. Demo Intent Heatmap ────────────────────────────────────────────────────
def _demo_intent_heatmap():
    np.random.seed(12)
    days  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = [f"{h:02d}:00" for h in range(0, 23, 2)]
    z = np.random.randint(5, 60, (7, len(hours)))
    # Peak: Tue–Thu (indices 1,2,3), 9:00–17:00 (indices 4–8)
    z[1:4, 4:9] += np.random.randint(60, 120, (3, 5))

    rev_est  = z * 0.85 + np.random.uniform(0, 5, z.shape)
    follow_up = "09:00–11:00 next business day"

    fig = go.Figure(go.Heatmap(
        z=z,
        x=hours,
        y=days,
        colorscale=[[0, "rgba(15,23,42,0.85)"], [0.42, "rgba(20,184,166,0.34)"], [1, _CYAN]],
        xgap=1,
        ygap=1,
        hovertemplate=(
            "<b>%{y} %{x}</b><br>"
            "Demo Intent Count: %{z}<br>"
            f"Recommended Follow-Up: {follow_up}<extra></extra>"
        ),
        showscale=False,
    ))

    fig.update_layout(
        height=280,
        margin=dict(l=42, r=14, t=16, b=58),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,17,24,0.44)",
        font=dict(color="#CBD5E1", size=10),
        xaxis=dict(tickangle=-45, color="#CBD5E1", tickfont=dict(size=9), automargin=True),
        yaxis=dict(color="#CBD5E1", tickfont=dict(size=10), automargin=True),
    )

    _card_start("Demo Intent by Hour", "clock")
    st.markdown(
        '<div style="font-size:9px;color:#8A98A6;margin-bottom:6px;">Peak: Tue–Thu, 09:00–17:00 &nbsp; - &nbsp; '
        'High-intent windows highlighted</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


# ── J. Conversion Rate by Stage ───────────────────────────────────────────────
def _conversion_by_stage():
    stages   = ["Awareness", "Engaged", "Qualified", "Proposal", "Won"]
    cum_conv = [100.0, 42.1, 16.4, 6.7, 2.6]
    drops    = [0, 42.1-16.4, 16.4-6.7, 6.7-2.6]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=stages, y=cum_conv,
        mode="lines+markers",
        line=dict(color=_CYAN, width=2.5),
        marker=dict(size=8, color=_CYAN, line=dict(color="#071820", width=2)),
        fill="tozeroy",
        fillcolor="rgba(34,211,238,0.06)",
        hovertemplate="<b>%{x}</b><br>Cumulative Conv: %{y:.1f}%<extra></extra>",
    ))
    # Largest drop-off annotation
    fig.add_annotation(
        x="Qualified", y=16.4,
        text="Largest Drop-Off ▼ 60%",
        showarrow=True, arrowhead=2, arrowcolor=_RED,
        font=dict(color=_RED, size=9, family="Inter"),
        ax=60, ay=-30,
    )

    _chart_layout(fig, h=240)
    fig.update_layout(yaxis_title="Cumulative Conversion %", showlegend=False)

    _card_start("Conversion Rate by Stage", "target")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown(
        '<div style="font-size:10px;color:#8A98A6;margin-top:4px;">'
        'lightbulb Opportunity: Improving QualifiedtoProposal by 10% could add ~50 additional won deals per cycle.</div>',
        unsafe_allow_html=True,
    )
    _card_end()


# ── Main analytics renderer ───────────────────────────────────────────────────
def _revenue_earned_chart(df):
    work = df if df is not None and not df.empty else pd.DataFrame()
    human = work[~_truthy_col(work, "is_bot")] if not work.empty and "is_bot" in work.columns else work
    _card_start("Revenue Earned", "money")
    if human.empty:
        st.markdown(
            '<div style="font-size:11px;color:#8A98A6;">No revenue data is available for the selected filters.</div>',
            unsafe_allow_html=True,
        )
        _card_end()
        return

    value_col = "expected_conversion_value" if "expected_conversion_value" in human.columns else "pipeline_value" if "pipeline_value" in human.columns else "estimated_deal_value"
    human = human.copy()
    human["_earned_value"] = pd.to_numeric(human.get(value_col, pd.Series(dtype="float64")), errors="coerce").fillna(0)
    if "service_name" in human.columns:
        earned = human.groupby("service_name")["_earned_value"].sum().sort_values(ascending=False).head(7)
    else:
        earned = pd.Series({"Revenue": human["_earned_value"].sum()})

    fig = go.Figure(go.Bar(
        x=(earned.values / 1_000_000),
        y=earned.index.astype(str),
        orientation="h",
        marker=dict(color="#22D3EE", line=dict(color="rgba(255,255,255,.16)", width=1)),
        hovertemplate="<b>%{y}</b><br>Revenue earned: P%{x:.2f}M<extra></extra>",
    ))
    _chart_layout(fig, h=245)
    fig.update_layout(
        xaxis_title="Revenue earned (Pula M)",
        yaxis=dict(autorange="reversed", color="#CBD5E1", tickfont=dict(size=10), automargin=True),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown(
        f'<div style="font-size:10px;color:#8A98A6;margin-top:4px;">Based on <b>{value_col}</b>; values are modelled BI revenue evidence.</div>',
        unsafe_allow_html=True,
    )
    _card_end()


def render_sales_analytics(df):
    inject_sales_css()

    with st.container(key="sales_analytics_scope"):
        c1, c2 = st.columns(2, gap="medium")
        with c1: _funnel_by_market()
        with c2: _funnel_by_service()

        c1, c2 = st.columns(2, gap="medium")
        with c1: _repeat_visitor_conv()
        with c2: _segment_quality_bubble()

        c1, c2 = st.columns([1.15, 1], gap="medium")
        with c1: _sales_insight_assistant()
        with c2: _mini_hotzones_map()

        c1, c2, c3 = st.columns([1.05, 1, 1], gap="medium")
        with c1: _top_service_demand()
        with c2: _demo_intent_heatmap()
        with c3: _conversion_by_stage()

        c1, c2 = st.columns([1.05, 1], gap="medium")
        with c1: _revenue_earned_chart(df)
        with c2: _customers_by_country()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FORECASTING TAB
# ═══════════════════════════════════════════════════════════════════════════════

def _forecast_kpis():
    kpis = [
        ("Customers Forecast", "1,642", "vs current 1,248", "+ 31.6%", "up", _PURPLE),
        ("Demo Requests Forecast", "412", "vs current 312", "+ 32.1%", "up", _CYAN),
        ("Expected Conversions", "98", "next 30 days", "+ 28.9%", "up", _GREEN),
        ("Forecasted Revenue", "P2.86M", "vs current P2.24M", "+ 27.7%", "up", _TEAL),
        ("Confidence Level", "76%", "medium-high accuracy", "Medium-High", "watch", _YELLOW),
    ]
    delta_cls = {"up": "kpi-delta-up", "watch": "kpi-delta-watch", "down": "kpi-delta-down"}
    cols = st.columns(5, gap="small")
    for col, (lbl, val, sub, chg, cls, accent) in zip(cols, kpis):
        with col:
            _delta_cls = delta_cls.get(cls, "kpi-delta-up")
            delta = (
                f'<div class="{_delta_cls}" style="margin-bottom:6px;">{chg}</div>'
                if chg else ""
            )
            st.markdown(
                f'<div class="sv-kpi-card">'
                f'<div class="kpi-label">{lbl}</div>'
                f'<div class="kpi-value" style="color:{accent};font-size:1.7rem;">{val}</div>'
                f'{delta}'
                f'<div style="font-size:10px;color:#8A98A6;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _customer_forecast_30d():
    np.random.seed(9)
    days_hist = list(range(-30, 1))
    days_fwd  = list(range(0, 31))

    act_vals  = [1100 + i * 4.9 + np.random.randint(-15, 15) for i in range(31)]
    fwd_base  = act_vals[-1]
    fwd_vals  = [fwd_base + i * 5.2 for i in range(31)]
    upper_b   = [v + 55 + i * 0.8 for i, v in enumerate(fwd_vals)]
    lower_b   = [v - 55 - i * 0.8 for i, v in enumerate(fwd_vals)]
    target_v  = [1350 + i * 4 for i in range(31)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days_hist, y=act_vals, name="Actual",
        line=dict(color=_CYAN, width=2.5), mode="lines",
        hovertemplate="Day %{x}<br>Actual: %{y:,}<extra></extra>"))
    fig.add_trace(go.Scatter(x=days_fwd, y=fwd_vals, name="Forecast",
        line=dict(color=_CYAN, width=2, dash="dash"), mode="lines",
        hovertemplate="Day %{x}<br>Forecast: %{y:,}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=days_fwd + days_fwd[::-1],
        y=upper_b + lower_b[::-1],
        fill="toself", fillcolor="rgba(20,184,166,0.08)",
        line=dict(width=0), name="Confidence Band",
    ))
    fig.add_trace(go.Scatter(x=days_fwd, y=target_v, name="Target",
        line=dict(color=_PURPLE, width=1.5, dash="dash"), mode="lines",
        hovertemplate="Day %{x}<br>Target: %{y:,}<extra></extra>"))
    fig.add_vline(x=0, line_color=_ORANGE, line_width=1.5,
                  annotation_text="Today", annotation_font_color=_ORANGE, annotation_font_size=9)

    _chart_layout(fig, h=260)
    fig.update_layout(yaxis_title="Potential Customers")

    _card_start("30-Day Customer Forecast", "trend")
    st.markdown(
        '<div style="font-size:9px;color:#FFD84A;margin-bottom:6px;">'
        'alert Rule-based linear forecast, not predictive AI.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


def _demo_request_forecast():
    np.random.seed(7)
    days_hist = list(range(-30, 1))
    days_fwd  = list(range(0, 31))

    act_vals  = [240 + i * 2.4 + np.random.randint(-8, 8) for i in range(31)]
    fwd_base  = act_vals[-1]
    fwd_vals  = [fwd_base + i * 2.6 for i in range(31)]
    upper_b   = [v + 22 + i * 0.3 for i, v in enumerate(fwd_vals)]
    lower_b   = [v - 22 - i * 0.3 for i, v in enumerate(fwd_vals)]
    target_v  = [290 + i * 2.8 for i in range(31)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days_hist, y=act_vals, name="Actual",
        line=dict(color=_TEAL, width=2.5), mode="lines",
        hovertemplate="Day %{x}<br>Actual Demos: %{y:,}<extra></extra>"))
    fig.add_trace(go.Scatter(x=days_fwd, y=fwd_vals, name="Forecast",
        line=dict(color=_TEAL, width=2, dash="dash"), mode="lines",
        hovertemplate="Day %{x}<br>Forecast Demos: %{y:,}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=days_fwd + days_fwd[::-1],
        y=upper_b + lower_b[::-1],
        fill="toself", fillcolor="rgba(20,184,166,0.08)",
        line=dict(width=0), name="Confidence Band",
    ))
    fig.add_trace(go.Scatter(x=days_fwd, y=target_v, name="Target",
        line=dict(color=_PURPLE, width=1.5, dash="dash"), mode="lines",
        hovertemplate="Day %{x}<br>Target: %{y:,}<extra></extra>"))
    fig.add_vline(x=0, line_color=_ORANGE, line_width=1.5,
                  annotation_text="Today", annotation_font_color=_ORANGE, annotation_font_size=9)

    _chart_layout(fig, h=260)
    fig.update_layout(yaxis_title="Demo Requests")

    _card_start("Demo Request Forecast", "chart")
    st.markdown(
        '<div style="font-size:9px;color:#FFD84A;margin-bottom:6px;">'
        'alert Rule-based linear forecast, not predictive AI.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


def _forecast_vs_target():
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    fcast  = [1.82, 2.10, 2.38, 2.62, 2.86, 3.10]
    target = [2.00, 2.20, 2.50, 2.80, 3.20, 3.50]
    upper  = [f + 0.18 for f in fcast]
    lower  = [f - 0.18 for f in fcast]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months + months[::-1], y=upper + lower[::-1],
        fill="toself", fillcolor="rgba(20,184,166,0.08)",
        line=dict(width=0), name="Confidence Band",
    ))
    fig.add_trace(go.Scatter(x=months, y=fcast, name="Forecast",
        line=dict(color=_CYAN, width=2.5), mode="lines+markers",
        marker=dict(size=6, color=_CYAN),
        hovertemplate="<b>%{x}</b><br>Forecast: P%{y:.2f}M<extra></extra>"))
    fig.add_trace(go.Scatter(x=months, y=target, name="Target",
        line=dict(color=_PURPLE, width=1.5, dash="dash"), mode="lines",
        hovertemplate="<b>%{x}</b><br>Target: P%{y:.2f}M<extra></extra>"))

    _chart_layout(fig, h=240)
    fig.update_layout(yaxis_title="Revenue (Pula M)")

    _card_start("Forecast vs Target", "flag")
    st.markdown(
        '<div style="font-size:9px;color:#FFD84A;margin-bottom:4px;">'
        'alert Rule-based linear forecast, not predictive AI.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div style="font-size:10px;color:#8A98A6;">Forecast <b style="color:{_CYAN};">P2.86M</b></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div style="font-size:10px;color:#8A98A6;">Target <b style="color:{_PURPLE};">P3.20M</b></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div style="font-size:10px;color:#8A98A6;">Gap <b style="color:{_RED};">-P340K</b></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div style="font-size:10px;color:#8A98A6;">Confidence <b style="color:{_YELLOW};">76%</b></div>', unsafe_allow_html=True)
    _card_end()


def _whatif_analysis():
    _card_start("AI-to-Demo What-If Analysis", "bot")
    slider_pct = st.slider(
        "AI-to-Demo Conversion Rate (%)",
        min_value=15, max_value=35, value=25, step=1,
        key="whatif_slider",
    )
    total_visitors = 1642
    current_demos  = int(total_visitors * slider_pct / 100)
    conv_rate_won  = 0.238
    revenue_per    = 29285
    current_conv   = int(current_demos * conv_rate_won)
    current_rev    = current_conv * revenue_per / 1_000_000

    scenarios = [
        ("Low",     20,  "rgba(248,113,113,0.08)",  "rgba(248,113,113,0.25)", _RED),
        ("Current", slider_pct, "rgba(34,211,238,0.08)", "rgba(34,211,238,0.3)",  _CYAN),
        ("High",    30,  "rgba(124,255,79,0.08)",   "rgba(124,255,79,0.25)",  _GREEN),
    ]

    cols = st.columns(3, gap="small")
    for col, (label, pct, bg, border, color) in zip(cols, scenarios):
        demos  = int(total_visitors * pct / 100)
        convs  = int(demos * conv_rate_won)
        rev    = convs * revenue_per / 1_000_000
        gap    = rev - 3.20
        gap_s  = f"{'+'if gap>=0 else ''}{gap:.2f}M"
        gap_c  = _GREEN if gap >= 0 else _RED
        with col:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};border-radius:12px;'
                f'padding:10px 11px;margin-bottom:8px;min-width:0;overflow:hidden;">'
                f'<div style="font-size:10px;font-weight:700;color:{color};text-transform:uppercase;'
                f'letter-spacing:.1em;margin-bottom:8px;">{label} ({pct}%)</div>'
                f'<div style="font-size:12px;font-weight:700;color:#F8FAFC;margin-bottom:4px;">'
                f'Demos: {demos:,}</div>'
                f'<div style="font-size:12px;font-weight:700;color:#F8FAFC;margin-bottom:4px;">'
                f'Conversions: {convs}</div>'
                f'<div style="font-size:13px;font-weight:800;color:{color};margin-bottom:4px;">'
                f'Revenue: P{rev:.2f}M</div>'
                f'<div style="font-size:10px;color:{gap_c};">Gap to Target: {gap_s}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    _card_end()


def _readiness_checklist():
    items = [
        ("Done", "Increase follow-up cadence", "done",        _GREEN),
        ("Done", "Enable industry-specific playbooks", "done", _GREEN),
        ("○", "Prioritise enterprise accounts", "in-progress", _YELLOW),
        ("○", "Upskill SDRs on demo conversion", "in-progress", _YELLOW),
        ("○", "Launch Zambia expansion campaign", "planned",  _GRAY),
    ]
    badge_map = {
        "done":        (f"background:rgba(124,255,79,0.12);color:{_GREEN};border:1px solid rgba(124,255,79,0.25);", "Done"),
        "in-progress": (f"background:rgba(255,216,74,0.12);color:{_YELLOW};border:1px solid rgba(255,216,74,0.25);", "In Progress"),
        "planned":     (f"background:rgba(138,152,166,0.12);color:{_GRAY};border:1px solid rgba(138,152,166,0.2);", "Planned"),
    }

    rows_html = ""
    for icon, text, status, color in items:
        badge_style, badge_label = badge_map[status]
        rows_html += (
            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;'
            f'border-bottom:1px solid rgba(77,255,225,0.06);">'
            f'<span style="font-size:14px;color:{color};font-weight:700;flex-shrink:0;">{icon}</span>'
            f'<span style="flex:1;font-size:12px;color:#F8FAFC;">{text}</span>'
            f'<span style="font-size:9px;font-weight:600;padding:2px 7px;border-radius:20px;{badge_style}">{badge_label}</span>'
            f'</div>'
        )

    _card_start("Sales Readiness Recommendations", "lightbulb")
    st.markdown(rows_html, unsafe_allow_html=True)
    _card_end()


def _forecast_confidence_gauge():
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=76,
        title={"text": "Confidence Level", "font": {"color": "#8A98A6", "size": 11}},
        number={"suffix": "%", "font": {"color": _YELLOW, "size": 28}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#8A98A6", "tickfont": {"size": 9}},
            "bar": {"color": _CYAN, "thickness": 0.28},
            "bgcolor": "rgba(7,16,28,0.6)",
            "bordercolor": "rgba(77,255,225,0.14)",
            "steps": [
                {"range": [0, 40],  "color": "rgba(248,113,113,0.15)"},
                {"range": [40, 70], "color": "rgba(255,216,74,0.12)"},
                {"range": [70, 100],"color": "rgba(124,255,79,0.10)"},
            ],
            "threshold": {"line": {"color": _PURPLE, "width": 2}, "thickness": 0.75, "value": 80},
        },
    ))
    fig.update_layout(
        height=250,
        margin=dict(l=18, r=18, t=42, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", size=11),
    )

    _card_start("Forecast Confidence", "target")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown(
        f'<div style="text-align:center;font-size:11px;color:{_YELLOW};font-weight:600;">Medium-High</div>'
        f'<div style="text-align:center;font-size:10px;color:#8A98A6;">Based on historical accuracy</div>',
        unsafe_allow_html=True,
    )
    _card_end()


def _market_outlook():
    markets = [
        ("🇿🇦", "South Africa", "High Growth",  "Invest",  _GREEN),
        ("🇿🇲", "Zambia",        "High Growth",  "Invest",  _GREEN),
        ("🇧🇼", "Botswana",       "Stable",       "Monitor", _YELLOW),
        ("🇲🇿", "Mozambique",    "Emerging",     "Watch",   _ORANGE),
    ]
    status_bg = {"Invest": "rgba(124,255,79,0.08)", "Monitor": "rgba(255,216,74,0.08)", "Watch": "rgba(245,158,11,0.08)"}

    _card_start("Market Outlook", "map")
    for flag, country, status, action, color in markets:
        _bg = status_bg.get(action, "rgba(8,22,28,0.5)")
        st.markdown(
            f'<div style="background:{_bg};'
            f'border:1px solid rgba(77,255,225,0.1);border-left:3px solid {color};'
            f'border-radius:10px;padding:10px 14px;margin-bottom:8px;'
            f'display:flex;align-items:center;justify-content:space-between;">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span style="font-size:16px;">{flag}</span>'
            f'<div><div style="font-size:12px;font-weight:600;color:#F8FAFC;">{country}</div>'
            f'<div style="font-size:10px;color:#8A98A6;">{status}</div></div>'
            f'</div>'
            f'<span style="font-size:10px;font-weight:700;color:{color};padding:2px 8px;'
            f'background:rgba(0,0,0,0.2);border-radius:20px;">{action}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    _card_end()


def _forecast_signals():
    signals = [
        ("trend", "Rising website visits",       "Positive",    _GREEN),
        ("target", "Product page engagement",      "Positive",    _GREEN),
        ("hot", "Intent signals increasing",    "Positive",    _GREEN),
        ("message", "Competitive mentions",         "Low & Stable", _YELLOW),
    ]

    _card_start("Forecast Signals", "signal")
    for icon, label, status, color in signals:
        st.markdown(
            f'<div class="forecast-signal-card">'
            f'<span style="font-size:16px;">{icon}</span>'
            f'<div style="flex:1;"><div style="font-size:12px;color:#F8FAFC;">{label}</div></div>'
            f'<span style="font-size:10px;font-weight:700;color:{color};padding:2px 8px;'
            f'background:rgba(0,0,0,0.2);border-radius:20px;">{status}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    _card_end()


def _alert_center_risk():
    alerts = [
        ("Zambia demo conversion below forecast",     "High priority",   "high"),
        ("Large opportunity aging (>21 days unactioned)", "Medium priority", "warn"),
    ]

    _card_start("Alert Center + Risk Gauge", "bell")
    for msg, priority, cls in alerts:
        p_color = _RED if cls == "high" else _YELLOW
        st.markdown(
            f'<div class="alert-item {"" if cls=="high" else "warn"}">'
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<span style="color:{p_color};">{_svg_for_icon("alert")}</span>'
            f'<span style="flex:1;font-size:12px;">{msg}</span>'
            f'<span style="font-size:9px;font-weight:700;color:{p_color};'
            f'padding:2px 7px;border-radius:20px;background:rgba(0,0,0,0.2);">{priority}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # Risk gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=22,
        title={"text": "Risk Score", "font": {"color": "#8A98A6", "size": 10}},
        number={"font": {"color": _GREEN, "size": 24}},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"size": 8}, "tickcolor": "#8A98A6"},
            "bar": {"color": _GREEN, "thickness": 0.28},
            "bgcolor": "rgba(7,16,28,0.6)",
            "bordercolor": "rgba(77,255,225,0.14)",
            "steps": [
                {"range": [0, 33],  "color": "rgba(124,255,79,0.12)"},
                {"range": [33, 66], "color": "rgba(255,216,74,0.1)"},
                {"range": [66, 100],"color": "rgba(248,113,113,0.1)"},
            ],
        },
    ))
    fig.update_layout(
        height=160,
        margin=dict(l=10, r=10, t=20, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8A98A6", size=9),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown(
        f'<div style="text-align:center;font-size:11px;color:{_GREEN};font-weight:700;">LOW RISK</div>',
        unsafe_allow_html=True,
    )
    _card_end()


def render_sales_forecasting(df):
    inject_sales_css()

    with st.container(key="sales_forecasting_scope"):
        _forecast_kpis()
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2, gap="medium")
        with c1: _customer_forecast_30d()
        with c2: _demo_request_forecast()

        _whatif_analysis()

        c1, c2 = st.columns([1.05, 1], gap="medium")
        with c1: _forecast_vs_target()
        with c2: _forecast_confidence_gauge()

        c1, c2 = st.columns([1, 1], gap="medium")
        with c1: _readiness_checklist()
        with c2: _forecast_signals()

        c1, c2 = st.columns([1, 1], gap="medium")
        with c1: _market_outlook()
        with c2: _alert_center_risk()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DATA & EXPORT TAB
# ═══════════════════════════════════════════════════════════════════════════════

def _action_queue():
    actions = [
        ("bell", "Follow up",       "🇦🇴 Luanda, Angola",      "High",   "Today",     "Alex M.",   "P85K"),
        ("file", "Qualify",         "🇿🇲 Lusaka, Zambia",       "High",   "Tomorrow",  "Sarah K.",  "P120K"),
        ("sync", "Re-engage",       "🇳🇦 Windhoek, Namibia",    "Med",    "May 30",    "Alex M.",   "P42K"),
        ("file", "Prepare proposal","🇿🇦 Durban, S. Africa",     "High",   "May 31",    "James O.",  "P200K"),
        ("phone", "Intro call",      "🇿🇦 Cape Town, S. Africa",  "Med",    "Jun 1",     "Alex M.",   "P95K"),
    ]
    priority_html = {
        "High": f'<span style="background:rgba(248,113,113,0.12);color:{_RED};border:1px solid rgba(248,113,113,0.25);border-radius:20px;padding:2px 7px;font-size:9px;font-weight:700;">High</span>',
        "Med":  f'<span style="background:rgba(255,216,74,0.12);color:{_YELLOW};border:1px solid rgba(255,216,74,0.25);border-radius:20px;padding:2px 7px;font-size:9px;font-weight:700;">Med</span>',
    }

    header = (
        '<div style="display:flex;padding:6px 4px;border-bottom:1px solid rgba(77,255,225,0.12);margin-bottom:4px;">'
        '<span style="flex:0.4;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Icon</span>'
        '<span style="flex:1.2;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Action</span>'
        '<span style="flex:1.4;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Market</span>'
        '<span style="flex:0.7;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Priority</span>'
        '<span style="flex:0.8;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Due</span>'
        '<span style="flex:0.8;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Owner</span>'
        '<span style="flex:0.8;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;text-align:right;">Value</span>'
        '</div>'
    )
    rows_html = "".join(
        f'<div style="display:flex;align-items:center;padding:8px 4px;'
        f'border-bottom:1px solid rgba(77,255,225,0.05);">'
        f'<span style="flex:0.4;color:#8A98A6;">{_svg_for_icon(icon)}</span>'
        f'<span style="flex:1.2;font-size:11px;color:#F8FAFC;font-weight:500;">{action}</span>'
        f'<span style="flex:1.4;font-size:11px;color:#8A98A6;">{market}</span>'
        f'<span style="flex:0.7;">{priority_html.get(prio, prio)}</span>'
        f'<span style="flex:0.8;font-size:11px;color:#8A98A6;">{due}</span>'
        f'<span style="flex:0.8;font-size:11px;color:#22D3EE;">{owner}</span>'
        f'<span style="flex:0.8;font-size:11px;color:{_GREEN};font-weight:600;text-align:right;">{val}</span>'
        f'</div>'
        for icon, action, market, prio, due, owner, val in actions
    )

    _card_start("Sales Action Queue", "check")
    st.markdown(f"<div>{header}{rows_html}</div>", unsafe_allow_html=True)
    _card_end()


def _customers_table():
    customers = [
        ("Lusaka Telecom Ltd",         "Zambia",       "Strategic Hub",  "Qualified", 88, "P142K", "2h ago",  "Sarah K."),
        ("Cape Town Digital Co.",      "South Africa", "Core Market",    "Proposal",  82, "P210K", "1d ago",  "James O."),
        ("Maputo Industries",          "Mozambique",   "Strategic Hub",  "Engaged",   74, "P95K",  "3h ago",  "Alex M."),
        ("Gaborone FinServ",           "Botswana",     "Stable",         "Qualified", 71, "P88K",  "2d ago",  "Sarah K."),
        ("Luanda Solutions Ltd",       "Angola",       "Emerging",       "Proposal",  79, "P175K", "5h ago",  "James O."),
        ("Harare Cloud Systems",       "Zimbabwe",     "High Growth",    "Risk",      45, "P62K",  "7d ago",  "Alex M."),
        ("Windhoek Data Group",        "Namibia",      "Emerging",       "Engaged",   66, "P54K",  "4h ago",  "Sarah K."),
        ("Durban Enterprise Hub",      "South Africa", "Core Market",    "Won",       95, "P320K", "1d ago",  "James O."),
        ("Lilongwe Agri Connect",      "Malawi",       "Emerging",       "Engaged",   58, "P41K",  "6h ago",  "Alex M."),
        ("Johannesburg AI Ventures",   "South Africa", "High Growth",    "Proposal",  86, "P265K", "2d ago",  "Sarah K."),
    ]

    header = (
        '<div style="display:flex;padding:6px 8px;border-bottom:1px solid rgba(77,255,225,0.12);">'
        '<span style="flex:1.8;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Customer</span>'
        '<span style="flex:1;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Region</span>'
        '<span style="flex:0.9;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Hub</span>'
        '<span style="flex:0.9;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Stage</span>'
        '<span style="flex:0.5;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;text-align:right;">Score</span>'
        '<span style="flex:0.7;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;text-align:right;">Revenue</span>'
        '<span style="flex:0.7;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Activity</span>'
        '<span style="flex:0.7;font-size:8px;color:#8A98A6;font-weight:700;text-transform:uppercase;letter-spacing:.1em;">Owner</span>'
        '</div>'
    )
    rows_html = "".join(
        f'<div style="display:flex;align-items:center;padding:8px 8px;'
        f'border-bottom:1px solid rgba(77,255,225,0.05);transition:background .15s;" '
        f'onmouseover="this.style.background=\'rgba(20,184,166,0.06)\'" '
        f'onmouseout="this.style.background=\'transparent\'">'
        f'<span style="flex:1.8;font-size:11px;color:#F8FAFC;font-weight:500;">{name}</span>'
        f'<span style="flex:1;font-size:11px;color:#8A98A6;">{region}</span>'
        f'<span style="flex:0.9;font-size:11px;color:#8A98A6;">{hub}</span>'
        f'<span style="flex:0.9;">{_pill(stage)}</span>'
        f'<span style="flex:0.5;font-size:11px;color:{_score_color(score)};font-weight:600;text-align:right;">{score}</span>'
        f'<span style="flex:0.7;font-size:11px;color:{_GREEN};font-weight:600;text-align:right;">{rev}</span>'
        f'<span style="flex:0.7;font-size:10px;color:#8A98A6;">{activity}</span>'
        f'<span style="flex:0.7;font-size:11px;color:{_CYAN};">{owner}</span>'
        f'</div>'
        for name, region, hub, stage, score, rev, activity, owner in customers
    )

    _card_start("Potential Customers Table", "file")
    st.markdown(
        f'<div style="font-size:10px;color:#8A98A6;margin-bottom:8px;">'
        f'Use market filter (right panel) to narrow results. Showing top 10 of 1,248 records.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="overflow-x:auto;overflow-y:auto;max-height:320px;border:1px solid rgba(77,255,225,0.08);border-radius:10px;">'
        f'{header}{rows_html}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:10px;color:#8A98A6;margin-top:6px;text-align:right;">'
        'Page 1 of 5  -  1,248 records</div>',
        unsafe_allow_html=True,
    )
    _card_end()


def _score_color(score: int) -> str:
    if score >= 80: return _GREEN
    if score >= 60: return _YELLOW
    return _RED


def _evidence_snapshot():
    metrics = [
        ("money", "Total Potential Revenue",   "P82.6M", _GREEN),
        ("users", "Potential Customers",       "1,248",  _CYAN),
        ("🆕", "New Potential Customers",   "312",    _TEAL),
        ("chart", "Avg Potential Revenue",     "P66.3K", _YELLOW),
        ("activity", "Avg Engagement Score",      "74/100", _PURPLE),
    ]

    rows_html = "".join(
        f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;'
        f'border-bottom:1px solid rgba(77,255,225,0.06);">'
        f'<span style="font-size:16px;">{icon}</span>'
        f'<span style="flex:1;font-size:11px;color:#8A98A6;">{label}</span>'
        f'<span style="font-size:14px;font-weight:700;color:{color};">{val}</span>'
        f'</div>'
        for icon, label, val, color in metrics
    )

    health_pct = 74
    _card_start("Evidence Snapshot", "folder")
    st.markdown(rows_html, unsafe_allow_html=True)
    st.markdown(
        f'<div style="margin-top:12px;">'
        f'<div style="font-size:10px;color:#8A98A6;margin-bottom:4px;">Pipeline Health</div>'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<div style="flex:1;height:8px;background:rgba(77,255,225,0.08);border-radius:4px;">'
        f'<div style="width:{health_pct}%;height:100%;background:{_GREEN};border-radius:4px;"></div>'
        f'</div>'
        f'<span style="font-size:11px;font-weight:700;color:{_GREEN};">{health_pct}% Healthy</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    _card_end()


def _export_center(df):
    _card_start("Export Center", "download")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f'<div class="export-btn-card">'
            f'<div style="font-size:14px;margin-bottom:6px;color:#8A98A6;">{_svg_for_icon("file")}</div>'
            f'<div style="font-size:11px;font-weight:600;color:#F8FAFC;margin-bottom:4px;">Weekly PDF Report</div>'
            f'<div style="font-size:10px;color:#8A98A6;margin-bottom:8px;">Sales summary  -  Current week</div>'
            f'<button style="background:rgba(34,211,238,0.1);border:1px solid rgba(34,211,238,0.25);'
            f'color:{_CYAN};border-radius:6px;padding:4px 12px;font-size:10px;cursor:pointer;">Generate PDF</button>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="export-btn-card">'
            f'<div style="font-size:14px;margin-bottom:6px;color:#8A98A6;">{_svg_for_icon("file")}</div>'
            f'<div style="font-size:11px;font-weight:600;color:#F8FAFC;margin-bottom:4px;">Monthly PDF Report</div>'
            f'<div style="font-size:10px;color:#8A98A6;margin-bottom:8px;">Full monthly intelligence briefing</div>'
            f'<button style="background:rgba(34,211,238,0.1);border:1px solid rgba(34,211,238,0.25);'
            f'color:{_CYAN};border-radius:6px;padding:4px 12px;font-size:10px;cursor:pointer;">Generate PDF</button>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="export-btn-card">'
            f'<div style="font-size:14px;margin-bottom:6px;color:#8A98A6;">{_svg_for_icon("file")}</div>'
            f'<div style="font-size:11px;font-weight:600;color:#F8FAFC;margin-bottom:4px;">Pipeline Snapshot PDF</div>'
            f'<div style="font-size:10px;color:#8A98A6;margin-bottom:8px;">Current pipeline status</div>'
            f'<button style="background:rgba(34,211,238,0.1);border:1px solid rgba(34,211,238,0.25);'
            f'color:{_CYAN};border-radius:6px;padding:4px 12px;font-size:10px;cursor:pointer;">Generate PDF</button>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c2:
        # Real CSV downloads
        if df is not None:
            pc_df = df[~df["is_bot"]] if "is_bot" in df.columns else df
            st.download_button(
                label="Potential Customers CSV",
                data=pc_df.head(5000).to_csv(index=False).encode(),
                file_name="cybernova_potential_customers.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_pc_csv",
            )
            mkt = st.session_state.get("selected_market", "All")
            filtered = pc_df[pc_df["country"] == mkt] if (mkt != "All" and "country" in pc_df.columns) else pc_df
            if filtered.empty:
                filtered = pc_df
            st.download_button(
                label="Filtered Data CSV",
                data=filtered.head(5000).to_csv(index=False).encode(),
                file_name="cybernova_filtered.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_filtered_csv",
            )
        else:
            st.markdown(
                f'<div style="font-size:10px;color:{_YELLOW};padding:8px 0;">CSV export unavailable - data not loaded.</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="export-btn-card">'
            f'<div style="font-size:14px;margin-bottom:6px;">book</div>'
            f'<div style="font-size:11px;font-weight:600;color:#F8FAFC;margin-bottom:4px;">Data Dictionary</div>'
            f'<div style="font-size:10px;color:#8A98A6;margin-bottom:8px;">Field definitions & methodology</div>'
            f'<button style="background:rgba(34,211,238,0.1);border:1px solid rgba(34,211,238,0.25);'
            f'color:{_CYAN};border-radius:6px;padding:4px 12px;font-size:10px;cursor:pointer;">View Dictionary</button>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _card_end()


def _data_quality_summary():
    metrics = [
        ("Data Completeness",    95,  _GREEN,  False),
        ("Duplicate Rate",       2,   _RED,    True),
        ("Data Freshness",       98,  _GREEN,  False),
        ("Valid Emails",         96,  _GREEN,  False),
        ("Phone Verified",       89,  _YELLOW, False),
        ("Firmographic",         93,  _GREEN,  False),
        ("Engagement Coverage",  74,  _YELLOW, False),
    ]

    _card_start("Data Quality Summary", "search")
    for label, pct, color, inverse in metrics:
        disp_pct = pct if not inverse else 100 - pct
        bar_color = (_RED if inverse else color)
        # For duplicate rate: lower is better - show visually inverted
        fill = 100 - pct if inverse else pct
        note = " (lower is better)" if inverse else ""
        st.markdown(
            f'<div class="quality-bar-row">'
            f'<span style="font-size:10px;color:#8A98A6;width:160px;flex-shrink:0;">{label}{note}</span>'
            f'<div class="quality-bar-track">'
            f'<div class="quality-bar-fill" style="width:{fill}%;background:{bar_color};"></div></div>'
            f'<span style="font-size:10px;font-weight:700;color:{color};width:40px;text-align:right;">'
            f'{pct}{"%" if not inverse else "%"}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    _card_end()


def _methodology():
    _card_start("Methodology & Assumptions", "book")
    st.markdown(
        """
<div style="font-size:12px;color:#F8FAFC;line-height:1.7;">
  <div style="margin-bottom:12px;">
    <div style="font-size:10px;font-weight:700;color:#22D3EE;text-transform:uppercase;
      letter-spacing:.1em;margin-bottom:4px;">Potential Customer Scoring</div>
    <div style="color:#8A98A6;">Visitors are classified as potential customers when engagement score ≥ 60,
      3+ pages visited, and at least one intent page (AI Solutions, Cybersecurity, or demo request) is included in the session.</div>
  </div>
  <div style="margin-bottom:12px;">
    <div style="font-size:10px;font-weight:700;color:#22D3EE;text-transform:uppercase;
      letter-spacing:.1em;margin-bottom:4px;">Revenue Assumptions</div>
    <div style="color:#8A98A6;">Average deal value of P66.3K is based on segment analysis of the SADC enterprise software market. Values are indicative estimates.</div>
  </div>
  <div style="margin-bottom:12px;">
    <div style="font-size:10px;font-weight:700;color:#FFD84A;text-transform:uppercase;
      letter-spacing:.1em;margin-bottom:4px;">Data Limitation</div>
    <div style="color:#8A98A6;">This prototype uses synthetic IIS log data generated for evaluation purposes only. Not for production use.</div>
  </div>
  <div style="margin-bottom:12px;">
    <div style="font-size:10px;font-weight:700;color:#22D3EE;text-transform:uppercase;
      letter-spacing:.1em;margin-bottom:4px;">Currency</div>
    <div style="color:#8A98A6;">All revenue values are denominated in BWP.</div>
  </div>
  <div>
    <div style="font-size:10px;font-weight:700;color:#22D3EE;text-transform:uppercase;
      letter-spacing:.1em;margin-bottom:4px;">Data Refresh</div>
    <div style="color:#8A98A6;">Live pulse updates every second. Full data refresh every 2 hours.</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    _card_end()


def _revenue_by_region():
    labels = ["South Africa", "Zambia", "Mozambique", "Botswana", "Angola", "Other"]
    values = [18.2, 9.5, 7.2, 4.8, 3.1, 5.8]
    colors = [_CYAN, _TEAL, _GREEN, _YELLOW, _ORANGE, _GRAY]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        marker=dict(
            colors=[c.replace("#", "rgba(") + "0.8)" if c.startswith("#") else c for c in [
                "rgba(34,211,238,0.8)", "rgba(20,184,166,0.8)", "rgba(124,255,79,0.8)",
                "rgba(255,216,74,0.8)", "rgba(245,158,11,0.8)", "rgba(138,152,166,0.7)"]],
            line=dict(color="rgba(0,0,0,0.3)", width=1),
        ),
        textfont=dict(color="#F8FAFC", size=9),
        hovertemplate="<b>%{label}</b><br>Revenue: P%{value:.1f}M<br>Share: %{percent}<extra></extra>",
    ))
    fig.add_annotation(text="P82.6M", x=0.5, y=0.58,
                       font=dict(size=14, color="#FFFFFF", family="Inter"), showarrow=False)
    fig.add_annotation(text="Total", x=0.5, y=0.42,
                       font=dict(size=9, color="#8A98A6", family="Inter"), showarrow=False)
    fig.update_layout(
        height=290,
        margin=dict(l=8, r=8, t=16, b=54),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(7,16,28,0.72)", bordercolor="rgba(148,163,184,0.16)", borderwidth=1,
                    font=dict(color="#CBD5E1", size=10), orientation="h", y=-0.12, x=0),
    )

    _card_start("Revenue by Region", "money")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


def _new_customers_trend():
    np.random.seed(4)
    months_hist = ["Jan", "Feb", "Mar", "Apr"]
    months_fwd  = ["May", "Jun"]
    months_all  = months_hist + months_fwd

    actual  = [72, 88, 95, 110]
    target  = [80, 88, 96, 104, 112, 120]
    fcast   = [110, 128, 148]  # Apr onward
    prev_m  = [68, 82, 90, 103]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months_hist, y=actual, name="Actual",
        line=dict(color=_CYAN, width=2.5), mode="lines+markers",
        marker=dict(size=6, color=_CYAN),
        hovertemplate="<b>%{x}</b><br>Actual: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=["Apr", "May", "Jun"], y=fcast, name="Forecast",
        line=dict(color=_CYAN, width=2, dash="dash"), mode="lines+markers",
        marker=dict(size=6, color=_CYAN, symbol="diamond"),
        hovertemplate="<b>%{x}</b><br>Forecast: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=months_all, y=target, name="Target",
        line=dict(color=_PURPLE, width=1.5, dash="dash"), mode="lines",
        hovertemplate="<b>%{x}</b><br>Target: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=months_hist, y=prev_m, name="Prev Month",
        line=dict(color="#3A4A5E", width=1.5, dash="dot"), mode="lines",
        hovertemplate="<b>%{x}</b><br>Prev: %{y}<extra></extra>",
    ))
    fig.add_vrect(x0="Apr", x1="Jun", fillcolor="rgba(34,211,238,0.03)",
                  line_width=0, annotation_text="Forecast", annotation_position="top left",
                  annotation_font_color=_YELLOW, annotation_font_size=8)

    _chart_layout(fig, h=260)
    fig.update_layout(yaxis_title="New Potential Customers", xaxis_title="Month")
    st.markdown(
        '<div style="font-size:9px;color:#FFD84A;margin-bottom:4px;">'
        'alert Rule-based linear forecast, not predictive AI.</div>',
        unsafe_allow_html=True,
    )

    _card_start("New Potential Customers Trend", "trend")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


def _top_customers_revenue():
    companies = [
        ("Durban Enterprise Hub",      320, "Won"),
        ("Johannesburg AI Ventures",   265, "Proposal"),
        ("Cape Town Digital Co.",      210, "Proposal"),
        ("Lusaka Telecom Ltd",         142, "Qualified"),
        ("Cape Town CyberGroup",       138, "Won"),
        ("Luanda Solutions Ltd",       175, "Proposal"),
        ("Maputo Industries",           95, "Engaged"),
        ("Harare Cloud Systems",        62, "Risk"),
    ]
    stage_c = {
        "Won":      "rgba(34,211,238,0.7)",
        "Proposal": "rgba(245,158,11,0.7)",
        "Qualified":"rgba(124,255,79,0.7)",
        "Engaged":  "rgba(20,184,166,0.7)",
        "Risk":     "rgba(248,113,113,0.7)",
    }

    names  = [c[0] for c in companies]
    revs   = [c[1] for c in companies]
    stages = [c[2] for c in companies]
    colors = [stage_c.get(s, "rgba(138,152,166,0.7)") for s in stages]

    fig = go.Figure(go.Bar(
        y=names,
        x=revs,
        orientation="h",
        marker_color=colors,
        text=[f"P{r}K" for r in revs],
        textposition="outside",
        textfont=dict(color="#F8FAFC", size=9),
        hovertemplate="<b>%{y}</b><br>Revenue: P%{x}K<extra></extra>",
    ))
    fig.update_layout(
        height=330,
        margin=dict(l=164, r=64, t=16, b=46),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,17,24,0.44)",
        font=dict(color="#CBD5E1", size=10),
        xaxis=dict(gridcolor="rgba(148,163,184,0.10)", color="#94A3B8", title="Revenue (BWP thousands)", tickfont=dict(size=10), title_font=dict(size=10), automargin=True),
        yaxis=dict(color="#CBD5E1", tickfont=dict(size=10), automargin=True),
        showlegend=False,
    )

    _card_start("Top Potential Customers by Revenue", "award")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_end()


def _export_center(df):
    _card_start("Export Center", "file")
    filters = {
        "role": "Sales",
        "market": st.session_state.get("selected_market", "All"),
        "service": st.session_state.get("svc_filter", "All Services"),
        "segment": st.session_state.get("seg_filter", "All Segments"),
    }
    today_label = period_label(7) if _EXPORTS_OK else "current 7 days"
    month_label = period_label(30) if _EXPORTS_OK else "current 30 days"
    row_count = len(df) if df is not None else 0
    st.markdown(
        f"""
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:10px;">
  <div class="export-btn-card"><div style="font-size:10px;color:{_CYAN};font-weight:800;">Sales Pack</div><div style="font-size:18px;color:{_WHITE};font-weight:900;">{row_count:,}</div><div style="font-size:10px;color:{_GRAY};">filtered rows</div></div>
  <div class="export-btn-card"><div style="font-size:10px;color:{_CYAN};font-weight:800;">Weekly</div><div style="font-size:11px;color:{_WHITE};font-weight:700;">Last 7 Days</div><div style="font-size:9px;color:{_GRAY};">{today_label}</div></div>
  <div class="export-btn-card"><div style="font-size:10px;color:{_CYAN};font-weight:800;">Monthly</div><div style="font-size:11px;color:{_WHITE};font-weight:700;">Last 30 Days</div><div style="font-size:9px;color:{_GRAY};">{month_label}</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if _EXPORTS_OK:
            weekly_pdf = build_weekly_report_pdf("CyberNova Pulse - Sales", df, filters)
            monthly_pdf = build_monthly_report_pdf("CyberNova Pulse - Sales", df, filters)
            method_pdf = build_methodology_pdf("CyberNova Pulse - Sales")
            st.download_button(
                "Weekly PDF Report (Last 7 Days)",
                data=weekly_pdf,
                file_name="cybernova_sales_weekly_last_7_days.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="sales_weekly_pdf_real",
            )
            st.download_button(
                "Monthly PDF Report (Last 30 Days)",
                data=monthly_pdf,
                file_name="cybernova_sales_monthly_last_30_days.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="sales_monthly_pdf_real",
            )
            st.download_button(
                "Methodology PDF",
                data=method_pdf,
                file_name="cybernova_sales_methodology.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="sales_methodology_pdf_real",
            )
        else:
            st.markdown(
                f'<div style="font-size:10px;color:{_YELLOW};padding:8px 0;">PDF export module unavailable.</div>',
                unsafe_allow_html=True,
            )

    with c2:
        if df is not None and not df.empty:
            clean_df = df[~df["is_bot"]] if "is_bot" in df.columns else df
            if "potential_customer_signal" in clean_df.columns:
                signal = clean_df["potential_customer_signal"]
                if signal.dtype == bool:
                    pc_mask = signal
                else:
                    pc_mask = signal.astype(str).str.lower().isin(["1", "true", "yes", "y"])
                pc_df = clean_df[pc_mask]
            else:
                pc_df = clean_df
            mkt = st.session_state.get("selected_market", "All")
            filtered = pc_df[pc_df["country"] == mkt] if (mkt != "All" and "country" in pc_df.columns) else pc_df
            if filtered.empty:
                filtered = pc_df
            to_csv = dataframe_to_csv_bytes if _EXPORTS_OK else lambda frame: frame.to_csv(index=False).encode("utf-8")
            weekly_filtered = filter_last_n_days(filtered, 7)[0] if _EXPORTS_OK else filtered
            monthly_filtered = filter_last_n_days(filtered, 30)[0] if _EXPORTS_OK else filtered
            st.download_button(
                "Potential Customers CSV",
                data=to_csv(pc_df.head(5000)),
                file_name="cybernova_sales_potential_customers.csv",
                mime="text/csv",
                use_container_width=True,
                key="sales_pc_csv_real",
            )
            st.download_button(
                "Filtered Data CSV (Last 7 Days)",
                data=to_csv(weekly_filtered.head(5000)),
                file_name="cybernova_sales_filtered_data_last_7_days.csv",
                mime="text/csv",
                use_container_width=True,
                key="sales_filtered_csv_real",
            )
            st.download_button(
                "Filtered Data CSV (Last 30 Days)",
                data=to_csv(monthly_filtered.head(5000)),
                file_name="cybernova_sales_filtered_data_last_30_days.csv",
                mime="text/csv",
                use_container_width=True,
                key="sales_filtered_csv_30d_real",
            )
        else:
            st.markdown(
                f'<div style="font-size:10px;color:{_YELLOW};padding:8px 0;">CSV export unavailable - data not loaded.</div>',
                unsafe_allow_html=True,
            )
    _card_end()


def render_sales_data(df):
    inject_sales_css()

    with st.container(key="sales_data_scope"):
        _export_center(df)

        c1, c2 = st.columns([1.1, 1.55], gap="medium")
        with c1:
            _action_queue()
            _evidence_snapshot()
        with c2:
            _customers_table()

        c1, c2 = st.columns([1, 1.25], gap="medium")
        with c1: _sales_summary_statistics(df)
        with c2: _data_quality_summary()

        c1, c2 = st.columns([1, 1], gap="medium")
        with c1: _methodology()
        with c2: _revenue_by_region()

        c1, c2 = st.columns([1, 1.12], gap="medium")
        with c1: _new_customers_trend()
        with c2: _top_customers_revenue()
