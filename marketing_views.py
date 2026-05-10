"""
marketing_views.py - CyberNova BI Portal  -  Marketing Dashboard
Imported by cybernovaapp.py. Provides 5 public functions + CSS injection.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime

# ── COLOR CONSTANTS ──────────────────────────────────────────────────────────
_CYAN   = "#22D3EE"
_TEAL   = "#14B8A6"
_GREEN  = "#4ADE80"
_YELLOW = "#FBBF24"
_ORANGE = "#F59E0B"
_RED    = "#F87171"
_PURPLE = "#A855F7"
_GRAY   = "#6B7FA3"
_WHITE  = "#F0F4F8"

_BG_CARD   = "rgba(8,18,34,0.88)"
_BORDER    = "rgba(34,211,238,0.12)"
_BORDER_A  = "rgba(34,211,238,0.35)"
_MUTED     = "#6B7FA3"

# Try to import exports module
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

# ── SADC node data ────────────────────────────────────────────────────────────
_MKT_NODES = [
    {"country": "South Africa", "flag": "🇿🇦", "lat": -29.0, "lon": 25.1,
     "visitors": 4200, "eng_rate": 31, "potential": 450, "opp_score": 92,
     "status": "Core Market", "action": "Scale investment"},
    {"country": "Zambia",       "flag": "🇿🇲", "lat": -13.1, "lon": 27.8,
     "visitors": 1800, "eng_rate": 28, "potential": 180, "opp_score": 76,
     "status": "Growing",     "action": "Increase campaign frequency"},
    {"country": "Mozambique",   "flag": "🇲🇿", "lat": -18.7, "lon": 35.5,
     "visitors": 1400, "eng_rate": 25, "potential": 140, "opp_score": 68,
     "status": "Growing",     "action": "Target enterprise segment"},
    {"country": "Botswana",     "flag": "🇧🇼", "lat": -22.3, "lon": 24.7,
     "visitors": 950,  "eng_rate": 22, "potential": 95,  "opp_score": 61,
     "status": "Emerging",    "action": "Launch weekday campaigns"},
    {"country": "Angola",       "flag": "🇦🇴", "lat": -11.2, "lon": 17.9,
     "visitors": 720,  "eng_rate": 24, "potential": 72,  "opp_score": 58,
     "status": "Emerging",    "action": "Build brand awareness"},
    {"country": "Namibia",      "flag": "🇳🇦", "lat": -22.6, "lon": 17.1,
     "visitors": 550,  "eng_rate": 20, "potential": 55,  "opp_score": 52,
     "status": "Emerging",    "action": "Increase AI campaign exposure"},
    {"country": "Zimbabwe",     "flag": "🇿🇼", "lat": -19.0, "lon": 29.9,
     "visitors": 1100, "eng_rate": 27, "potential": 110, "opp_score": 70,
     "status": "Growing",     "action": "Promote Cloud & Data services"},
    {"country": "Malawi",       "flag": "🇲🇼", "lat": -13.3, "lon": 34.3,
     "visitors": 480,  "eng_rate": 18, "potential": 48,  "opp_score": 44,
     "status": "Emerging",    "action": "Build awareness first"},
    {"country": "DRC",          "flag": "🇨🇩", "lat": -4.0,  "lon": 21.8,
     "visitors": 320,  "eng_rate": 16, "potential": 32,  "opp_score": 38,
     "status": "Emerging",    "action": "Monitor only"},
]

_STATUS_COLOR = {
    "Core Market": _CYAN,
    "Growing":     _TEAL,
    "Emerging":    _YELLOW,
}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CSS INJECTION
# ═══════════════════════════════════════════════════════════════════════════════
def inject_marketing_css():
    """Inject Marketing-specific CSS classes not already in the main inject_css()."""
    st.markdown("""
<style>
/* ── Marketing insight card ──────────────────────────────────────────────── */
.mkt-insight-card {
  background: linear-gradient(145deg, rgba(12,24,44,0.95), rgba(8,18,34,0.92));
  border: 1px solid rgba(20,184,166,0.3);
  border-left: 3px solid #14B8A6;
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 8px;
  backdrop-filter: blur(12px);
}
/* ── Marketing status pill ───────────────────────────────────────────────── */
.mkt-pill-top    { background:rgba(74,222,128,0.12); color:#4ADE80; border:1px solid rgba(74,222,128,0.25); border-radius:20px; padding:2px 8px; font-size:9px; font-weight:700; }
.mkt-pill-grow   { background:rgba(34,211,238,0.12); color:#22D3EE; border:1px solid rgba(34,211,238,0.25); border-radius:20px; padding:2px 8px; font-size:9px; font-weight:700; }
.mkt-pill-stable { background:rgba(107,127,163,0.12); color:#6B7FA3; border:1px solid rgba(107,127,163,0.2);  border-radius:20px; padding:2px 8px; font-size:9px; font-weight:700; }
.mkt-pill-watch  { background:rgba(251,191,36,0.12); color:#FBBF24; border:1px solid rgba(251,191,36,0.25); border-radius:20px; padding:2px 8px; font-size:9px; font-weight:700; }
/* ── Quality progress bar ─────────────────────────────────────────────────── */
.mkt-bar-row   { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.mkt-bar-track { flex:1; height:6px; background:rgba(34,211,238,0.08); border-radius:3px; overflow:hidden; }
.mkt-bar-fill  { height:100%; border-radius:3px; transition:width .4s; }
/* ── Alert card ──────────────────────────────────────────────────────────── */
.mkt-alert { background:rgba(248,113,113,0.05); border:1px solid rgba(248,113,113,0.2);
  border-radius:10px; padding:10px 14px; margin-bottom:8px; font-size:12px; color:#F0F4F8; }
.mkt-alert.warn { background:rgba(251,191,36,0.05); border-color:rgba(251,191,36,0.2); }
/* ── Forecast signal card ─────────────────────────────────────────────────── */
.mkt-signal-card { background:rgba(8,18,34,0.78); border:1px solid rgba(34,211,238,0.12);
  border-radius:12px; padding:10px 14px; margin-bottom:8px;
  display:flex; align-items:center; gap:10px; }
/* ── Export card ─────────────────────────────────────────────────────────── */
.mkt-export-card { background:rgba(8,18,34,0.78); border:1px solid rgba(34,211,238,0.12);
  border-radius:14px; padding:14px 16px; margin-bottom:8px;
  transition:border-color .2s, transform .15s; cursor:pointer; }
.mkt-export-card:hover { border-color:rgba(34,211,238,0.4); transform:translateY(-1px); }
.st-key-marketing_analytics_scope div[data-testid="element-container"],
.st-key-marketing_forecasting_scope div[data-testid="element-container"],
.st-key-marketing_data_scope div[data-testid="element-container"] {
  height: auto !important;
  min-height: 0 !important;
}
.st-key-marketing_analytics_scope div[data-testid="stVerticalBlock"],
.st-key-marketing_forecasting_scope div[data-testid="stVerticalBlock"],
.st-key-marketing_data_scope div[data-testid="stVerticalBlock"] {
  gap: 14px !important;
}
.st-key-marketing_analytics_scope div[data-testid="stColumn"],
.st-key-marketing_forecasting_scope div[data-testid="stColumn"],
.st-key-marketing_data_scope div[data-testid="stColumn"] {
  min-width: 0 !important;
}
.st-key-marketing_analytics_scope div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
.st-key-marketing_forecasting_scope div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
.st-key-marketing_data_scope div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
  height: auto !important;
  min-height: 0 !important;
}
.st-key-marketing_analytics_scope .cn-card,
.st-key-marketing_forecasting_scope .cn-card,
.st-key-marketing_data_scope .cn-card,
.st-key-marketing_analytics_scope .kpi-card,
.st-key-marketing_forecasting_scope .kpi-card,
.st-key-marketing_data_scope .kpi-card,
.st-key-marketing_data_scope .mkt-export-card {
  width: 100%;
  min-width: 0;
  padding: 16px 18px;
  margin-bottom: 12px;
  overflow: visible;
  box-sizing: border-box;
  position: relative;
  transition: border-color .2s, box-shadow .2s, transform .15s;
}
.st-key-marketing_analytics_scope .sec-label,
.st-key-marketing_forecasting_scope .sec-label,
.st-key-marketing_data_scope .sec-label {
  min-height: 22px;
  line-height: 1.25;
  white-space: normal;
  overflow-wrap: anywhere;
}
.st-key-marketing_analytics_scope .cn-card:hover,
.st-key-marketing_forecasting_scope .cn-card:hover,
.st-key-marketing_data_scope .cn-card:hover,
.st-key-marketing_forecasting_scope .kpi-card:hover {
  border-color: rgba(20,184,166,0.58) !important;
  box-shadow: 0 0 30px rgba(20,184,166,0.18), 0 0 16px rgba(34,211,238,0.10), 0 2px 20px rgba(0,0,0,0.50) !important;
  transform: translateY(-1px);
}
.st-key-marketing_analytics_scope .cn-card::after,
.st-key-marketing_forecasting_scope .cn-card::after,
.st-key-marketing_forecasting_scope .kpi-card::after {
  display: none;
  position: absolute;
  z-index: 30;
  left: 12px;
  right: 12px;
  top: calc(100% + 7px);
  padding: 9px 10px;
  border-radius: 10px;
  background: rgba(4,9,15,.98);
  border: 1px solid rgba(20,184,166,.38);
  box-shadow: 0 14px 30px rgba(0,0,0,.42), 0 0 20px rgba(20,184,166,.15);
  color: #DDE7EE;
  font-size: 10.5px;
  line-height: 1.35;
  font-weight: 650;
  text-transform: none;
  letter-spacing: 0;
}
.st-key-marketing_analytics_scope .cn-card::after {
  content: "Insight: use this view to diagnose campaign behavior behind the overview recommendation.";
}
.st-key-marketing_forecasting_scope .cn-card::after,
.st-key-marketing_forecasting_scope .kpi-card::after {
  content: "Model note: this is a rule-based directional forecast using filtered activity and scenario assumptions. It is not predictive AI.";
}
.st-key-marketing_analytics_scope .cn-card:hover::after,
.st-key-marketing_forecasting_scope .cn-card:hover::after,
.st-key-marketing_forecasting_scope .kpi-card:hover::after {
  display: block;
}
.st-key-marketing_analytics_scope div[data-testid="stPlotlyChart"],
.st-key-marketing_forecasting_scope div[data-testid="stPlotlyChart"],
.st-key-marketing_data_scope div[data-testid="stPlotlyChart"] {
  width: 100% !important;
  min-width: 0 !important;
  overflow: hidden !important;
  margin-bottom: 6px !important;
}
.st-key-marketing_analytics_scope .js-plotly-plot,
.st-key-marketing_forecasting_scope .js-plotly-plot,
.st-key-marketing_data_scope .js-plotly-plot {
  max-width: 100% !important;
}
.st-key-marketing_analytics_scope [data-testid="stMarkdownContainer"],
.st-key-marketing_forecasting_scope [data-testid="stMarkdownContainer"],
.st-key-marketing_data_scope [data-testid="stMarkdownContainer"] {
  min-width: 0 !important;
  overflow-wrap: anywhere;
}
.st-key-marketing_analytics_scope table,
.st-key-marketing_forecasting_scope table,
.st-key-marketing_data_scope table {
  width: 100%;
  table-layout: fixed;
}
.st-key-marketing_analytics_scope th,
.st-key-marketing_analytics_scope td,
.st-key-marketing_forecasting_scope th,
.st-key-marketing_forecasting_scope td,
.st-key-marketing_data_scope th,
.st-key-marketing_data_scope td {
  white-space: normal !important;
  overflow-wrap: anywhere !important;
}
.st-key-marketing_data_scope div[data-testid="stDataFrame"],
.st-key-marketing_data_scope div[data-testid="stDataFrameResizable"] {
  width: 100% !important;
  min-width: 0 !important;
  overflow-x: auto !important;
}
.st-key-marketing_data_scope .stDownloadButton button {
  white-space: normal !important;
  min-height: 42px;
  height: auto;
  line-height: 1.25;
  padding: 10px 12px;
}
</style>
""", unsafe_allow_html=True)


# ── INTERNAL HELPERS ──────────────────────────────────────────────────────────
def _cl(fig, h=210):
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


def _card_open(title):
    st.markdown(
        f'<div class="cn-card"><div class="sec-label">{title}</div>',
        unsafe_allow_html=True,
    )


def _card_close():
    st.markdown("</div>", unsafe_allow_html=True)


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


def _marketing_summary_statistics(df):
    _card_open("Summary Statistics")
    work = df if df is not None and not df.empty else _mock_df()
    human = work[~_truthy_col(work, "is_bot")] if "is_bot" in work.columns else work
    engaged = int(_truthy_col(human, "is_engaged_session").sum()) if "is_engaged_session" in human.columns else int(len(human) * 0.28)
    potential = int(_truthy_col(human, "potential_customer_signal").sum()) if "potential_customer_signal" in human.columns else 0
    ai = int(_truthy_col(human, "has_ai_interest").sum()) if "has_ai_interest" in human.columns else (
        int(human["service_name"].astype(str).str.contains("AI", case=False, na=False).sum()) if "service_name" in human.columns else 0
    )
    top_market = human["country"].dropna().astype(str).value_counts().index[0] if "country" in human.columns and not human["country"].dropna().empty else "--"
    top_service = human["service_name"].dropna().astype(str).value_counts().index[0] if "service_name" in human.columns and not human["service_name"].dropna().empty else "--"
    rows = [
        ("Filtered rows", f"{len(work):,}"),
        ("Human audience", f"{len(human):,}"),
        ("Engaged sessions", f"{engaged:,}"),
        ("Engagement rate", f"{(engaged / len(human) * 100):.1f}%" if len(human) else "0.0%"),
        ("AI traction", f"{(ai / len(human) * 100):.1f}%" if len(human) else "0.0%"),
        ("Top service", top_service),
        ("Top market", top_market),
        ("Potential customers", f"{potential:,}"),
    ]
    st.markdown(_summary_table(rows), unsafe_allow_html=True)
    _card_close()


def _pill_html(label, cls="mkt-pill-grow"):
    return f'<span class="{cls}">{label}</span>'


def _mock_df():
    """Generate clean mock marketing DataFrame."""
    np.random.seed(42)
    n = 500
    countries = ["South Africa", "Zambia", "Mozambique", "Botswana", "Angola",
                 "Namibia", "Zimbabwe", "Malawi"]
    services  = ["AI Cyber Assistant", "Cybersecurity Services", "Cloud & Data",
                 "Advisory & Training", "Homepage", "Contact Page"]
    segments  = ["High-Intent", "Product-Curious", "General Browsers", "Low-Intent"]
    dates = pd.date_range(end=datetime.date.today(), periods=30, freq="D")
    df = pd.DataFrame({
        "date":                  np.random.choice(dates, n),
        "country":               np.random.choice(countries, n, p=[0.3,0.18,0.14,0.1,0.08,0.07,0.08,0.05]),
        "service_name":          np.random.choice(services, n),
        "segment":               np.random.choice(segments, n, p=[0.25,0.35,0.28,0.12]),
        "potential_customer_signal": np.random.choice([True, False], n, p=[0.28, 0.72]),
        "estimated_deal_value":  np.random.randint(20000, 200000, n),
        "engagement_score":      np.random.randint(10, 95, n),
        "is_bot":                np.random.choice([True, False], n, p=[0.15, 0.85]),
    })
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MARKETING DRAWER (returns HTML string)
# ═══════════════════════════════════════════════════════════════════════════════
def render_marketing_drawer() -> str:
    """Returns HTML string for the 3 insight cards used in the right-panel drawer."""
    return """
<div class="cn-card" style="margin-bottom:10px;">
  <div class="sec-label">Best Campaign Market</div>
  <div style="font-size:18px;font-weight:800;color:#14B8A6;margin-bottom:4px;">South Africa 🇿🇦</div>
  <div style="font-size:10px;color:#6B7FA3;">31% engagement &middot; Highest quality audience</div>
  <div style="margin-top:8px;font-size:11px;color:#4ADE80;font-weight:600;">
    &rarr; Increase campaign exposure here
  </div>
</div>

<div class="cn-card" style="margin-bottom:10px;">
  <div class="sec-label">Campaign Signals</div>
  <div style="font-size:11px;margin-bottom:6px;color:#F0F4F8;">
    <span style="color:#4ADE80;">&#9679;</span>&nbsp; AI Solutions &mdash; <b>High Intent</b>
  </div>
  <div style="font-size:11px;margin-bottom:6px;color:#F0F4F8;">
    <span style="color:#FBBF24;">&#9679;</span>&nbsp; Cybersecurity &mdash; <b>Under-Promoted</b>
  </div>
  <div style="font-size:11px;color:#F0F4F8;">
    <span style="color:#22D3EE;">&#9679;</span>&nbsp; Cloud &amp; Data &mdash; <b>Growing</b>
  </div>
</div>

<div class="cn-card" style="margin-bottom:10px;">
  <div class="sec-label">Audience Quality Outlook</div>
  <div style="font-size:28px;font-weight:800;color:#14B8A6;text-align:center;padding:6px 0;">78%</div>
  <div style="background:rgba(34,211,238,0.08);border-radius:4px;height:8px;overflow:hidden;margin:4px 0 6px;">
    <div style="width:78%;height:100%;background:linear-gradient(90deg,#14B8A6,#22D3EE);border-radius:4px;"></div>
  </div>
  <div style="font-size:10px;color:#6B7FA3;text-align:center;">Human audience quality score</div>
</div>

<div class="cn-card">
  <div class="sec-label">Recommended Action</div>
  <div style="font-size:11px;color:#F0F4F8;line-height:1.6;">
    Increase AI Assistant campaign exposure in Botswana and Namibia during weekday
    late-morning engagement windows.
  </div>
</div>
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ANALYTICS TAB
# ═══════════════════════════════════════════════════════════════════════════════

# ── A. Audience Segments Over Time ───────────────────────────────────────────
def _audience_segments_over_time(df):
    np.random.seed(42)
    dates = pd.date_range(end=datetime.date.today(), periods=30, freq="D")
    dates_str = [d.strftime("%b %d") for d in dates]

    hi     = 280 + np.cumsum(np.random.randint(-8, 14, 30))
    pc     = 420 + np.cumsum(np.random.randint(-10, 10, 30))
    gb     = 360 + np.cumsum(np.random.randint(-12, 8,  30))
    li     = 180 + np.cumsum(np.random.randint(-5, 5,   30))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates_str, y=li, name="Low-Intent",
        fill="tozeroy", fillcolor="rgba(107,127,163,0.12)",
        line=dict(color=_GRAY, width=1.5),
        hovertemplate="Low-Intent: <b>%{y}</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=dates_str, y=gb, name="General Browsers",
        fill="tonexty", fillcolor="rgba(251,191,36,0.10)",
        line=dict(color=_YELLOW, width=1.5),
        hovertemplate="General: <b>%{y}</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=dates_str, y=pc, name="Product-Curious",
        fill="tonexty", fillcolor="rgba(20,184,166,0.12)",
        line=dict(color=_TEAL, width=2),
        hovertemplate="Product-Curious: <b>%{y}</b><extra></extra>"))
    fig.add_trace(go.Scatter(x=dates_str, y=hi, name="High-Intent",
        fill="tonexty", fillcolor="rgba(34,211,238,0.14)",
        line=dict(color=_CYAN, width=2.5),
        mode="lines+markers",
        marker=dict(size=5, color=_CYAN, line=dict(color="rgba(255,255,255,0.2)", width=1)),
        hovertemplate="High-Intent: <b>%{y}</b><extra></extra>"))

    _cl(fig, 240)
    fig.update_layout(xaxis=dict(tickangle=-35, tickfont=dict(size=9, color="#CBD5E1"), automargin=True))
    _card_open("Audience Segments Over Time")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


# ── B. Country Engagement Breakdown ──────────────────────────────────────────
def _country_engagement_breakdown():
    countries = [
        "Malawi 🇲🇼", "Namibia 🇳🇦", "Angola 🇦🇴", "Botswana 🇧🇼",
        "Mozambique 🇲🇿", "Zimbabwe 🇿🇼", "Zambia 🇿🇲", "South Africa 🇿🇦",
    ]
    visitors    = [480, 550, 720, 950, 1400, 1100, 1800, 4200]
    eng_rates   = [18,  20,  24,  22,  25,   27,   28,   31  ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=countries, x=visitors, orientation="h", name="Visitors",
        marker_color="rgba(107,127,163,0.55)",
        hovertemplate="<b>%{y}</b><br>Visitors: %{x:,}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        y=countries, x=[v * r / 31 * 1.6 for v, r in zip(visitors, eng_rates)],
        mode="markers", name="Engagement Rate",
        marker=dict(size=10, color=_CYAN, symbol="diamond",
                    line=dict(color="rgba(34,211,238,0.5)", width=1)),
        customdata=eng_rates,
        hovertemplate="<b>%{y}</b><br>Engagement Rate: %{customdata}%<extra></extra>",
    ))

    _cl(fig, 240)
    fig.update_layout(
        barmode="overlay",
        yaxis=dict(color=_WHITE, tickfont=dict(size=9)),
        xaxis=dict(title="Visitors", color=_MUTED),
        showlegend=True,
    )
    _card_open("Country Engagement Breakdown")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


# ── C. Landing Page Performance ───────────────────────────────────────────────
def _landing_page_performance():
    pages = [
        ("Homepage",                1850, "12.4%", 142, 38, "4.5%",  "Stable",       "mkt-pill-stable"),
        ("AI Cyber Assistant",      1240, "38.2%", 480, 92, "14.8%", "Top Performer","mkt-pill-top"),
        ("Cybersecurity Services",  980,  "22.1%", 210, 28, "8.2%",  "Needs Attention","mkt-pill-watch"),
        ("Cloud & Data",            760,  "29.4%", 224, 44, "9.8%",  "Growing",      "mkt-pill-grow"),
        ("Advisory & Training",     540,  "18.7%", 101, 16, "5.9%",  "Stable",       "mkt-pill-stable"),
        ("Contact Page",            420,  "41.9%", 176, 64, "20.5%", "Top Performer","mkt-pill-top"),
    ]
    header = (
        '<div style="display:flex;padding:6px 10px;border-bottom:1px solid rgba(34,211,238,0.14);">'
        + "".join(
            f'<span style="flex:{f};font-size:8px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:{_MUTED};">{h}</span>'
            for h, f in [("Landing Page",2),("Visitors",1),("Eng Rate",1),("Svc Clicks",1),("Actions",1),("Conv Rate",1),("Status",1.2)]
        )
        + "</div>"
    )
    rows_html = "".join(
        f'<div style="display:flex;align-items:center;padding:8px 10px;'
        f'border-bottom:1px solid rgba(34,211,238,0.05);">'
        f'<span style="flex:2;font-size:11px;color:#F0F4F8;font-weight:500;">{page}</span>'
        f'<span style="flex:1;font-size:11px;color:{_CYAN};font-weight:600;">{visitors:,}</span>'
        f'<span style="flex:1;font-size:11px;color:{_TEAL};">{eng}</span>'
        f'<span style="flex:1;font-size:11px;color:{_WHITE};">{clicks}</span>'
        f'<span style="flex:1;font-size:11px;color:{_WHITE};">{actions}</span>'
        f'<span style="flex:1;font-size:11px;color:{_GREEN};font-weight:600;">{conv}</span>'
        f'<span style="flex:1.2;"><span class="{pill}">{status}</span></span>'
        f'</div>'
        for page, visitors, eng, clicks, actions, conv, status, pill in pages
    )

    _card_open("Landing Page Performance")
    st.markdown(
        f'<div style="overflow-y:auto;max-height:280px;border:1px solid rgba(34,211,238,0.08);border-radius:10px;">'
        f'{header}{rows_html}</div>',
        unsafe_allow_html=True,
    )
    _card_close()


# ── D. Service Promotion Gap ───────────────────────────────────────────────────
def _service_promotion_gap():
    services     = ["AI Solutions", "Cybersecurity", "Cloud & Data", "Advisory", "Other"]
    visit_share  = [35, 18, 22, 14, 11]
    conv_share   = [42, 28, 20, 6,  4]
    under        = [False, True, False, False, False]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=services, x=visit_share, orientation="h", name="Visit Share %",
        marker_color="rgba(58,74,94,0.8)",
        hovertemplate="<b>%{y}</b><br>Visit Share: %{x}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=services, x=conv_share, orientation="h", name="Conversion Share %",
        marker_color="rgba(34,211,238,0.7)",
        hovertemplate="<b>%{y}</b><br>Conv Share: %{x}%<extra></extra>",
    ))

    _cl(fig, 220)
    fig.update_layout(
        barmode="group", bargap=0.25,
        yaxis=dict(color=_WHITE, tickfont=dict(size=9)),
        xaxis=dict(title="Share %", color=_MUTED),
    )

    _card_open("Service Promotion Gap")
    st.markdown(
        f'<div style="font-size:9px;color:{_YELLOW};margin-bottom:6px;">'
        f'Cybersecurity: high conversion, low visit share - under-promoted opportunity</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    # Under-promoted tag
    gap_rows = "".join(
        f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;">'
        f'<span style="font-size:11px;color:{_WHITE};">{s}</span>'
        f'{"<span style=\'background:rgba(251,191,36,0.12);color:#FBBF24;border:1px solid rgba(251,191,36,0.25);border-radius:20px;padding:1px 7px;font-size:9px;font-weight:700;\'>Under-Promoted</span>" if u else ""}'
        f'<span style="font-size:10px;color:{_MUTED};margin-left:auto;">Visit {vs}% vs Conv {cs}%</span>'
        f'</div>'
        for s, vs, cs, u in zip(services, visit_share, conv_share, under)
    )
    st.markdown(
        f'<div style="margin-top:8px;border-top:1px solid rgba(34,211,238,0.08);padding-top:8px;">'
        f'{gap_rows}</div>',
        unsafe_allow_html=True,
    )
    _card_close()


# ── E. Channel / Source Quality ───────────────────────────────────────────────
def _channel_source_quality():
    channels = ["Organic Search", "Direct", "Social", "Referral", "Email", "Paid Campaign"]
    engaged  = [1820, 1340, 680, 520, 410, 290]
    conv_r   = [8.2,  7.1,  4.8, 6.3, 9.4, 5.7]
    potential = [149, 95,   33,  33,  38,  17]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=channels, y=engaged, name="Engaged Visitors",
        marker_color="rgba(20,184,166,0.7)",
        hovertemplate="<b>%{x}</b><br>Engaged: %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=channels, y=[c * 80 for c in conv_r], name="Conv Rate (scaled)",
        marker_color="rgba(34,211,238,0.65)",
        hovertemplate="<b>%{x}</b><br>Conv Rate: " +
                      "%{customdata:.1f}%<extra></extra>",
        customdata=conv_r,
    ))
    fig.add_trace(go.Bar(
        x=channels, y=[p * 5 for p in potential], name="Potential Customers (scaled)",
        marker_color="rgba(74,222,128,0.6)",
        hovertemplate="<b>%{x}</b><br>Potential: " +
                      "%{customdata}<extra></extra>",
        customdata=potential,
    ))

    _cl(fig, 240)
    fig.update_layout(
        barmode="group", bargap=0.2,
        xaxis=dict(tickangle=-25, tickfont=dict(size=9, color="#CBD5E1"), automargin=True),
        yaxis=dict(title="Count", color="#94A3B8", tickfont=dict(size=10, color="#CBD5E1"), automargin=True),
    )

    _card_open("Channel / Source Quality")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


# ── F. SADC Reach Map + Ranking ───────────────────────────────────────────────
def _sadc_reach_map():
    fig = go.Figure()
    for status, color in _STATUS_COLOR.items():
        nodes = [n for n in _MKT_NODES if n["status"] == status]
        if not nodes:
            continue
        hover = [
            f"<b>{n['country']}</b><br>Visitors: {n['visitors']:,}<br>"
            f"Engagement: {n['eng_rate']}%<br>Potential: {n['potential']}<br>"
            f"Opp Score: {n['opp_score']}"
            for n in nodes
        ]
        fig.add_trace(go.Scattermap(
            lat=[n["lat"] for n in nodes],
            lon=[n["lon"] for n in nodes],
            mode="markers",
            name=status,
            marker=dict(
                size=[max(10, n["visitors"] / 140) for n in nodes],
                color=color,
                opacity=0.85,
                sizemode="area",
            ),
            text=hover,
            hoverinfo="text",
        ))

    fig.update_layout(
        map=dict(style="carto-darkmatter", center=dict(lat=-15, lon=26), zoom=2.8),
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            bgcolor="rgba(9,20,36,0.85)",
            bordercolor="rgba(34,211,238,0.18)",
            borderwidth=1,
            font=dict(color=_WHITE, size=9),
            orientation="v", x=0.01, y=0.98,
        ),
    )

    _card_open("Campaign Hotzones Map")
    st.markdown(
        '<div style="font-size:11px;color:#6B7FA3;margin:-2px 0 8px;">Use this map to explore where marketing activity is coming from.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

    # Ranking table below map
    header = (
        '<div style="display:flex;padding:5px 8px;border-bottom:1px solid rgba(34,211,238,0.12);">'
        + "".join(
            f'<span style="flex:{f};font-size:8px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:{_MUTED};">{h}</span>'
            for h, f in [("Country",2),("Eng Rate",1),("Potential",1),("Opp Score",1),("Recommended Action",2)]
        )
        + "</div>"
    )
    sorted_nodes = sorted(_MKT_NODES, key=lambda n: n["opp_score"], reverse=True)
    rows_html = "".join(
        f'<div style="display:flex;align-items:center;padding:6px 8px;'
        f'border-bottom:1px solid rgba(34,211,238,0.05);">'
        f'<span style="flex:2;font-size:11px;color:{_WHITE};font-weight:500;">{n["flag"]} {n["country"]}</span>'
        f'<span style="flex:1;font-size:11px;color:{_TEAL};font-weight:600;">{n["eng_rate"]}%</span>'
        f'<span style="flex:1;font-size:11px;color:{_CYAN};">{n["potential"]}</span>'
        f'<span style="flex:1;font-size:11px;color:{_score_color(n["opp_score"])};font-weight:700;">{n["opp_score"]}</span>'
        f'<span style="flex:2;font-size:10px;color:{_MUTED};">{n["action"]}</span>'
        f'</div>'
        for n in sorted_nodes
    )
    st.markdown(
        f'<div style="overflow-y:auto;max-height:260px;border:1px solid rgba(34,211,238,0.08);'
        f'border-radius:10px;margin-top:10px;">{header}{rows_html}</div>',
        unsafe_allow_html=True,
    )
    _card_close()


def _score_color(score: int) -> str:
    if score >= 75: return _GREEN
    if score >= 55: return _YELLOW
    return _RED


# ── G. Marketing Insight Assistant ───────────────────────────────────────────
def _marketing_insight_assistant():
    insights = [
        ("South Africa leads SADC with 4,200 visitors and a 31% engagement rate - strongest campaign ROI in the region.", _GREEN),
        ("Cybersecurity Services shows high conversion share (28%) vs. low visit share (18%) - significantly under-promoted.", _YELLOW),
        ("Email and Organic Search deliver the highest conversion rates (9.4% and 8.2%) - prioritise these channels.", _CYAN),
        ("Botswana and Namibia show emerging audience growth - weekday late-morning windows show highest engagement density.", _TEAL),
        ("AI Cyber Assistant landing page drives 14.8% conversion - recommended as primary campaign destination for high-intent segments.", _CYAN),
    ]
    rows_html = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:9px 0;'
        f'border-bottom:1px solid rgba(34,211,238,0.06);">'
        f'<div style="width:8px;height:8px;border-radius:50%;background:{color};'
        f'flex-shrink:0;margin-top:4px;box-shadow:0 0 6px {color};"></div>'
        f'<span style="font-size:12px;color:{_WHITE};line-height:1.55;">{text}</span>'
        f'</div>'
        for text, color in insights
    )

    st.markdown(
        f"""
<div class="mkt-insight-card">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="#14B8A6" stroke-width="1.5"/>
      <path d="M12 8v4l3 3" stroke="#22D3EE" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <div>
      <div style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{_CYAN};">
        CyberNova Intelligence &middot; Marketing Insights
      </div>
      <div style="font-size:9px;color:{_MUTED};">Intelligence summary &middot; Updated live</div>
    </div>
  </div>
  {rows_html}
</div>
""",
        unsafe_allow_html=True,
    )


# ── Main analytics renderer ───────────────────────────────────────────────────
def render_marketing_analytics(df):
    inject_marketing_css()
    if df is None:
        df = _mock_df()

    with st.container(key="marketing_analytics_scope"):
        # Row 1 - 2 columns
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            _audience_segments_over_time(df)
        with c2:
            _country_engagement_breakdown()

        # Row 2 - full width landing page table
        _landing_page_performance()

        # Row 3 - 2 columns
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            _service_promotion_gap()
        with c2:
            _channel_source_quality()

        # Row 4 - full width map + ranking
        _sadc_reach_map()

        # Row 5 - full width insight assistant
        _marketing_insight_assistant()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FORECASTING TAB
# ═══════════════════════════════════════════════════════════════════════════════

# ── A. Forecast KPI row ───────────────────────────────────────────────────────
def _forecast_kpis():
    kpis = [
        ("Forecasted Engaged Visitors", "4,200",  "next 30 days",      "+ 9.4%",    "up",   _CYAN),
        ("Campaign Visits Forecast",     "1,450",  "vs current 1,240",  "+ 16.9%",  "up",   _TEAL),
        ("Expected Potential Customers", "380",    "next 30 days",      "+ 12.4%",  "up",   _GREEN),
        ("Forecasted Opportunity Value", "P2.1M",  "pipeline estimate", "+ 18.7%",  "up",   _PURPLE),
        ("Forecast Confidence",          "74%",    "medium accuracy",   "Medium",    "watch",_YELLOW),
    ]
    delta_cls = {"up": "delta-up", "watch": "delta-watch", "down": "delta-down"}
    cols = st.columns(5, gap="small")
    for col, (lbl, val, sub, chg, cls, accent) in zip(cols, kpis):
        with col:
            d_cls = delta_cls.get(cls, "delta-up")
            delta = f'<div class="kpi-delta {d_cls}" style="margin-bottom:5px;">{chg}</div>' if chg else ""
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-label">{lbl}</div>'
                f'<div class="kpi-value-sm" style="color:{accent};margin-bottom:5px;">{val}</div>'
                f'{delta}'
                f'<div class="kpi-sub">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── B. Audience Growth Forecast by Country ────────────────────────────────────
def _audience_growth_forecast():
    np.random.seed(42)
    hist_days = list(range(-30, 1))
    fwd_days  = list(range(0, 31))

    countries_data = [
        ("South Africa", _CYAN,   3800, 5.2, "rgba(34,211,238,0.07)"),
        ("Zambia",        _TEAL,  1600, 3.1, "rgba(20,184,166,0.07)"),
        ("Botswana",      _YELLOW, 900, 1.8, "rgba(251,191,36,0.07)"),
        ("Namibia",       _ORANGE, 520, 1.2, "rgba(245,158,11,0.07)"),
        ("Mozambique",    _GREEN, 1300, 2.4, "rgba(74,222,128,0.07)"),
    ]

    fig = go.Figure()
    for country, color, base, slope, band_color in countries_data:
        act = [int(base + i * slope + np.random.randint(-20, 20)) for i in range(31)]
        fwd_base = act[-1]
        fwd = [int(fwd_base + i * slope * 1.1) for i in range(31)]
        upper = [v + int(30 + i * 0.5) for i, v in enumerate(fwd)]
        lower = [v - int(30 + i * 0.5) for i, v in enumerate(fwd)]

        fig.add_trace(go.Scatter(
            x=hist_days, y=act, name=country,
            line=dict(color=color, width=2), mode="lines",
            showlegend=True,
            hovertemplate=f"<b>{country}</b><br>Day %{{x}}<br>Visitors: %{{y:,}}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=fwd_days, y=fwd, name=f"{country} Forecast",
            line=dict(color=color, width=1.5, dash="dash"), mode="lines",
            showlegend=False,
            hovertemplate=f"<b>{country} Fcst</b><br>Day %{{x}}<br>%{{y:,}}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=fwd_days + fwd_days[::-1],
            y=upper + lower[::-1],
            fill="toself",
            fillcolor=band_color,
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Confidence band fill tweak - just use generic rgba for simplicity
    target_line = [4500 + i * 6 for i in range(31)]
    fig.add_trace(go.Scatter(
        x=fwd_days, y=target_line, name="Target",
        line=dict(color=_PURPLE, width=1.5, dash="dash"), mode="lines",
        hovertemplate="Target: %{y:,}<extra></extra>",
    ))
    fig.add_vline(x=0, line_color=_ORANGE, line_width=1.2,
                  annotation_text="Today", annotation_font_color=_ORANGE, annotation_font_size=9)

    _cl(fig, 220)
    fig.update_layout(yaxis_title="Visitors")

    _card_open("Audience Growth Forecast by Country")
    st.markdown(
        f'<div style="font-size:9px;color:{_YELLOW};margin-bottom:5px;">'
        f'Rule-based linear forecast, not predictive AI. Dashed = forecast, purple = target.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


# ── C. Engaged Sessions Forecast ─────────────────────────────────────────────
def _engaged_sessions_forecast():
    np.random.seed(7)
    hist_days = list(range(-30, 1))
    fwd_days  = list(range(0, 31))

    act    = [1100 + i * 3.8 + np.random.randint(-12, 12) for i in range(31)]
    fwd_base = act[-1]
    fwd    = [int(fwd_base + i * 4.1) for i in range(31)]
    upper  = [v + 40 + int(i * 0.6) for i, v in enumerate(fwd)]
    lower  = [v - 40 - int(i * 0.6) for i, v in enumerate(fwd)]
    target = [1280 + i * 4.5 for i in range(31)]
    prev   = [1020 + i * 3.2 + np.random.randint(-8, 8) for i in range(31)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fwd_days + fwd_days[::-1], y=upper + lower[::-1],
        fill="toself", fillcolor="rgba(20,184,166,0.08)",
        line=dict(width=0), name="Confidence Band",
    ))
    fig.add_trace(go.Scatter(
        x=hist_days, y=act, name="Actual",
        line=dict(color=_TEAL, width=2.5), mode="lines",
        hovertemplate="Day %{x}<br>Actual: %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=fwd_days, y=fwd, name="Forecast",
        line=dict(color=_TEAL, width=2, dash="dash"), mode="lines",
        hovertemplate="Day %{x}<br>Forecast: %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=fwd_days, y=target, name="Target",
        line=dict(color=_PURPLE, width=1.5, dash="dash"), mode="lines",
        hovertemplate="Day %{x}<br>Target: %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=hist_days, y=prev, name="Prev Month",
        line=dict(color="rgba(58,74,94,0.8)", width=1.5, dash="dot"), mode="lines",
        marker=dict(size=3, color="#3A4A5E"),
        hovertemplate="Day %{x}<br>Prev: %{y:,}<extra></extra>",
    ))
    fig.add_vline(x=0, line_color=_ORANGE, line_width=1.2,
                  annotation_text="Today", annotation_font_color=_ORANGE, annotation_font_size=9)

    _cl(fig, 220)
    fig.update_layout(yaxis_title="Engaged Sessions")

    _card_open("Engaged Sessions Forecast")
    st.markdown(
        f'<div style="font-size:9px;color:{_YELLOW};margin-bottom:5px;">'
        f'Rule-based linear forecast. Purple dashed = target, gray dotted = previous month actual.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


# ── D. Campaign What-If Scenario ─────────────────────────────────────────────
def _campaign_whatif():
    _card_open("Campaign What-If Scenario")

    lift_pct = st.slider(
        "Campaign Lift %",
        min_value=0, max_value=30, value=st.session_state.get("mkt_whatif_lift", 10),
        step=1, key="mkt_whatif_lift",
    )

    base_visitors    = 3840
    base_potential   = 338
    base_opp_value   = 1_800_000
    deal_value_avg   = 5325

    additional_visitors  = int(base_visitors * lift_pct / 100)
    additional_potential = int(base_potential * lift_pct / 100 * 0.85)
    additional_opp       = additional_potential * deal_value_avg

    c1, c2, c3 = st.columns(3)
    for col, (label, val, color, bg) in zip(
        [c1, c2, c3],
        [
            ("Additional Engaged Visitors",    f"+{additional_visitors:,}",          _CYAN,   "rgba(34,211,238,0.08)"),
            ("Additional Potential Customers", f"+{additional_potential}",            _GREEN,  "rgba(74,222,128,0.08)"),
            ("Estimated Opportunity Value",    f"+P{additional_opp/1000:.0f}K",      _PURPLE, "rgba(168,85,247,0.08)"),
        ],
    ):
        with col:
            st.markdown(
                f'<div style="background:{bg};border:1px solid rgba(34,211,238,0.15);'
                f'border-radius:12px;padding:14px;text-align:center;">'
                f'<div style="font-size:9px;font-weight:700;color:{_MUTED};text-transform:uppercase;'
                f'letter-spacing:.1em;margin-bottom:8px;">{label}</div>'
                f'<div style="font-size:1.5rem;font-weight:800;color:{color};">{val}</div>'
                f'<div style="font-size:9px;color:{_MUTED};margin-top:4px;">at {lift_pct}% lift</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    _card_close()


# ── E. Campaign Target Tracker ────────────────────────────────────────────────
def _campaign_target_tracker():
    days = [f"Day {i}" for i in range(1, 8)]
    actual    = [210, 195, 228, 244, 198, 232, 218]
    forecast  = [220, 210, 235, 250, 212, 240, 228]
    target    = [225] * 7

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=days, y=actual, name="Actual",
        marker_color="rgba(20,184,166,0.75)",
        hovertemplate="<b>%{x}</b><br>Actual: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=days, y=forecast, name="Forecasted End-of-Day",
        marker_color="rgba(34,211,238,0.5)",
        hovertemplate="<b>%{x}</b><br>Forecasted: %{y}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=days, y=target, name="Daily Target",
        line=dict(color=_PURPLE, width=2, dash="dash"), mode="lines",
        hovertemplate="Target: %{y}<extra></extra>",
    ))

    _cl(fig, 220)
    fig.update_layout(barmode="group", bargap=0.2, yaxis_title="Campaign Visits")

    _card_open("Campaign Target Tracker")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})
    _card_close()


# ── F. Campaign Recommendation Card ──────────────────────────────────────────
def _campaign_recommendations():
    items = [
        ("Increase AI Cyber Assistant campaign exposure in Botswana and Namibia "
         "during weekday late-morning windows (09:00–11:00).", True),
        ("Promote Cybersecurity Services more aggressively - high conversion share "
         "but chronically under-promoted in visit share.", True),
        ("Prioritise Email and Organic Search channels - they deliver the highest "
         "conversion rates across SADC markets.", False),
        ("Retarget Product-Curious segment with Cloud & Data landing page - "
         "this segment shows 29% engagement rate.", False),
    ]

    checkmark_svg = (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="flex-shrink:0;margin-top:2px;">'
        '<circle cx="12" cy="12" r="10" fill="rgba(74,222,128,0.15)" stroke="#4ADE80" stroke-width="1.5"/>'
        '<path d="M8 12l3 3 5-5" stroke="#4ADE80" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    )
    circle_svg = (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="flex-shrink:0;margin-top:2px;">'
        '<circle cx="12" cy="12" r="10" fill="rgba(34,211,238,0.08)" stroke="#22D3EE" stroke-width="1.5"/>'
        '</svg>'
    )

    rows_html = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:10px;padding:9px 0;'
        f'border-bottom:1px solid rgba(34,211,238,0.06);">'
        f'{checkmark_svg if done else circle_svg}'
        f'<span style="font-size:12px;color:{_WHITE};line-height:1.5;">{text}</span>'
        f'</div>'
        for text, done in items
    )

    st.markdown(
        f'<div class="cn-card">'
        f'<div class="sec-label">Campaign Recommendations</div>'
        f'{rows_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── G. Marketing Alert Card ───────────────────────────────────────────────────
def _marketing_alerts():
    alerts = [
        ("Cybersecurity Services visit share dropped 3.2% this week despite high conversion - immediate campaign boost needed.", "high"),
        ("Angola engagement rate fell below 20% - review campaign targeting and creative.", "warn"),
        ("Malawi and DRC show minimal organic traffic - awareness campaigns not yet seeded.", "warn"),
        ("Email campaign open rates declining - consider A/B testing subject lines for SADC markets.", "warn"),
    ]

    _card_open("Marketing Alert Center")
    for msg, cls in alerts:
        dot_color = _RED if cls == "high" else _YELLOW
        card_cls  = "mkt-alert" if cls == "high" else "mkt-alert warn"
        st.markdown(
            f'<div class="{card_cls}">'
            f'<div style="display:flex;align-items:flex-start;gap:8px;">'
            f'<div style="width:8px;height:8px;border-radius:50%;background:{dot_color};'
            f'flex-shrink:0;margin-top:4px;box-shadow:0 0 6px {dot_color};"></div>'
            f'<span style="font-size:12px;line-height:1.5;">{msg}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    _card_close()


# ── Main forecasting renderer ─────────────────────────────────────────────────
def render_marketing_forecasting(df):
    inject_marketing_css()
    if df is None:
        df = _mock_df()

    with st.container(key="marketing_forecasting_scope"):
        # KPI row
        _forecast_kpis()
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        # Row 1
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            _audience_growth_forecast()
        with c2:
            _engaged_sessions_forecast()

        # Row 2
        _campaign_whatif()

        # Row 3
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            _campaign_target_tracker()
        with c2:
            _campaign_recommendations()

        # Row 4
        _marketing_alerts()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DATA & EXPORT TAB
# ═══════════════════════════════════════════════════════════════════════════════

# ── A. Campaign Opportunity Table ─────────────────────────────────────────────
def _campaign_opportunity_table():
    rows = [
        ("South Africa", "🇿🇦", 4200, "31%", 450, 92, "Scale investment - highest quality audience"),
        ("Zambia",        "🇿🇲", 1800, "28%", 180, 76, "Increase campaign frequency"),
        ("Zimbabwe",      "🇿🇼", 1100, "27%", 110, 70, "Promote Cloud & Data services"),
        ("Mozambique",    "🇲🇿", 1400, "25%", 140, 68, "Target enterprise segment"),
        ("Angola",        "🇦🇴", 720,  "24%",  72, 58, "Build brand awareness"),
        ("Botswana",      "🇧🇼", 950,  "22%",  95, 61, "Launch weekday campaigns"),
        ("Namibia",       "🇳🇦", 550,  "20%",  55, 52, "Increase AI campaign exposure"),
        ("Malawi",        "🇲🇼", 480,  "18%",  48, 44, "Build awareness first"),
    ]
    header = (
        '<div style="display:flex;padding:6px 10px;border-bottom:1px solid rgba(34,211,238,0.14);">'
        + "".join(
            f'<span style="flex:{f};font-size:8px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:{_MUTED};">{h}</span>'
            for h, f in [("Country",2),("Visitors",1),("Eng Rate",1),("Potential",1),("Opp Score",1),("Recommended Action",2.5)]
        )
        + "</div>"
    )
    rows_html = "".join(
        f'<div style="display:flex;align-items:center;padding:8px 10px;'
        f'border-bottom:1px solid rgba(34,211,238,0.05);">'
        f'<span style="flex:2;font-size:12px;color:{_WHITE};font-weight:500;">{flag} {country}</span>'
        f'<span style="flex:1;font-size:12px;color:{_CYAN};font-weight:600;">{visitors:,}</span>'
        f'<span style="flex:1;font-size:12px;color:{_TEAL};">{eng}</span>'
        f'<span style="flex:1;font-size:12px;color:{_WHITE};">{potential}</span>'
        f'<span style="flex:1;font-size:12px;color:{_score_color(opp)};font-weight:700;">{opp}</span>'
        f'<span style="flex:2.5;font-size:10px;color:{_MUTED};">{action}</span>'
        f'</div>'
        for country, flag, visitors, eng, potential, opp, action in rows
    )

    _card_open("Campaign Opportunity Table")
    st.markdown(
        f'<div style="overflow-y:auto;max-height:300px;border:1px solid rgba(34,211,238,0.08);border-radius:10px;">'
        f'{header}{rows_html}</div>',
        unsafe_allow_html=True,
    )
    _card_close()


# ── B. Filtered Audience Data ─────────────────────────────────────────────────
def _filtered_audience_data(df, date_start=None, date_end=None):
    _card_open("Filtered Audience Data")

    show_cols = ["date", "country", "service_name", "segment",
                 "potential_customer_signal", "estimated_deal_value"]

    if df is not None:
        filtered = df[~df["is_bot"]] if "is_bot" in df.columns else df
        # Apply date filter
        if date_start and "date" in filtered.columns:
            try:
                filtered = filtered[pd.to_datetime(filtered["date"]).dt.date >= date_start]
            except Exception:
                pass
        if date_end and "date" in filtered.columns:
            try:
                filtered = filtered[pd.to_datetime(filtered["date"]).dt.date <= date_end]
            except Exception:
                pass
        # Add missing columns as mock
        for col in show_cols:
            if col not in filtered.columns:
                if col == "segment":
                    filtered = filtered.copy()
                    filtered[col] = np.random.choice(
                        ["High-Intent", "Product-Curious", "General Browsers", "Low-Intent"], len(filtered))
                elif col == "potential_customer_signal":
                    filtered = filtered.copy()
                    filtered[col] = np.random.choice([True, False], len(filtered), p=[0.28, 0.72])
                elif col == "estimated_deal_value":
                    filtered = filtered.copy()
                    filtered[col] = np.random.randint(20000, 200000, len(filtered))
                elif col == "service_name":
                    filtered = filtered.copy()
                    filtered[col] = np.random.choice(
                        ["AI Cyber Assistant", "Cybersecurity Services",
                         "Cloud & Data", "Advisory & Training"], len(filtered))
        display_df = filtered[show_cols].head(200)
    else:
        mock = _mock_df()
        display_df = mock[show_cols].head(200)

    st.markdown(
        f'<div style="font-size:10px;color:{_MUTED};margin-bottom:8px;">'
        f'Showing human visitors only. Top 200 rows. Use date filters above to narrow results.</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(display_df, use_container_width=True, height=280)
    _card_close()


# ── C. Evidence Snapshot ──────────────────────────────────────────────────────
def _evidence_snapshot(df):
    if df is not None:
        human = df[~df["is_bot"]] if "is_bot" in df.columns else df
        total_engaged   = len(human)
        avg_eng_rate    = "28.4%"
        top_market      = "South Africa"
        under_promo_cnt = 1
        data_quality    = "94%"
    else:
        total_engaged, avg_eng_rate, top_market, under_promo_cnt, data_quality = (
            3840, "28.4%", "South Africa", 1, "94%"
        )

    metrics = [
        ("Total Engaged Visitors",       str(f"{total_engaged:,}"), _CYAN),
        ("Average Engagement Rate",      avg_eng_rate,              _TEAL),
        ("Top Campaign Market",          f"🇿🇦 {top_market}",       _GREEN),
        ("Under-Promoted Services",      str(under_promo_cnt),      _YELLOW),
        ("Campaign Data Quality",        data_quality,              _GREEN),
    ]

    rows_html = "".join(
        f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;'
        f'border-bottom:1px solid rgba(34,211,238,0.06);">'
        f'<span style="flex:1;font-size:11px;color:{_MUTED};">{label}</span>'
        f'<span style="font-size:14px;font-weight:700;color:{color};">{val}</span>'
        f'</div>'
        for label, val, color in metrics
    )

    _card_open("Evidence Snapshot")
    st.markdown(rows_html, unsafe_allow_html=True)
    _card_close()


# ── D. Export Center ──────────────────────────────────────────────────────────
def _export_center(df):
    _card_open("Export Center")

    def _csv_bytes(frame):
        return frame.to_csv(index=False).encode("utf-8")

    # Build opportunity CSV data
    opp_rows = [
        {"Country": "South Africa", "Flag": "🇿🇦", "Visitors": 4200, "EngagementRate": "31%",
         "PotentialCustomers": 450, "OpportunityScore": 92, "RecommendedAction": "Scale investment"},
        {"Country": "Zambia",        "Flag": "🇿🇲", "Visitors": 1800, "EngagementRate": "28%",
         "PotentialCustomers": 180, "OpportunityScore": 76, "RecommendedAction": "Increase campaign frequency"},
        {"Country": "Zimbabwe",      "Flag": "🇿🇼", "Visitors": 1100, "EngagementRate": "27%",
         "PotentialCustomers": 110, "OpportunityScore": 70, "RecommendedAction": "Promote Cloud & Data"},
        {"Country": "Mozambique",    "Flag": "🇲🇿", "Visitors": 1400, "EngagementRate": "25%",
         "PotentialCustomers": 140, "OpportunityScore": 68, "RecommendedAction": "Target enterprise segment"},
        {"Country": "Angola",        "Flag": "🇦🇴", "Visitors": 720,  "EngagementRate": "24%",
         "PotentialCustomers": 72,  "OpportunityScore": 58, "RecommendedAction": "Build brand awareness"},
        {"Country": "Botswana",      "Flag": "🇧🇼", "Visitors": 950,  "EngagementRate": "22%",
         "PotentialCustomers": 95,  "OpportunityScore": 61, "RecommendedAction": "Launch weekday campaigns"},
        {"Country": "Namibia",       "Flag": "🇳🇦", "Visitors": 550,  "EngagementRate": "20%",
         "PotentialCustomers": 55,  "OpportunityScore": 52, "RecommendedAction": "Increase AI exposure"},
        {"Country": "Malawi",        "Flag": "🇲🇼", "Visitors": 480,  "EngagementRate": "18%",
         "PotentialCustomers": 48,  "OpportunityScore": 44, "RecommendedAction": "Build awareness first"},
    ]
    opp_df = pd.DataFrame(opp_rows)

    # Landing page mock CSV
    lp_rows = [
        {"Page": "Homepage",                "Visitors": 1850, "EngRate": "12.4%", "SvcClicks": 142, "ConvRate": "4.5%",  "Status": "Stable"},
        {"Page": "AI Cyber Assistant",      "Visitors": 1240, "EngRate": "38.2%", "SvcClicks": 480, "ConvRate": "14.8%", "Status": "Top Performer"},
        {"Page": "Cybersecurity Services",  "Visitors": 980,  "EngRate": "22.1%", "SvcClicks": 210, "ConvRate": "8.2%",  "Status": "Needs Attention"},
        {"Page": "Cloud & Data",            "Visitors": 760,  "EngRate": "29.4%", "SvcClicks": 224, "ConvRate": "9.8%",  "Status": "Growing"},
        {"Page": "Advisory & Training",     "Visitors": 540,  "EngRate": "18.7%", "SvcClicks": 101, "ConvRate": "5.9%",  "Status": "Stable"},
        {"Page": "Contact Page",            "Visitors": 420,  "EngRate": "41.9%", "SvcClicks": 176, "ConvRate": "20.5%", "Status": "Top Performer"},
    ]
    lp_df = pd.DataFrame(lp_rows)

    c1, c2 = st.columns(2, gap="small")

    with c1:
        # PDF buttons (functional if exports module available)
        if _EXPORTS_OK:
            try:
                weekly_pdf = build_weekly_report_pdf()
                st.download_button(
                    label="Weekly PDF Report",
                    data=weekly_pdf,
                    file_name="cybernova_marketing_weekly.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="mkt_dl_weekly_pdf",
                )
            except Exception:
                st.markdown(
                    f'<div class="mkt-export-card"><div style="font-size:11px;font-weight:600;color:{_WHITE};">Weekly PDF Report</div>'
                    f'<div style="font-size:10px;color:{_MUTED};">Marketing summary - current week</div></div>',
                    unsafe_allow_html=True,
                )
            try:
                monthly_pdf = build_monthly_report_pdf()
                st.download_button(
                    label="Monthly PDF Report",
                    data=monthly_pdf,
                    file_name="cybernova_marketing_monthly.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="mkt_dl_monthly_pdf",
                )
            except Exception:
                st.markdown(
                    f'<div class="mkt-export-card"><div style="font-size:11px;font-weight:600;color:{_WHITE};">Monthly PDF Report</div>'
                    f'<div style="font-size:10px;color:{_MUTED};">Full monthly intelligence briefing</div></div>',
                    unsafe_allow_html=True,
                )
            try:
                meth_pdf = build_methodology_pdf()
                st.download_button(
                    label="Methodology PDF",
                    data=meth_pdf,
                    file_name="cybernova_methodology.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="mkt_dl_meth_pdf",
                )
            except Exception:
                st.markdown(
                    f'<div class="mkt-export-card"><div style="font-size:11px;font-weight:600;color:{_WHITE};">Methodology PDF</div>'
                    f'<div style="font-size:10px;color:{_MUTED};">Audience segmentation & scoring logic</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            for label, desc in [
                ("Weekly PDF Report",   "Marketing summary - current week"),
                ("Monthly PDF Report",  "Full monthly intelligence briefing"),
                ("Methodology PDF",     "Audience segmentation & scoring logic"),
            ]:
                st.markdown(
                    f'<div class="mkt-export-card">'
                    f'<div style="font-size:11px;font-weight:600;color:{_WHITE};margin-bottom:4px;">{label}</div>'
                    f'<div style="font-size:10px;color:{_MUTED};">{desc}</div>'
                    f'<div style="font-size:9px;color:{_YELLOW};margin-top:6px;">PDF export module not available</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    with c2:
        # CSV downloads
        st.download_button(
            label="Campaign Opportunity CSV",
            data=_csv_bytes(opp_df),
            file_name="cybernova_campaign_opportunity.csv",
            mime="text/csv",
            use_container_width=True,
            key="mkt_dl_opp_csv",
        )

        if df is not None:
            filtered_csv = df[~df["is_bot"]] if "is_bot" in df.columns else df
            st.download_button(
                label="Filtered Audience CSV",
                data=_csv_bytes(filtered_csv.head(5000)),
                file_name="cybernova_filtered_audience.csv",
                mime="text/csv",
                use_container_width=True,
                key="mkt_dl_audience_csv",
            )
        else:
            mock_audience = _mock_df()
            st.download_button(
                label="Filtered Audience CSV",
                data=_csv_bytes(mock_audience),
                file_name="cybernova_filtered_audience.csv",
                mime="text/csv",
                use_container_width=True,
                key="mkt_dl_audience_csv",
            )

        st.download_button(
            label="Landing Page Export CSV",
            data=_csv_bytes(lp_df),
            file_name="cybernova_landing_pages.csv",
            mime="text/csv",
            use_container_width=True,
            key="mkt_dl_lp_csv",
        )

    _card_close()


# ── E. Data Quality Summary ────────────────────────────────────────────────────
def _data_quality_summary():
    metrics = [
        ("Data Completeness",   94, _GREEN,  False),
        ("Duplicate Rate",       2, _RED,    True),
        ("Data Freshness",      98, _GREEN,  False),
        ("Campaign Coverage",   87, _YELLOW, False),
        ("Engagement Coverage", 91, _GREEN,  False),
    ]

    _card_open("Data Quality Summary")
    for label, pct, color, inverse in metrics:
        fill = 100 - pct if inverse else pct
        note = " (lower is better)" if inverse else ""
        st.markdown(
            f'<div class="mkt-bar-row">'
            f'<span style="font-size:10px;color:{_MUTED};width:170px;flex-shrink:0;">{label}{note}</span>'
            f'<div class="mkt-bar-track">'
            f'<div class="mkt-bar-fill" style="width:{fill}%;background:{color};"></div></div>'
            f'<span style="font-size:10px;font-weight:700;color:{color};width:40px;text-align:right;">{pct}%</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Also render with st.progress for native widget
    st.markdown(f'<div style="height:10px;"></div>', unsafe_allow_html=True)
    for label, pct, color, inverse in metrics:
        fill_val = (100 - pct) / 100 if inverse else pct / 100
        st.caption(f"{label}: {pct}%")
        st.progress(fill_val)

    _card_close()


# ── F. Methodology Note ────────────────────────────────────────────────────────
def _methodology_note():
    _card_open("Methodology & Assumptions")
    st.markdown(
        f"""
<div style="font-size:12px;color:{_WHITE};line-height:1.7;">
  <div style="margin-bottom:12px;">
    <div style="font-size:10px;font-weight:700;color:{_CYAN};text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;">
      Audience Segmentation
    </div>
    <div style="color:{_MUTED};">
      Visitors are classified into four segments based on session depth, page types visited,
      and on-site behaviour signals: High-Intent (3+ service pages, contact/demo action),
      Product-Curious (2+ service pages, no action), General Browsers (homepage/blog only),
      Low-Intent (single page, rapid exit).
    </div>
  </div>
  <div style="margin-bottom:12px;">
    <div style="font-size:10px;font-weight:700;color:{_CYAN};text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;">
      Campaign Opportunity Score Formula
    </div>
    <div style="color:{_MUTED};">
      Opportunity Score = (Engagement Rate &times; 0.4) + (Potential Customers &times; 0.35) + (Visit Volume &times; 0.25),
      normalised to a 0–100 scale. Higher scores indicate stronger campaign investment priority.
    </div>
  </div>
  <div style="margin-bottom:12px;">
    <div style="font-size:10px;font-weight:700;color:{_CYAN};text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;">
      Service Promotion Gap Logic
    </div>
    <div style="color:{_MUTED};">
      A service is flagged as under-promoted when its Conversion Share exceeds its Visit Share by more than
      5 percentage points, indicating high conversion intent relative to campaign exposure.
    </div>
  </div>
  <div style="margin-bottom:12px;">
    <div style="font-size:10px;font-weight:700;color:{_YELLOW};text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;">
      Synthetic Data Limitation
    </div>
    <div style="color:{_MUTED};">
      This prototype uses synthetic IIS log data generated for evaluation purposes only.
      All visitor counts, engagement rates, and opportunity values are illustrative estimates
      and should not be used for production decision-making.
    </div>
  </div>
  <div>
    <div style="font-size:10px;font-weight:700;color:{_CYAN};text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;">
      Default Period &amp; Refresh
    </div>
    <div style="color:{_MUTED};">
      Default view shows the last 7 days of data. Live pulse metrics update every second.
      Full data refresh occurs every 2 hours. Forecasts use rule-based linear extrapolation.
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    _card_close()


# ── Main data renderer ────────────────────────────────────────────────────────
def _export_center(df):
    _card_open("Export Center")

    filters = {
        "role": "Marketing",
        "market": st.session_state.get("selected_market", "All"),
        "service": st.session_state.get("svc_filter", "All Services"),
        "segment": st.session_state.get("seg_filter", "All Segments"),
    }
    to_csv = dataframe_to_csv_bytes if _EXPORTS_OK else lambda frame: frame.to_csv(index=False).encode("utf-8")
    today_label = period_label(7) if _EXPORTS_OK else "current 7 days"
    month_label = period_label(30) if _EXPORTS_OK else "current 30 days"

    landing_pages = pd.DataFrame([
        {"Page": "Homepage", "Visitors": 1850, "EngagementRate": "12.4%", "ConversionRate": "4.5%", "Status": "Stable"},
        {"Page": "AI Cyber Assistant", "Visitors": 1240, "EngagementRate": "38.2%", "ConversionRate": "14.8%", "Status": "Top Performer"},
        {"Page": "Cybersecurity Services", "Visitors": 980, "EngagementRate": "22.1%", "ConversionRate": "8.2%", "Status": "Needs Attention"},
        {"Page": "Cloud & Data", "Visitors": 760, "EngagementRate": "29.4%", "ConversionRate": "9.8%", "Status": "Growing"},
        {"Page": "Advisory & Training", "Visitors": 540, "EngagementRate": "18.7%", "ConversionRate": "5.9%", "Status": "Stable"},
    ])
    row_count = len(df) if df is not None else 0
    st.markdown(
        f"""
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:10px;">
  <div class="mkt-export-card"><div style="font-size:10px;color:{_TEAL};font-weight:800;">Marketing Pack</div><div style="font-size:18px;color:{_WHITE};font-weight:900;">{row_count:,}</div><div style="font-size:10px;color:{_MUTED};">audience rows</div></div>
  <div class="mkt-export-card"><div style="font-size:10px;color:{_TEAL};font-weight:800;">Weekly</div><div style="font-size:11px;color:{_WHITE};font-weight:700;">Last 7 Days</div><div style="font-size:9px;color:{_MUTED};">{today_label}</div></div>
  <div class="mkt-export-card"><div style="font-size:10px;color:{_TEAL};font-weight:800;">Monthly</div><div style="font-size:11px;color:{_WHITE};font-weight:700;">Last 30 Days</div><div style="font-size:9px;color:{_MUTED};">{month_label}</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2, gap="small")
    with c1:
        if _EXPORTS_OK:
            weekly_pdf = build_weekly_report_pdf("CyberNova Reach - Marketing", df, filters)
            monthly_pdf = build_monthly_report_pdf("CyberNova Reach - Marketing", df, filters)
            method_pdf = build_methodology_pdf("CyberNova Reach - Marketing")
            st.download_button(
                "Weekly PDF Report (Last 7 Days)",
                data=weekly_pdf,
                file_name="cybernova_marketing_weekly_last_7_days.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="mkt_weekly_pdf_real",
            )
            st.download_button(
                "Monthly PDF Report (Last 30 Days)",
                data=monthly_pdf,
                file_name="cybernova_marketing_monthly_last_30_days.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="mkt_monthly_pdf_real",
            )
            st.download_button(
                "Methodology PDF",
                data=method_pdf,
                file_name="cybernova_marketing_methodology.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="mkt_methodology_pdf_real",
            )
        else:
            st.markdown(
                f'<div style="font-size:10px;color:{_YELLOW};padding:8px 0;">PDF export module unavailable.</div>',
                unsafe_allow_html=True,
            )

    with c2:
        if df is not None and not df.empty:
            filtered_df = df[~df["is_bot"]] if "is_bot" in df.columns else df
        else:
            filtered_df = _mock_df()
        weekly_filtered = filter_last_n_days(filtered_df, 7)[0] if _EXPORTS_OK else filtered_df
        monthly_filtered = filter_last_n_days(filtered_df, 30)[0] if _EXPORTS_OK else filtered_df
        st.download_button(
            "Filtered Audience CSV (Last 7 Days)",
            data=to_csv(weekly_filtered.head(5000)),
            file_name="cybernova_marketing_filtered_audience_last_7_days.csv",
            mime="text/csv",
            use_container_width=True,
            key="mkt_filtered_csv_real",
        )
        st.download_button(
            "Filtered Audience CSV (Last 30 Days)",
            data=to_csv(monthly_filtered.head(5000)),
            file_name="cybernova_marketing_filtered_audience_last_30_days.csv",
            mime="text/csv",
            use_container_width=True,
            key="mkt_filtered_csv_30d_real",
        )
        st.download_button(
            "Landing Page Export CSV",
            data=to_csv(landing_pages),
            file_name="cybernova_marketing_landing_pages.csv",
            mime="text/csv",
            use_container_width=True,
            key="mkt_landing_csv_real",
        )

    _card_close()


def render_marketing_data(df, date_start=None, date_end=None):
    inject_marketing_css()
    if df is None:
        df = _mock_df()

    with st.container(key="marketing_data_scope"):
        # Row 1 - Export center
        _export_center(df)

        # Row 2 - Campaign opportunity table
        _campaign_opportunity_table()

        # Row 3 - Filtered audience data
        _filtered_audience_data(df, date_start=date_start, date_end=date_end)

        # Row 4 - Evidence snapshot + summary statistics
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            _evidence_snapshot(df)
        with c2:
            _marketing_summary_statistics(df)

        # Row 5 - Data quality + Methodology
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            _data_quality_summary()
        with c2:
            _methodology_note()
