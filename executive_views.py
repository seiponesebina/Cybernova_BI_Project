"""
executive_views.py - CyberNova BI Portal  -  Executive Dashboard
Imported by cybernovaapp.py. Provides 5 public functions:
  inject_executive_css, render_executive_drawer,
  render_executive_analytics, render_executive_forecasting, render_executive_data
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime

# ── EXPORTS (optional) ─────────────────────────────────────────────────────────
try:
    from exports import (
        build_weekly_report_pdf,
        build_monthly_report_pdf,
        dataframe_to_csv_bytes,
        build_methodology_pdf,
        filter_last_n_days,
        period_label,
    )
    _EXPORTS_OK = True
except Exception:
    _EXPORTS_OK = False

# ── COLOR CONSTANTS ────────────────────────────────────────────────────────────
_CYAN   = "#22D3EE"
_TEAL   = "#14B8A6"
_GREEN  = "#4ADE80"
_YELLOW = "#FBBF24"
_ORANGE = "#F59E0B"
_RED    = "#F87171"
_PURPLE = "#A855F7"
_GRAY   = "#6B7FA3"
_WHITE  = "#F0F4F8"
_MUTED  = "#6B7FA3"


# ── CHART HELPER ───────────────────────────────────────────────────────────────
def _cl(fig, h=210):
    """Apply consistent dark Executive chart layout."""
    fig.update_layout(
        height=h,
        margin=dict(l=50, r=26, t=24, b=70),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,17,24,0.44)",
        font=dict(color="#CBD5E1", size=11, family="Inter"),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(7,14,26,0.95)",
            bordercolor="rgba(124,110,230,0.30)",
            font=dict(color="#F0F4F8", size=11, family="Inter"),
        ),
        xaxis=dict(
            gridcolor="rgba(148,163,184,0.10)",
            color="#94A3B8",
            showgrid=True,
            zeroline=False,
            showspikes=True, spikesnap="cursor",
            spikecolor="rgba(124,110,230,0.24)", spikethickness=1,
            tickfont=dict(size=10, color="#CBD5E1"),
            title_font=dict(size=10, color="#94A3B8"),
            automargin=True,
        ),
        yaxis=dict(
            gridcolor="rgba(148,163,184,0.10)",
            color="#94A3B8",
            showgrid=True,
            zeroline=False,
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


def _card_open(title):
    """Open a cn-card div with a sec-label."""
    st.markdown(
        f'<div class="cn-card"><div class="sec-label">{title}</div>',
        unsafe_allow_html=True,
    )


def _card_close():
    st.markdown("</div>", unsafe_allow_html=True)


# ── STATUS PILL HELPER ─────────────────────────────────────────────────────────
def _truthy_col(df, col):
    if df is None or col not in df.columns:
        return pd.Series(False, index=df.index if df is not None else [])
    s = df[col]
    if s.dtype == bool:
        return s.fillna(False)
    return s.astype(str).str.lower().isin(["1", "true", "yes", "y"])


def _summary_table(rows):
    body = "".join(
        f'<tr><td>{label}</td><td>{value}</td></tr>'
        for label, value in rows
    )
    return f'<table class="summary-stat-table"><tbody>{body}</tbody></table>'


def _executive_summary_statistics(df):
    _card_open("Summary Statistics")
    work = df if df is not None and not df.empty else pd.DataFrame()
    human = work[~_truthy_col(work, "is_bot")] if not work.empty and "is_bot" in work.columns else work
    potential = int(_truthy_col(human, "potential_customer_signal").sum()) if not human.empty else 0
    ai = int(_truthy_col(human, "has_ai_interest").sum()) if "has_ai_interest" in human.columns else (
        int(human["service_name"].astype(str).str.contains("AI", case=False, na=False).sum()) if "service_name" in human.columns else 0
    )
    risk = int((pd.to_numeric(human["risk_score"], errors="coerce").fillna(0) >= 70).sum()) if "risk_score" in human.columns else (
        int(_truthy_col(human, "is_anomaly").sum()) if "is_anomaly" in human.columns else 0
    )
    active_markets = int(human["country"].nunique()) if "country" in human.columns and not human.empty else 0
    top_market = human["country"].dropna().astype(str).value_counts().index[0] if "country" in human.columns and not human["country"].dropna().empty else "--"
    rows = [
        ("Strategic rows", f"{len(work):,}"),
        ("Human signals", f"{len(human):,}"),
        ("Potential customers", f"{potential:,}"),
        ("AI traction", f"{(ai / len(human) * 100):.1f}%" if len(human) else "0.0%"),
        ("Active markets", f"{active_markets:,}"),
        ("Risk alerts", f"{risk:,}"),
        ("Top market", top_market),
    ]
    st.markdown(_summary_table(rows), unsafe_allow_html=True)
    _card_close()


_STATUS_STYLES = {
    "Above Target": f"background:rgba(74,222,128,0.12);color:{_GREEN};border:1px solid rgba(74,222,128,0.25);",
    "On Track":     f"background:rgba(34,211,238,0.12);color:{_CYAN};border:1px solid rgba(34,211,238,0.25);",
    "On Watch":     f"background:rgba(251,191,36,0.12);color:{_YELLOW};border:1px solid rgba(251,191,36,0.25);",
    "Below Target": f"background:rgba(248,113,113,0.12);color:{_RED};border:1px solid rgba(248,113,113,0.25);",
}

def _status_pill(label):
    style = _STATUS_STYLES.get(label, f"background:rgba(107,127,163,0.12);color:{_MUTED};border:1px solid rgba(107,127,163,0.2);")
    return (
        f'<span style="display:inline-block;padding:2px 9px;border-radius:20px;'
        f'font-size:10px;font-weight:700;{style}">{label}</span>'
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. CSS INJECTION - Executive-specific additions only
# ══════════════════════════════════════════════════════════════════════════════
def inject_executive_css():
    """Inject Executive-specific CSS not already in main inject_css()."""
    st.markdown("""
<style>
/* ── Executive insight card (glassmorphism, purple border) ─────────────────── */
.exec-insight-card {
  background: linear-gradient(145deg,rgba(12,4,40,0.94),rgba(8,3,28,0.90));
  border: 1px solid rgba(168,85,247,0.28);
  border-left: 3px solid #A855F7;
  border-radius: 14px;
  padding: 18px 20px;
  margin-bottom: 10px;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 0 32px rgba(168,85,247,0.08), inset 0 1px 0 rgba(168,85,247,0.06);
}
/* ── Executive KPI card (purple accent override) ─────────────────────────── */
.exec-kpi-card {
  background: linear-gradient(145deg,rgba(12,4,40,0.92),rgba(8,3,28,0.88));
  border: 1px solid rgba(168,85,247,0.18);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  box-shadow: 0 2px 16px rgba(168,85,247,0.1);
  backdrop-filter: blur(12px);
  transition: border-color .2s, transform .15s;
}
.exec-kpi-card:hover {
  border-color: rgba(168,85,247,0.45);
  transform: translateY(-1px);
}
/* ── Strategic signals metric card ─────────────────────────────────────────── */
.signal-metric-card {
  background: rgba(12,4,40,0.82);
  border: 1px solid rgba(168,85,247,0.15);
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 8px;
  transition: border-color .2s;
}
.signal-metric-card:hover {
  border-color: rgba(168,85,247,0.38);
}
/* ── Investment decision card sections ─────────────────────────────────────── */
.invest-card {
  border-left: 3px solid #4ADE80;
  background: rgba(74,222,128,0.05);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 8px;
}
.monitor-card {
  border-left: 3px solid #FBBF24;
  background: rgba(251,191,36,0.05);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 8px;
}
.review-card {
  border-left: 3px solid #F87171;
  background: rgba(248,113,113,0.05);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 8px;
}
/* ── Exec table ─────────────────────────────────────────────────────────────── */
.exec-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.exec-table th {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: #6B7FA3;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(168,85,247,0.14);
  background: rgba(8,3,28,0.92);
}
.exec-table td {
  padding: 8px 10px;
  border-bottom: 1px solid rgba(168,85,247,0.06);
  color: #F0F4F8;
  vertical-align: middle;
}
.exec-table tr:hover td {
  background: rgba(168,85,247,0.04);
}
/* ── Progress bar (exec style) ──────────────────────────────────────────────── */
.exec-progress-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.exec-progress-track {
  flex: 1;
  height: 6px;
  background: rgba(168,85,247,0.08);
  border-radius: 3px;
  overflow: hidden;
}
.exec-progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width .4s;
}
/* ── Scenario card ────────────────────────────────────────────────────────── */
.scenario-card {
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 8px;
  backdrop-filter: blur(12px);
}
.st-key-executive_analytics_scope div[data-testid="element-container"],
.st-key-executive_forecasting_scope div[data-testid="element-container"],
.st-key-executive_data_scope div[data-testid="element-container"] {
  height: auto !important;
  min-height: 0 !important;
}
.st-key-executive_analytics_scope div[data-testid="stVerticalBlock"],
.st-key-executive_forecasting_scope div[data-testid="stVerticalBlock"],
.st-key-executive_data_scope div[data-testid="stVerticalBlock"] {
  gap: 12px !important;
}
.st-key-executive_analytics_scope div[data-testid="stColumn"],
.st-key-executive_forecasting_scope div[data-testid="stColumn"],
.st-key-executive_data_scope div[data-testid="stColumn"] {
  min-width: 0 !important;
}
.st-key-executive_analytics_scope div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
.st-key-executive_forecasting_scope div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
.st-key-executive_data_scope div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
  height: auto !important;
  min-height: 0 !important;
}
.st-key-executive_analytics_scope .cn-card,
.st-key-executive_forecasting_scope .cn-card,
.st-key-executive_data_scope .cn-card,
.st-key-executive_forecasting_scope .exec-kpi-card,
.st-key-executive_analytics_scope .signal-metric-card,
.st-key-executive_forecasting_scope .scenario-card,
.st-key-executive_data_scope .exec-insight-card {
  width: 100%;
  min-width: 0;
  padding: 16px 18px;
  margin-bottom: 12px;
  overflow: visible;
  box-sizing: border-box;
}
.st-key-executive_analytics_scope div[data-testid="stPlotlyChart"],
.st-key-executive_forecasting_scope div[data-testid="stPlotlyChart"],
.st-key-executive_data_scope div[data-testid="stPlotlyChart"] {
  width: 100% !important;
  min-width: 0 !important;
  overflow: hidden !important;
}
.st-key-executive_analytics_scope .js-plotly-plot,
.st-key-executive_forecasting_scope .js-plotly-plot,
.st-key-executive_data_scope .js-plotly-plot {
  max-width: 100% !important;
}
.st-key-executive_analytics_scope [data-testid="stMarkdownContainer"],
.st-key-executive_forecasting_scope [data-testid="stMarkdownContainer"],
.st-key-executive_data_scope [data-testid="stMarkdownContainer"] {
  min-width: 0 !important;
  overflow-wrap: anywhere;
}
.st-key-executive_analytics_scope .exec-table,
.st-key-executive_forecasting_scope .exec-table,
.st-key-executive_data_scope .exec-table {
  min-width: 720px;
}
.st-key-executive_analytics_scope .cn-card:has(.exec-table),
.st-key-executive_forecasting_scope .cn-card:has(.exec-table),
.st-key-executive_data_scope .cn-card:has(.exec-table) {
  overflow-x: auto;
}
.st-key-executive_data_scope div[data-testid="stDataFrame"],
.st-key-executive_data_scope div[data-testid="stDataFrameResizable"] {
  width: 100% !important;
  min-width: 0 !important;
  overflow-x: auto !important;
}
.st-key-executive_data_scope .stDownloadButton button {
  white-space: normal !important;
  min-height: 42px;
  height: auto;
  line-height: 1.25;
  padding: 10px 12px;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 2. EXECUTIVE DRAWER - returns HTML string
# ══════════════════════════════════════════════════════════════════════════════
def render_executive_drawer() -> str:
    """Returns HTML string for the 4 executive insight cards in the right-panel drawer."""
    return """
<div class="executive-drawer-grid">
<div class="cn-card" style="margin-bottom:10px;border-color:rgba(168,85,247,0.22);">
  <div class="sec-label">Regional Priority</div>
  <div style="font-size:15px;font-weight:800;color:#A855F7;margin-bottom:4px;">South Africa + Zambia</div>
  <div style="font-size:10px;color:#6B7FA3;">Core + Strategic Hub anchors</div>
  <div style="font-size:11px;color:#4ADE80;margin-top:8px;font-weight:700;">Invest - protect lead</div>
</div>

<div class="cn-card" style="margin-bottom:10px;border-color:rgba(168,85,247,0.15);">
  <div class="sec-label">Strategic Signals</div>
  <div style="font-size:11px;margin-bottom:6px;color:#F0F4F8;">
    <span style="color:#4ADE80;">●</span>&nbsp; AI Solutions - <b>Accelerating</b>
  </div>
  <div style="font-size:11px;margin-bottom:6px;color:#F0F4F8;">
    <span style="color:#22D3EE;">●</span>&nbsp; SADC Expansion - <b>On Track</b>
  </div>
  <div style="font-size:11px;color:#F0F4F8;">
    <span style="color:#F87171;">●</span>&nbsp; Zimbabwe - <b>Monitor</b>
  </div>
</div>

<div class="cn-card" style="margin-bottom:10px;border-color:rgba(168,85,247,0.15);">
  <div class="sec-label">Risk Outlook</div>
  <div style="font-size:28px;font-weight:800;color:#FBBF24;text-align:center;padding:6px 0;
    text-shadow:0 0 20px rgba(251,191,36,0.3);">MEDIUM</div>
  <div style="font-size:10px;color:#6B7FA3;text-align:center;">3 markets need executive attention</div>
</div>

<div class="cn-card" style="border-color:rgba(168,85,247,0.2);">
  <div class="sec-label">Investment Recommendation</div>
  <div style="font-size:10px;margin-bottom:5px;">
    <span style="color:#4ADE80;font-weight:700;">Invest:</span>
    <span style="color:#F0F4F8;"> South Africa, Zambia.</span>
  </div>
  <div style="font-size:10px;margin-bottom:5px;">
    <span style="color:#FBBF24;font-weight:700;">Monitor:</span>
    <span style="color:#F0F4F8;"> Botswana, Mozambique, Namibia.</span>
  </div>
  <div style="font-size:10px;">
    <span style="color:#F87171;font-weight:700;">Review:</span>
    <span style="color:#F0F4F8;"> Angola, Malawi, DRC.</span>
  </div>
</div>
</div>
"""


# ══════════════════════════════════════════════════════════════════════════════
# 3. EXECUTIVE ANALYTICS TAB
# ══════════════════════════════════════════════════════════════════════════════

_COUNTRIES = [
    ("🇿🇦", "South Africa", 450, 488, +38,  "Above Target", "Invest"),
    ("🇿🇲", "Zambia",        150, 162, +12,  "Above Target", "Invest"),
    ("🇲🇿", "Mozambique",    120, 118,  -2,  "On Watch",     "Monitor"),
    ("🇧🇼", "Botswana",      100,  95,  -5,  "On Watch",     "Monitor"),
    ("🇦🇴", "Angola",         80,  68, -12,  "Below Target", "Review"),
    ("🇳🇦", "Namibia",        60,  58,  -2,  "On Watch",     "Monitor"),
    ("🇿🇼", "Zimbabwe",       90,  88,  -2,  "On Track",     "Maintain"),
    ("🇲🇼", "Malawi",         50,  42,  -8,  "Below Target", "Review"),
    ("🇨🇩", "DRC",            40,  30, -10,  "Below Target", "Review"),
]

_ACTION_COLORS = {
    "Invest":   _GREEN,
    "Monitor":  _YELLOW,
    "Maintain": _CYAN,
    "Review":   _RED,
}


def _regional_target_table():
    """Card 1: Regional Target Table - full width."""
    header = (
        '<table class="exec-table"><thead><tr>'
        '<th>Country</th>'
        '<th style="text-align:right;">Target</th>'
        '<th style="text-align:right;">Actual</th>'
        '<th style="text-align:right;">Gap</th>'
        '<th style="text-align:center;">Status</th>'
        '<th style="text-align:center;">Recommended Action</th>'
        '</tr></thead><tbody>'
    )
    rows = ""
    for flag, country, target, actual, gap, status, action in _COUNTRIES:
        gap_sign = "+" if gap > 0 else ""
        gap_color = _GREEN if gap > 0 else (_YELLOW if gap >= -5 else _RED)
        action_color = _ACTION_COLORS.get(action, _MUTED)
        rows += (
            f'<tr>'
            f'<td style="font-weight:600;">{flag} {country}</td>'
            f'<td style="text-align:right;color:{_MUTED};">{target:,}</td>'
            f'<td style="text-align:right;color:{_WHITE};font-weight:600;">{actual:,}</td>'
            f'<td style="text-align:right;color:{gap_color};font-weight:700;">{gap_sign}{gap}</td>'
            f'<td style="text-align:center;">{_status_pill(status)}</td>'
            f'<td style="text-align:center;font-weight:700;color:{action_color};">{action}</td>'
            f'</tr>'
        )
    rows += "</tbody></table>"

    _card_open("Regional Target Performance")
    st.markdown(
        f'<div style="overflow-x:auto;">{header}{rows}</div>',
        unsafe_allow_html=True,
    )
    _card_close()


def _market_contribution_chart():
    """Card 2: Market Contribution Analysis - stacked horizontal bar."""
    np.random.seed(42)
    countries = [r[1] for r in _COUNTRIES]
    strat_demand    = [488, 162, 118,  95, 68, 58, 88, 42, 30]
    potential_cust  = [420, 140, 100,  82, 55, 48, 75, 35, 25]
    ai_interest     = [165,  62,  42,  30, 22, 18, 32, 12,  8]
    opp_value       = [210,  80,  55,  40, 28, 24, 38, 18, 12]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Strategic Demand",     y=countries, x=strat_demand,   orientation="h", marker_color="rgba(34,211,238,0.75)"))
    fig.add_trace(go.Bar(name="Potential Customers",  y=countries, x=potential_cust, orientation="h", marker_color="rgba(20,184,166,0.70)"))
    fig.add_trace(go.Bar(name="AI Assistant Interest",y=countries, x=ai_interest,    orientation="h", marker_color="rgba(168,85,247,0.75)"))
    fig.add_trace(go.Bar(name="Opportunity Value",    y=countries, x=opp_value,      orientation="h", marker_color="rgba(74,222,128,0.65)"))

    _cl(fig, 320)
    fig.update_layout(
        barmode="stack",
        margin=dict(l=128, r=24, t=18, b=60),
        xaxis_title="Indexed contribution",
        yaxis=dict(autorange="reversed", tickfont=dict(size=10, color="#CBD5E1"), automargin=True),
    )

    _card_open("Market Contribution Analysis")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


def _ai_by_market_chart():
    """Card 3: AI Assistant by Market - grouped bar chart."""
    np.random.seed(42)
    countries_short = ["S. Africa", "Zambia", "Mozambique", "Botswana", "Angola", "Namibia", "Zimbabwe", "Malawi", "DRC"]
    ai_interest_pct  = [34, 38, 28, 22, 18, 15, 31, 12,  8]
    ai_interactions  = [166, 62, 33, 21, 12,  9, 27,  5,  2]
    ai_demo_conv_pct = [21, 24, 18, 15, 13, 12, 20,  9,  6]
    target_line      = [30] * 9
    prev_month       = [31, 35, 26, 20, 16, 14, 29, 11,  7]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="AI Interest %",           x=countries_short, y=ai_interest_pct,  marker_color="rgba(168,85,247,0.75)"))
    fig.add_trace(go.Bar(name="AI Interactions (x10)",   x=countries_short, y=[v*10 for v in ai_interactions], marker_color="rgba(20,184,166,0.70)"))
    fig.add_trace(go.Bar(name="AI-to-Demo Conv %",       x=countries_short, y=ai_demo_conv_pct, marker_color="rgba(34,211,238,0.65)"))
    fig.add_trace(go.Scatter(name="Target", x=countries_short, y=target_line,
        mode="lines", line=dict(color=_PURPLE, width=2, dash="dash"),
        hovertemplate="Target: %{y}%<extra></extra>"))
    fig.add_trace(go.Scatter(name="Prev Month", x=countries_short, y=prev_month,
        mode="lines", line=dict(color="rgba(107,127,163,0.6)", width=1.5, dash="dot"),
        hovertemplate="Prev Month: %{y}%<extra></extra>"))

    _cl(fig, 320)
    fig.update_layout(
        barmode="group",
        bargap=0.24,
        margin=dict(l=50, r=24, t=18, b=82),
        xaxis=dict(tickangle=-25, tickfont=dict(size=9, color="#CBD5E1"), automargin=True),
        yaxis_title="Index / percent",
    )

    _card_open("AI Assistant by Market")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


def _risk_anomaly_trend():
    """Card 4: Risk / Anomaly Trend - line chart, last 30 days, business language."""
    np.random.seed(42)
    days = list(range(-29, 1))
    risk_events       = [max(0, int(3 + np.random.normal(0, 1.2))) for _ in days]
    visit_issues      = [max(0, int(6 + np.random.normal(0, 2))) for _ in days]
    data_warnings     = [max(0, int(4 + np.random.normal(0, 1.5))) for _ in days]
    demand_spikes     = [max(0, int(2 + np.random.normal(0, 1))) for _ in days]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=risk_events, name="Risk Events",
        line=dict(color=_RED, width=2), mode="lines",
        fill="tozeroy", fillcolor="rgba(248,113,113,0.06)",
        hovertemplate="Risk Events: <b>%{y}</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=days, y=visit_issues, name="Visit Issues",
        line=dict(color=_ORANGE, width=2), mode="lines",
        fill="tozeroy", fillcolor="rgba(245,158,11,0.05)",
        hovertemplate="Visit Issues: <b>%{y}</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=days, y=data_warnings, name="Data Quality Warnings",
        line=dict(color=_YELLOW, width=2), mode="lines",
        fill="tozeroy", fillcolor="rgba(251,191,36,0.05)",
        hovertemplate="Data Warnings: <b>%{y}</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=days, y=demand_spikes, name="Unusual Demand Spikes",
        line=dict(color=_CYAN, width=2), mode="lines",
        fill="tozeroy", fillcolor="rgba(34,211,238,0.05)",
        hovertemplate="Demand Spikes: <b>%{y}</b><extra></extra>"))

    _cl(fig, 240)
    fig.update_layout(yaxis_title="Count", xaxis_title="Days Ago")

    _card_open("Risk and Anomaly Trend - Last 30 Days")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


def _strategic_signals_grid():
    """Card 5: Strategic Signals Breakdown - 5 styled metric cards in a grid."""
    signals = [
        ("Policy Momentum",      "+12%",   "+",  _GREEN,  "Regulatory tailwinds across SADC"),
        ("Digital Adoption",     "+18%",   "+",  _CYAN,   "Rising enterprise tech uptake"),
        ("Partner Activity",     "+8%",    "+",  _TEAL,   "Channel expansion progressing"),
        ("Market Readiness",     "72%",    "to",  _YELLOW, "Key markets approaching readiness"),
        ("Competitive Pressure", "Medium", "to",  _ORANGE, "Manageable - monitor closely"),
    ]
    cols = st.columns(5, gap="small")
    for col, (label, value, arrow, color, desc) in zip(cols, signals):
        with col:
            st.markdown(
                f'<div class="signal-metric-card">'
                f'<div style="font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;'
                f'color:{_MUTED};margin-bottom:6px;">{label}</div>'
                f'<div style="font-size:1.4rem;font-weight:800;color:{color};line-height:1;margin-bottom:4px;">'
                f'{arrow} {value}</div>'
                f'<div style="font-size:10px;color:{_MUTED};line-height:1.4;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _exec_insight_assistant():
    """Card 6: Executive Insight Assistant - board-level glassmorphism card."""
    bullets = [
        ("South Africa leads with 488 potential customers, 38 above the 450 target - sustain investment momentum."),
        ("Zambia exceeds its 150-customer target with 162 actuals, confirming strategic hub status."),
        ("Angola, Malawi, and DRC are collectively 30 customers below target - executive review recommended."),
        ("AI Assistant traction is at 29.4% across SADC sessions, on track toward the 30% board target."),
        ("Forecasted 90-day potential customer pipeline is 1,850 at base case - regional expansion justified."),
    ]
    rows_html = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:9px 0;'
        f'border-bottom:1px solid rgba(168,85,247,0.08);">'
        f'<span style="color:{_PURPLE};font-size:14px;flex-shrink:0;font-weight:700;">▸</span>'
        f'<span style="font-size:12px;color:{_WHITE};line-height:1.55;">{b}</span>'
        f'</div>'
        for b in bullets
    )
    recommended = (
        '<div style="margin-top:14px;padding:12px 14px;background:rgba(168,85,247,0.06);'
        'border:1px solid rgba(168,85,247,0.2);border-radius:10px;">'
        '<div style="font-size:9px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;'
        f'color:{_PURPLE};margin-bottom:6px;">Recommended Action</div>'
        f'<div style="font-size:12px;color:{_WHITE};line-height:1.55;">'
        'Invest in South Africa and Zambia immediately. Schedule Angola, Malawi, and DRC executive review '
        'within 30 days. Maintain AI Assistant traction initiatives across all active markets.'
        '</div></div>'
    )

    _card_open("Executive Insight Assistant")
    st.markdown(
        f'<div class="exec-insight-card">'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
        f'<div style="width:32px;height:32px;background:rgba(168,85,247,0.15);border:1px solid rgba(168,85,247,0.3);'
        f'border-radius:8px;display:flex;align-items:center;justify-content:center;'
        f'font-size:16px;">&#128200;</div>'
        f'<div>'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{_PURPLE};">'
        f'CyberNova Intelligence  -  Board Briefing</div>'
        f'<div style="font-size:9px;color:{_MUTED};">Strategic analysis  -  Executive level</div>'
        f'</div></div>'
        f'{rows_html}'
        f'{recommended}'
        f'</div>',
        unsafe_allow_html=True,
    )
    _card_close()


def render_executive_analytics(df):
    """Render Executive Analytics tab - 6 cards."""
    inject_executive_css()

    with st.container(key="executive_analytics_scope"):
        # Card 1: Regional Target Table - full width
        _regional_target_table()

        # Cards 2 + 3: 2 columns
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            _market_contribution_chart()
        with c2:
            _ai_by_market_chart()

        # Card 4: Risk / Anomaly Trend - full width
        _risk_anomaly_trend()

        # Card 5: Strategic Signals - 5 cols
        _card_open("Strategic Signals Breakdown")
        _strategic_signals_grid()
        _card_close()

        # Card 6: Executive Insight Assistant - full width
        _exec_insight_assistant()


# ══════════════════════════════════════════════════════════════════════════════
# 4. EXECUTIVE FORECASTING TAB
# ══════════════════════════════════════════════════════════════════════════════

def _forecast_kpi_row():
    """Item 1: Forecast Summary KPI row - 5 cards."""
    kpis = [
        ("90-Day Customer Forecast", "1,850",  "base case scenario",   "+ 48%",    "up"),
        ("Forecasted Strategic Demand","11,200","projected engagement", "+ 22%",    "up"),
        ("AI Traction Forecast",     "34%",    "vs current 29.4%",     "+ 4.6 pts","up"),
        ("Forecasted Opp. Value",    "P4.8M",  "base case revenue",    "+ 27%",    "up"),
        ("Confidence Level",         "72%",    "medium accuracy",      "Medium",   "watch"),
    ]
    delta_cls = {"up": "delta-up", "watch": "delta-watch", "down": "delta-down"}
    cols = st.columns(5, gap="small")
    for col, (lbl, val, sub, chg, cls) in zip(cols, kpis):
        with col:
            dcls = delta_cls.get(cls, "delta-up")
            delta_html = f'<div class="kpi-delta {dcls}">{chg}</div>' if chg else ""
            st.markdown(
                f'<div class="exec-kpi-card">'
                f'<div class="kpi-label">{lbl}</div>'
                f'<div class="kpi-value-sm" style="color:{_PURPLE};">{val}</div>'
                f'{delta_html}'
                f'<div class="kpi-sub">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _forecast_90d_chart():
    """Item 2: 90-Day Potential Customer Forecast - line chart."""
    np.random.seed(42)
    days_hist = list(range(-60, 1))
    days_fwd  = list(range(0, 91))

    actual_vals = [1100 + i * 2.5 + np.random.randint(-18, 18) for i in range(61)]
    fwd_base    = actual_vals[-1]
    fwd_vals    = [fwd_base + i * 3.2 for i in range(91)]
    upper_b     = [v + 60 + i * 0.7 for i, v in enumerate(fwd_vals)]
    lower_b     = [v - 60 - i * 0.7 for i, v in enumerate(fwd_vals)]
    target_vals = [1400 + i * 5 for i in range(91)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days_hist, y=actual_vals, name="Actual",
        line=dict(color=_CYAN, width=2.5), mode="lines",
        hovertemplate="Day %{x}<br>Actual: %{y:,}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=days_fwd, y=fwd_vals, name="Forecast",
        line=dict(color=_CYAN, width=2, dash="dash"), mode="lines",
        hovertemplate="Day %{x}<br>Forecast: %{y:,}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=days_fwd + days_fwd[::-1],
        y=upper_b + lower_b[::-1],
        fill="toself", fillcolor="rgba(34,211,238,0.06)",
        line=dict(width=0), name="Confidence Band"))
    fig.add_trace(go.Scatter(
        x=days_fwd, y=target_vals, name="Target / Aim",
        line=dict(color=_PURPLE, width=1.5, dash="dash"), mode="lines",
        hovertemplate="Day %{x}<br>Target: %{y:,}<extra></extra>"))
    fig.add_vline(x=0, line_color="rgba(255,255,255,0.5)", line_width=1.5, line_dash="dash",
                  annotation_text="Today", annotation_font_color=_WHITE, annotation_font_size=9)

    _cl(fig, 230)
    fig.update_layout(yaxis_title="Potential Customers")

    _card_open("90-Day Potential Customer Forecast")
    st.markdown(
        f'<div style="font-size:9px;color:{_YELLOW};margin-bottom:6px;">'
        'Rule-based linear forecast, not predictive AI.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


def _regional_expansion_forecast():
    """Item 3: Regional Expansion Forecast - styled HTML table."""
    data = [
        ("🇿🇦", "South Africa", "Core Market",   "Invest",   "Strong pipeline growth",    _GREEN),
        ("🇿🇲", "Zambia",       "Strategic Hub",  "Invest",   "Rising potential",          _GREEN),
        ("🇧🇼", "Botswana",     "Stable",         "Monitor",  "Consistent but slow growth",_YELLOW),
        ("🇲🇿", "Mozambique",   "Emerging",       "Monitor",  "Improving engagement",      _YELLOW),
        ("🇦🇴", "Angola",       "Emerging",       "Review",   "Below target",              _RED),
        ("🇳🇦", "Namibia",      "Stable",         "Monitor",  "Flat performance",          _YELLOW),
        ("🇿🇼", "Zimbabwe",     "High Growth",    "Monitor",  "Volatile signals",          _YELLOW),
        ("🇲🇼", "Malawi",       "Emerging",       "Review",   "Insufficient demand",       _RED),
        ("🇨🇩", "DRC",          "Emerging",       "Review",   "Limited access",            _RED),
    ]
    header = (
        '<table class="exec-table"><thead><tr>'
        '<th>Country</th><th>Current Status</th><th>Forecast Action</th>'
        '<th>Reason</th><th>Recommended Action</th>'
        '</tr></thead><tbody>'
    )
    rows = ""
    for flag, country, current, forecast, reason, color in data:
        action_pill = (
            f'<span style="font-size:10px;font-weight:700;color:{color};'
            f'background:rgba(0,0,0,0.2);padding:2px 8px;border-radius:20px;">{forecast}</span>'
        )
        rows += (
            f'<tr>'
            f'<td style="font-weight:600;">{flag} {country}</td>'
            f'<td style="color:{_MUTED};">{current}</td>'
            f'<td>{action_pill}</td>'
            f'<td style="color:{_MUTED};font-size:11px;">{reason}</td>'
            f'<td style="font-weight:700;color:{color};">{forecast}</td>'
            f'</tr>'
        )
    rows += "</tbody></table>"

    _card_open("Regional Expansion Forecast")
    st.markdown(f'<div style="overflow-x:auto;">{header}{rows}</div>', unsafe_allow_html=True)
    _card_close()


def _ai_traction_forecast_chart():
    """Item 4: AI Assistant Traction Forecast - multi-line chart."""
    np.random.seed(42)
    months_hist = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]
    months_fwd  = ["Apr", "May", "Jun", "Jul"]

    actual_ai   = [21, 23, 24, 26, 27, 28, 29]
    forecast_ai = [29, 30, 32, 34]
    target_mo   = [28, 29, 30, 32, 33, 34, 35]
    prev_actual = [19, 22, 23, 25, 26, 27, 28]
    upper_b     = [30.5, 32, 34, 36.5]
    lower_b     = [27.5, 28, 30, 31.5]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months_fwd + months_fwd[::-1], y=upper_b + lower_b[::-1],
        fill="toself", fillcolor="rgba(168,85,247,0.06)",
        line=dict(width=0), name="Confidence Band"))
    fig.add_trace(go.Scatter(
        x=months_hist, y=actual_ai, name="Actual AI Interest",
        line=dict(color=_PURPLE, width=2.5), mode="lines+markers",
        marker=dict(size=5, color=_PURPLE),
        hovertemplate="<b>%{x}</b><br>Actual: %{y}%<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=months_fwd, y=forecast_ai, name="Forecast AI Interest",
        line=dict(color=_PURPLE, width=2, dash="dash"), mode="lines",
        hovertemplate="<b>%{x}</b><br>Forecast: %{y}%<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=months_hist + months_fwd[1:], y=target_mo, name="Monthly Target",
        line=dict(color=_CYAN, width=1.5, dash="dash"), mode="lines",
        hovertemplate="<b>%{x}</b><br>Target: %{y}%<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=months_hist, y=prev_actual, name="Previous Month Actual",
        line=dict(color="rgba(107,127,163,0.6)", width=1.5, dash="dot"), mode="lines",
        hovertemplate="<b>%{x}</b><br>Prev: %{y}%<extra></extra>"))

    _cl(fig, 230)
    fig.update_layout(yaxis_title="AI Traction %")

    _card_open("AI Assistant Traction Forecast")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


def _forecast_vs_target_area():
    """Item 5: Forecast vs Target - area chart with side metrics panel."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    fcast  = [3.1, 3.5, 3.8, 4.2, 4.8, 5.3]
    target = [3.4, 3.8, 4.2, 4.6, 5.2, 5.8]
    upper  = [f + 0.22 for f in fcast]
    lower  = [f - 0.22 for f in fcast]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months + months[::-1], y=upper + lower[::-1],
        fill="toself", fillcolor="rgba(34,211,238,0.05)",
        line=dict(width=0), name="Confidence Band"))
    fig.add_trace(go.Scatter(
        x=months, y=lower, name="Lower Band",
        line=dict(color="rgba(107,127,163,0.5)", width=1, dash="dash"), mode="lines"))
    fig.add_trace(go.Scatter(
        x=months, y=upper, name="Upper Band",
        line=dict(color="rgba(107,127,163,0.5)", width=1, dash="dash"), mode="lines"))
    fig.add_trace(go.Scatter(
        x=months, y=fcast, name="Forecast",
        line=dict(color=_CYAN, width=2.5), mode="lines+markers",
        marker=dict(size=6, color=_CYAN),
        hovertemplate="<b>%{x}</b><br>Forecast: P%{y:.1f}M<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=months, y=target, name="Target",
        line=dict(color=_PURPLE, width=1.5, dash="dash"), mode="lines",
        hovertemplate="<b>%{x}</b><br>Target: P%{y:.1f}M<extra></extra>"))

    _cl(fig, 230)
    fig.update_layout(yaxis_title="Opportunity Value (PM)", showlegend=True)

    col_chart, col_metrics = st.columns([3, 1], gap="small")
    with col_chart:
        _card_open("Forecast vs Target")
        st.markdown(
            f'<div style="font-size:9px;color:{_YELLOW};margin-bottom:4px;">'
            'Rule-based linear forecast, not predictive AI.</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
        _card_close()
    with col_metrics:
        st.markdown(
            f'<div class="exec-kpi-card" style="height:100%;display:flex;flex-direction:column;gap:10px;">'
            f'<div><div class="kpi-label">Forecasted Value</div>'
            f'<div class="kpi-value-sm" style="color:{_CYAN};">P4.8M</div></div>'
            f'<div><div class="kpi-label">Target</div>'
            f'<div class="kpi-value-sm" style="color:{_PURPLE};">P5.2M</div></div>'
            f'<div><div class="kpi-label">Gap</div>'
            f'<div class="kpi-value-sm" style="color:{_RED};">-P400K</div></div>'
            f'<div><div class="kpi-label">Confidence</div>'
            f'<div class="kpi-value-sm" style="color:{_YELLOW};">72%</div></div>'
            f'<div><div class="kpi-label">Status</div>'
            f'{_status_pill("On Watch")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _risk_anomaly_gauge():
    """Item 6: Risk / Anomaly Outlook - Plotly indicator gauge."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=42,
        title={"text": "Risk Score", "font": {"color": _MUTED, "size": 11}},
        number={"suffix": "/100", "font": {"color": _YELLOW, "size": 26}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": _MUTED, "tickfont": {"size": 9}},
            "bar": {"color": _YELLOW, "thickness": 0.28},
            "bgcolor": "rgba(7,16,28,0.6)",
            "bordercolor": "rgba(168,85,247,0.14)",
            "steps": [
                {"range": [0, 33],  "color": "rgba(74,222,128,0.1)"},
                {"range": [33, 66], "color": "rgba(251,191,36,0.1)"},
                {"range": [66, 100],"color": "rgba(248,113,113,0.12)"},
            ],
            "threshold": {
                "line": {"color": _PURPLE, "width": 2},
                "thickness": 0.75,
                "value": 66,
            },
        },
    ))
    fig.update_layout(
        height=240,
        margin=dict(l=18, r=18, t=42, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", size=11),
    )

    _card_open("Risk and Anomaly Outlook")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    st.markdown(
        f'<div style="text-align:center;font-size:11px;color:{_YELLOW};font-weight:700;margin-bottom:8px;">MEDIUM RISK</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3, gap="small")
    metric_items = [
        ("Forecasted Risk Events", "8",   _YELLOW),
        ("Data Quality Outlook",   "91%", _GREEN),
        ("Operational Stability",  "Stable", _CYAN),
    ]
    for col, (lbl, val, color) in zip([c1, c2, c3], metric_items):
        with col:
            st.markdown(
                f'<div style="text-align:center;">'
                f'<div style="font-size:9px;color:{_MUTED};text-transform:uppercase;letter-spacing:.1em;">{lbl}</div>'
                f'<div style="font-size:14px;font-weight:700;color:{color};">{val}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    _card_close()


def _investment_recommendation():
    """Item 7: Executive Investment Recommendation - decision card."""
    sections = [
        ("Invest",   _GREEN,  "invest-card",  "🇿🇦 South Africa, 🇿🇲 Zambia"),
        ("Monitor",  _YELLOW, "monitor-card", "🇲🇿 Mozambique, 🇳🇦 Namibia, 🇧🇼 Botswana"),
        ("Review",   _RED,    "review-card",  "🇦🇴 Angola, 🇲🇼 Malawi, 🇨🇩 DRC"),
    ]
    _card_open("Executive Investment Recommendation")
    html = ""
    for action, color, css_cls, markets in sections:
        html += (
            f'<div class="{css_cls}">'
            f'<div style="font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;'
            f'color:{color};margin-bottom:6px;">{action}</div>'
            f'<div style="font-size:13px;color:{_WHITE};font-weight:500;">{markets}</div>'
            f'</div>'
        )
    st.markdown(html, unsafe_allow_html=True)
    _card_close()


def _scenario_cards():
    """Item 8: Scenario Cards - 3 cards in a row."""
    scenarios = [
        ("Conservative Case",
         "rgba(107,127,163,0.08)", "rgba(107,127,163,0.25)", _GRAY,
         [("Potential Customers","1,420"),("Opportunity Value","P3.2M"),
          ("Risk Level","Low"),("Strategy","Protect core markets")]),
        ("Base Case",
         "rgba(34,211,238,0.06)", "rgba(34,211,238,0.28)", _CYAN,
         [("Potential Customers","1,850"),("Opportunity Value","P4.8M"),
          ("Risk Level","Medium"),("Strategy","Invest in SA + Zambia")]),
        ("Growth Case",
         "rgba(168,85,247,0.07)", "rgba(168,85,247,0.3)", _PURPLE,
         [("Potential Customers","2,340"),("Opportunity Value","P6.1M"),
          ("Risk Level","Medium-High"),("Strategy","Expand to high-growth markets")]),
    ]
    cols = st.columns(3, gap="small")
    for col, (title, bg, border, color, items) in zip(cols, scenarios):
        metrics_html = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:5px 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.04);">'
            f'<span style="font-size:10px;color:{_MUTED};">{k}</span>'
            f'<span style="font-size:11px;font-weight:700;color:{_WHITE};">{v}</span>'
            f'</div>'
            for k, v in items
        )
        with col:
            st.markdown(
                f'<div class="scenario-card" style="background:{bg};border:1px solid {border};">'
                f'<div style="font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;'
                f'color:{color};margin-bottom:12px;">{title}</div>'
                f'{metrics_html}'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_executive_forecasting(df):
    """Render Executive Forecasting tab - 8 items."""
    inject_executive_css()

    with st.container(key="executive_forecasting_scope"):
        # Item 1: KPI row
        _forecast_kpi_row()
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        # Item 2: 90-day forecast chart - full width
        _forecast_90d_chart()

        # Item 3: Regional Expansion Forecast table - full width
        _regional_expansion_forecast()

        # Item 4 + 5: AI Traction Forecast and Forecast vs Target
        _ai_traction_forecast_chart()
        _forecast_vs_target_area()

        # Item 6 + 7 in a row
        c1, c2 = st.columns([1, 1.5], gap="medium")
        with c1:
            _risk_anomaly_gauge()
        with c2:
            _investment_recommendation()

        # Item 8: Scenario cards
        _card_open("Scenario Planning")
        _scenario_cards()
        _card_close()


# ══════════════════════════════════════════════════════════════════════════════
# 5. EXECUTIVE DATA & EXPORT TAB
# ══════════════════════════════════════════════════════════════════════════════

def _decision_brief():
    """Item 1: Executive Decision Brief."""
    bullets = [
        (f"color:{_GREEN};", "Top growth market: South Africa - 488 potential customers, above target by 38."),
        (f"color:{_CYAN};",  "AI Assistant: 29.4% traction rate, on track for 30% board target."),
        (f"color:{_RED};",   "Strategic risk: 3 markets below target - Angola, Malawi, and DRC require executive review."),
        (f"color:{_PURPLE};","Investment priority: Invest in South Africa and Zambia; monitor Botswana, Mozambique, Namibia."),
        (f"color:{_YELLOW};","Forecast confidence: 72% (base case scenario) - reliable for near-term planning."),
    ]
    html = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;'
        f'border-bottom:1px solid rgba(168,85,247,0.08);">'
        f'<span style="{color}font-size:14px;flex-shrink:0;font-weight:700;">▸</span>'
        f'<span style="font-size:12px;color:{_WHITE};line-height:1.55;">{text}</span>'
        f'</div>'
        for color, text in bullets
    )

    _card_open("Executive Decision Brief")
    st.markdown(
        f'<div class="exec-insight-card">'
        f'<div style="font-size:9px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;'
        f'color:{_PURPLE};margin-bottom:10px;">Board-Level Strategic Summary  -  {datetime.date.today().strftime("%B %Y")}</div>'
        f'{html}'
        f'</div>',
        unsafe_allow_html=True,
    )
    _card_close()


def _regional_priority_table():
    """Item 2: Regional Priority Table with flags."""
    data = [
        ("🇿🇦", "South Africa", "Core Market",   488, "34%", "P4.8M", "Low",    "Invest",   _GREEN),
        ("🇿🇲", "Zambia",       "Strategic Hub",  162, "38%", "P1.9M", "Low",    "Invest",   _GREEN),
        ("🇲🇿", "Mozambique",   "Emerging",       118, "28%", "P1.2M", "Medium", "Monitor",  _YELLOW),
        ("🇧🇼", "Botswana",     "Stable",          95, "22%", "P0.9M", "Low",    "Monitor",  _YELLOW),
        ("🇦🇴", "Angola",       "Emerging",        68, "18%", "P0.6M", "Medium", "Review",   _RED),
        ("🇳🇦", "Namibia",      "Stable",          58, "15%", "P0.5M", "Low",    "Monitor",  _YELLOW),
        ("🇿🇼", "Zimbabwe",     "High Growth",     88, "31%", "P0.9M", "Medium", "Maintain", _CYAN),
        ("🇲🇼", "Malawi",       "Emerging",        42, "12%", "P0.3M", "Low",    "Review",   _RED),
        ("🇨🇩", "DRC",          "Emerging",        30,  "8%", "P0.2M", "High",   "Review",   _RED),
    ]
    header = (
        '<table class="exec-table"><thead><tr>'
        '<th>Country</th><th>Status</th><th style="text-align:right;">Potential Customers</th>'
        '<th style="text-align:right;">AI Interest</th><th style="text-align:right;">Opportunity Value</th>'
        '<th style="text-align:center;">Risk Level</th><th style="text-align:center;">Action</th>'
        '</tr></thead><tbody>'
    )
    risk_colors = {"Low": _GREEN, "Medium": _YELLOW, "High": _RED}
    rows = ""
    for flag, country, status, cust, ai_int, opp, risk, action, color in data:
        risk_c = risk_colors.get(risk, _MUTED)
        rows += (
            f'<tr>'
            f'<td style="font-weight:600;">{flag} {country}</td>'
            f'<td style="color:{_MUTED};font-size:11px;">{status}</td>'
            f'<td style="text-align:right;color:{_CYAN};font-weight:700;">{cust:,}</td>'
            f'<td style="text-align:right;color:{_PURPLE};">{ai_int}</td>'
            f'<td style="text-align:right;color:{_GREEN};font-weight:600;">{opp}</td>'
            f'<td style="text-align:center;color:{risk_c};font-weight:600;">{risk}</td>'
            f'<td style="text-align:center;font-weight:700;color:{color};">{action}</td>'
            f'</tr>'
        )
    rows += "</tbody></table>"

    _card_open("Regional Priority Table")
    st.markdown(f'<div style="overflow-x:auto;">{header}{rows}</div>', unsafe_allow_html=True)
    _card_close()


def _risk_evidence_table():
    """Item 3: Risk / Anomaly Evidence Table."""
    data = [
        ("2026-04-28", "Angola",       "Demand Gap",         "High",   "Below target by 12 customers",       "Executive review required"),
        ("2026-04-30", "Malawi",       "Low Engagement",     "High",   "AI interaction rate critically low",  "Marketing support needed"),
        ("2026-05-01", "DRC",          "Market Access",      "High",   "Limited platform reach",             "Regional strategy review"),
        ("2026-04-25", "Zimbabwe",     "Signal Volatility",  "Medium", "Inconsistent demand trend",          "Monitor weekly"),
        ("2026-04-27", "Mozambique",   "Conversion Dip",     "Medium", "Slight drop in qualified interest",  "Adjust outreach timing"),
        ("2026-05-02", "Botswana",     "Slow Growth",        "Low",    "Growth below 5% monthly pace",       "Maintain current strategy"),
        ("2026-04-29", "Namibia",      "Flat Performance",   "Low",    "No meaningful change month-over-month", "Continue monitoring"),
        ("2026-05-03", "South Africa", "Unusual Demand Spike","Low",   "Higher than expected activity - positive", "Validate and scale"),
    ]
    sev_colors = {"High": _RED, "Medium": _YELLOW, "Low": _CYAN}
    header = (
        '<table class="exec-table"><thead><tr>'
        '<th>Date</th><th>Market</th><th>Risk Type</th><th>Severity</th>'
        '<th>Business Impact</th><th>Action Needed</th>'
        '</tr></thead><tbody>'
    )
    rows = ""
    for date, market, rtype, severity, impact, action in data:
        sev_c = sev_colors.get(severity, _MUTED)
        sev_pill = (
            f'<span style="font-size:10px;font-weight:700;color:{sev_c};'
            f'padding:2px 8px;border-radius:20px;background:rgba(0,0,0,0.2);">{severity}</span>'
        )
        rows += (
            f'<tr>'
            f'<td style="color:{_MUTED};font-size:11px;">{date}</td>'
            f'<td style="font-weight:600;">{market}</td>'
            f'<td style="color:{_WHITE};">{rtype}</td>'
            f'<td>{sev_pill}</td>'
            f'<td style="color:{_MUTED};font-size:11px;">{impact}</td>'
            f'<td style="color:{_CYAN};font-size:11px;">{action}</td>'
            f'</tr>'
        )
    rows += "</tbody></table>"

    _card_open("Risk and Anomaly Evidence Table")
    st.markdown(f'<div style="overflow-x:auto;">{header}{rows}</div>', unsafe_allow_html=True)
    _card_close()


def _filtered_strategic_data(df, date_start=None, date_end=None):
    """Item 4: Filtered Strategic Data - st.dataframe."""
    _NEEDED_COLS = [
        "date", "country", "service_name",
        "potential_customer_signal", "estimated_deal_value", "risk_level",
    ]

    # Try to use real df
    try:
        if df is not None and not df.empty:
            available = [c for c in _NEEDED_COLS if c in df.columns]
            dff = df[available].copy() if available else df.copy()
            if "date" in dff.columns:
                dff["date"] = pd.to_datetime(dff["date"], errors="coerce")
                if date_start:
                    dff = dff[dff["date"] >= pd.to_datetime(date_start)]
                if date_end:
                    dff = dff[dff["date"] <= pd.to_datetime(date_end)]
            dff = dff.head(200)
        else:
            raise ValueError("empty df")
    except Exception:
        # Mock fallback
        np.random.seed(42)
        n = 50
        countries = ["South Africa","Zambia","Mozambique","Botswana","Angola","Namibia","Zimbabwe","Malawi","DRC"]
        services  = ["Strategic Advisory","AI Solutions","Digital Transformation","Market Analytics","Managed Services"]
        risk_lvls = ["Low","Medium","High"]
        dff = pd.DataFrame({
            "date": pd.date_range("2026-04-01", periods=n, freq="D")[:n],
            "country": np.random.choice(countries, n),
            "service_name": np.random.choice(services, n),
            "potential_customer_signal": np.random.randint(10, 90, n),
            "estimated_deal_value": [f"P{v:,}" for v in np.random.randint(50000, 500000, n)],
            "risk_level": np.random.choice(risk_lvls, n),
        })

    _card_open("Filtered Strategic Data")
    st.dataframe(
        dff,
        use_container_width=True,
        height=280,
    )
    _card_close()


def _export_center(df):
    """Item 5: Export Center - download buttons."""
    _card_open("Export Center")

    # Build CSV bytes for filtered data
    try:
        csv_data = df.to_csv(index=False).encode() if df is not None and not df.empty else b"no data"
    except Exception:
        csv_data = b"no data"

    # Regional priority CSV - _COUNTRIES = (flag, country, target, actual, gap, status, action)
    rp_data = pd.DataFrame([
        {"Country": r[1], "Target": r[2], "Actual": r[3], "Gap": r[4],
         "Status": r[5], "Recommended_Action": r[6]}
        for r in _COUNTRIES
    ]).to_csv(index=False).encode()

    # Risk evidence CSV
    risk_rows = [
        {"Date":"2026-04-28","Market":"Angola","Risk_Type":"Demand Gap","Severity":"High"},
        {"Date":"2026-04-30","Market":"Malawi","Risk_Type":"Low Engagement","Severity":"High"},
        {"Date":"2026-05-01","Market":"DRC","Risk_Type":"Market Access","Severity":"High"},
        {"Date":"2026-04-25","Market":"Zimbabwe","Risk_Type":"Signal Volatility","Severity":"Medium"},
        {"Date":"2026-04-27","Market":"Mozambique","Risk_Type":"Conversion Dip","Severity":"Medium"},
        {"Date":"2026-05-02","Market":"Botswana","Risk_Type":"Slow Growth","Severity":"Low"},
    ]
    risk_csv = pd.DataFrame(risk_rows).to_csv(index=False).encode()

    methodology_text = (
        "CyberNova BI - Executive Methodology\n\n"
        "Strategic Demand Score: aggregated potential customer signals across SADC markets.\n"
        "Regional Priority Logic: markets ranked by actual vs target gap, AI traction, and risk level.\n"
        "AI Assistant Traction: % of platform sessions engaging CyberNova AI Assistant.\n"
        "Risk Scoring: composite of demand gap, data quality, and operational stability indicators.\n"
        "Forecasting: rule-based linear projection - not machine learning or predictive AI.\n"
        "Data Note: dashboard uses synthetic/generated data for demonstration purposes.\n"
        "Date Range Default: last 7 days unless overridden by date filter.\n"
    ).encode()

    exec_summary = (
        "CyberNova Executive Summary\n\n"
        "Top Growth Market: South Africa (488 customers, above target)\n"
        "AI Traction: 29.4% - on track for 30% target\n"
        "Markets Below Target: Angola, Malawi, DRC\n"
        "Investment Priority: South Africa, Zambia\n"
        "Forecast Confidence: 72% (base case)\n"
    ).encode()

    if _EXPORTS_OK:
        try:
            weekly_pdf  = build_weekly_report_pdf(df)
            monthly_pdf = build_monthly_report_pdf(df)
            method_pdf  = build_methodology_pdf()
        except Exception:
            weekly_pdf = monthly_pdf = method_pdf = None
    else:
        weekly_pdf = monthly_pdf = method_pdf = None

    st.markdown(
        f'<div style="font-size:9px;color:{_MUTED};margin-bottom:10px;">'
        'Download strategic reports and data exports for offline review.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        if weekly_pdf:
            st.download_button("Weekly PDF Report",    data=weekly_pdf,  file_name="cybernova_weekly_report.pdf",    mime="application/pdf", use_container_width=True)
        else:
            st.download_button("Weekly PDF Report",    data=csv_data,    file_name="cybernova_weekly_report.csv",    mime="text/csv",         use_container_width=True)
        if monthly_pdf:
            st.download_button("Monthly PDF Report",   data=monthly_pdf, file_name="cybernova_monthly_report.pdf",   mime="application/pdf", use_container_width=True)
        else:
            st.download_button("Monthly PDF Report",   data=csv_data,    file_name="cybernova_monthly_report.csv",   mime="text/csv",         use_container_width=True)
    with c2:
        st.download_button("Executive Summary PDF",    data=exec_summary, file_name="cybernova_executive_summary.pdf", mime="application/pdf",  use_container_width=True)
        st.download_button("Board Brief PDF",          data=exec_summary, file_name="cybernova_board_brief.pdf",        mime="application/pdf",  use_container_width=True)
    with c3:
        st.download_button("Regional Priority CSV",    data=rp_data,     file_name="cybernova_regional_priority.csv",  mime="text/csv",         use_container_width=True)
        st.download_button("Risk Evidence CSV",        data=risk_csv,    file_name="cybernova_risk_evidence.csv",       mime="text/csv",         use_container_width=True)
    with c4:
        st.download_button("Filtered Strategic Data CSV", data=csv_data, file_name="cybernova_strategic_data.csv",    mime="text/csv",         use_container_width=True)
        if method_pdf:
            st.download_button("Methodology PDF",      data=method_pdf,  file_name="cybernova_methodology.pdf",        mime="application/pdf",  use_container_width=True)
        else:
            st.download_button("Methodology PDF",      data=methodology_text, file_name="cybernova_methodology.txt",   mime="text/plain",       use_container_width=True)

    _card_close()


def _data_quality_summary():
    """Item 6: Data Quality Summary - 5 progress bars."""
    metrics = [
        ("Data Completeness",       96, _GREEN),
        ("Data Freshness",          99, _GREEN),
        ("Country Coverage",       100, _CYAN),
        ("Risk Signal Coverage",    88, _YELLOW),
        ("Forecast Confidence",     72, _YELLOW),
    ]
    html = ""
    for label, pct, color in metrics:
        html += (
            f'<div class="exec-progress-row">'
            f'<span style="font-size:11px;color:{_WHITE};min-width:180px;">{label}</span>'
            f'<div class="exec-progress-track">'
            f'<div class="exec-progress-fill" style="width:{pct}%;background:{color};"></div>'
            f'</div>'
            f'<span style="font-size:11px;font-weight:700;color:{color};min-width:36px;text-align:right;">{pct}%</span>'
            f'</div>'
        )
    _card_open("Data Quality Summary")
    st.markdown(html, unsafe_allow_html=True)
    _card_close()


def _methodology_note():
    """Item 7: Methodology Note - styled dark card with purple accent."""
    st.markdown(
        f"""
<div style="background:linear-gradient(145deg,rgba(12,4,40,0.92),rgba(8,3,28,0.88));
  border:1px solid rgba(168,85,247,0.22);border-left:3px solid {_PURPLE};
  border-radius:14px;padding:18px 20px;margin-bottom:12px;
  backdrop-filter:blur(12px);">
  <div style="font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
    color:{_PURPLE};margin-bottom:10px;">Methodology and Data Notes</div>
  <div style="display:flex;flex-direction:column;gap:7px;">
    <div style="font-size:11px;color:{_MUTED};">
      <b style="color:{_WHITE};">Strategic Demand Score:</b>
      Aggregated potential customer signals weighted by market readiness and AI traction rate.
    </div>
    <div style="font-size:11px;color:{_MUTED};">
      <b style="color:{_WHITE};">Regional Priority Logic:</b>
      Markets ranked by actual vs. target gap, AI engagement, forecasted growth, and risk level.
    </div>
    <div style="font-size:11px;color:{_MUTED};">
      <b style="color:{_WHITE};">AI Assistant Traction:</b>
      Percentage of total platform sessions in which the CyberNova AI Assistant was actively engaged.
    </div>
    <div style="font-size:11px;color:{_MUTED};">
      <b style="color:{_WHITE};">Risk Scoring:</b>
      Composite indicator combining demand gap, data quality, signal volatility, and operational stability.
    </div>
    <div style="font-size:11px;color:{_YELLOW};">
      <b style="color:{_YELLOW};">Forecasting Limitation:</b>
      All forecasts use rule-based linear projection methods and are not generated by predictive AI or ML models.
    </div>
    <div style="font-size:11px;color:{_YELLOW};">
      <b style="color:{_YELLOW};">Synthetic Data:</b>
      Dashboard data is generated for demonstration purposes. Production deployment requires live data integration.
    </div>
    <div style="font-size:11px;color:{_MUTED};">
      <b style="color:{_WHITE};">Default Date Range:</b>
      Last 7 days unless overridden by the date filter in the Data tab.
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _export_center(df):
    """Functional export center with real PDF/CSV downloads."""
    _card_open("Export Center")

    filters = {
        "role": "Executive",
        "market": st.session_state.get("selected_market", "All"),
        "service": st.session_state.get("svc_filter", "All Services"),
        "segment": st.session_state.get("seg_filter", "All Segments"),
    }
    to_csv = dataframe_to_csv_bytes if _EXPORTS_OK else lambda frame: frame.to_csv(index=False).encode("utf-8")
    strategic_df = df if df is not None and not df.empty else pd.DataFrame()
    weekly_df = filter_last_n_days(strategic_df, 7)[0] if _EXPORTS_OK else strategic_df
    monthly_df = filter_last_n_days(strategic_df, 30)[0] if _EXPORTS_OK else strategic_df
    csv_weekly = to_csv(weekly_df.head(5000)) if not strategic_df.empty else b"No data available\n"
    csv_monthly = to_csv(monthly_df.head(5000)) if not strategic_df.empty else b"No data available\n"
    today_label = period_label(7) if _EXPORTS_OK else "current 7 days"
    month_label = period_label(30) if _EXPORTS_OK else "current 30 days"

    regional_priority = pd.DataFrame([
        {"Country": r[1], "Target": r[2], "Actual": r[3], "Gap": r[4], "Status": r[5], "Recommended_Action": r[6]}
        for r in _COUNTRIES
    ])
    risk_rows = pd.DataFrame([
        {"Date": "2026-04-28", "Market": "Angola", "Risk_Type": "Demand Gap", "Severity": "High"},
        {"Date": "2026-04-30", "Market": "Malawi", "Risk_Type": "Low Engagement", "Severity": "High"},
        {"Date": "2026-05-01", "Market": "DRC", "Risk_Type": "Market Access", "Severity": "High"},
        {"Date": "2026-04-25", "Market": "Zimbabwe", "Risk_Type": "Signal Volatility", "Severity": "Medium"},
        {"Date": "2026-05-02", "Market": "Botswana", "Risk_Type": "Slow Growth", "Severity": "Low"},
    ])

    st.markdown(
        f"""
<div style="font-size:9px;color:{_MUTED};margin-bottom:10px;">
  Download strategic PDF reports with embedded visuals plus CSV evidence exports.
</div>
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:10px;">
  <div style="background:rgba(8,18,34,0.78);border:1px solid rgba(168,85,247,0.22);border-radius:12px;padding:10px;">
    <div style="font-size:10px;color:{_PURPLE};font-weight:800;">Executive Pack</div>
    <div style="font-size:18px;color:{_WHITE};font-weight:900;">{len(strategic_df):,}</div>
    <div style="font-size:10px;color:{_MUTED};">strategic rows</div>
  </div>
  <div style="background:rgba(8,18,34,0.78);border:1px solid rgba(168,85,247,0.22);border-radius:12px;padding:10px;">
    <div style="font-size:10px;color:{_PURPLE};font-weight:800;">Weekly</div>
    <div style="font-size:11px;color:{_WHITE};font-weight:700;">Last 7 Days</div>
    <div style="font-size:9px;color:{_MUTED};">{today_label}</div>
  </div>
  <div style="background:rgba(8,18,34,0.78);border:1px solid rgba(168,85,247,0.22);border-radius:12px;padding:10px;">
    <div style="font-size:10px;color:{_PURPLE};font-weight:800;">Monthly</div>
    <div style="font-size:11px;color:{_WHITE};font-weight:700;">Last 30 Days</div>
    <div style="font-size:9px;color:{_MUTED};">{month_label}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if _EXPORTS_OK:
            weekly_pdf = build_weekly_report_pdf("CyberNova Horizon - Executive", df, filters)
            monthly_pdf = build_monthly_report_pdf("CyberNova Horizon - Executive", df, filters)
            method_pdf = build_methodology_pdf("CyberNova Horizon - Executive")
            st.download_button(
                "Weekly PDF Report (Last 7 Days)",
                data=weekly_pdf,
                file_name="cybernova_executive_weekly_last_7_days.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="exec_weekly_pdf_real",
            )
            st.download_button(
                "Monthly PDF Report (Last 30 Days)",
                data=monthly_pdf,
                file_name="cybernova_executive_monthly_last_30_days.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="exec_monthly_pdf_real",
            )
            st.download_button(
                "Methodology PDF",
                data=method_pdf,
                file_name="cybernova_executive_methodology.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="exec_methodology_pdf_real",
            )
        else:
            st.markdown(
                f'<div style="font-size:10px;color:{_YELLOW};padding:8px 0;">PDF export module unavailable.</div>',
                unsafe_allow_html=True,
            )

    with c2:
        st.download_button(
            "Filtered Strategic Data CSV (Last 7 Days)",
            data=csv_weekly,
            file_name="cybernova_executive_filtered_data_last_7_days.csv",
            mime="text/csv",
            use_container_width=True,
            key="exec_filtered_csv_real",
        )
        st.download_button(
            "Filtered Strategic Data CSV (Last 30 Days)",
            data=csv_monthly,
            file_name="cybernova_executive_filtered_data_last_30_days.csv",
            mime="text/csv",
            use_container_width=True,
            key="exec_filtered_csv_30d_real",
        )
        st.download_button(
            "Regional Priority CSV",
            data=regional_priority.to_csv(index=False).encode("utf-8"),
            file_name="cybernova_executive_regional_priority.csv",
            mime="text/csv",
            use_container_width=True,
            key="exec_regional_csv_real",
        )

    with c3:
        st.download_button(
            "Risk Evidence CSV",
            data=risk_rows.to_csv(index=False).encode("utf-8"),
            file_name="cybernova_executive_risk_evidence.csv",
            mime="text/csv",
            use_container_width=True,
            key="exec_risk_csv_real",
        )
        summary_text = (
            "CyberNova Executive Summary\n\n"
            "Weekly reports cover the last 7 days from the current date.\n"
            "Monthly reports cover the last 30 days from the current date.\n"
            "PDF reports include KPI, market, service mix, daily trend, and evidence sections.\n"
        )
        st.download_button(
            "Executive Summary TXT",
            data=summary_text.encode("utf-8"),
            file_name="cybernova_executive_summary.txt",
            mime="text/plain",
            use_container_width=True,
            key="exec_summary_txt_real",
        )

    _card_close()


def render_executive_data(df, date_start=None, date_end=None):
    """Render Executive Data and Export tab."""
    inject_executive_css()

    with st.container(key="executive_data_scope"):
        # Item 1: Export Center
        _export_center(df)

        # Item 2: Decision Brief
        _decision_brief()

        # Item 3: Regional Priority Table
        _regional_priority_table()

        # Item 4: Risk Evidence Table
        _risk_evidence_table()

        # Item 5: Filtered Strategic Data
        _filtered_strategic_data(df, date_start, date_end)

        # Item 6: Summary statistics
        _executive_summary_statistics(df)

        # Item 7 + 8: Data Quality Summary + Methodology Note
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            _data_quality_summary()
        with c2:
            _methodology_note()
