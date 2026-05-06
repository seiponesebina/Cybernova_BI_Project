import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime, pathlib, random, base64

# Sales views — imported after page_config so Streamlit doesn't complain
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
                   initial_sidebar_state="collapsed", page_icon="⬡")

_BASE = pathlib.Path(__file__).parent
ENRICH_PATH = str(_BASE / "data" / "output" / "cybernova_enriched_logs.csv")
FAST_CACHE_PATH = _BASE / "data" / "output" / "cybernova_enriched_logs.fast.pkl"

# ── LOGO ──────────────────────────────────────────────────────────────────────
def _load_logo():
    for name, mime in [("cybernova_logo_transparent.svg","image/svg+xml"),("logo.png","image/png")]:
        p = _BASE / name
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            return f"data:{mime};base64,{b64}", mime
    return "", ""

LOGO_SRC, LOGO_MIME = _load_logo()
def logo_img(h=36, extra=""):
    return f'<img src="{LOGO_SRC}" style="height:{h}px;width:auto;display:inline-block;{extra}" />' if LOGO_SRC else '<span style="font-size:22px;color:#22D3EE;font-weight:900;">CN</span>'

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
    "Sales":     {"title":"CyberNova Pulse",   "sub":"Sales Command Center • Potential Customer Intelligence",       "accent":"#22D3EE","icon":"⚡"},
    "Marketing": {"title":"CyberNova Reach",   "sub":"Marketing Intelligence Hub • Campaign Opportunity Intelligence","accent":"#14B8A6","icon":"📡"},
    "Executive": {"title":"CyberNova Horizon", "sub":"Executive Insights Dashboard • SADC Expansion Intelligence",   "accent":"#A855F7","icon":"🌐"},
}
COLOR_MAP = {"Core Market":"#22D3EE","Strategic Hub":"#14B8A6","High Growth":"#FFD84A","Emerging":"#7CFF4F","Stable":"#8A98A6"}

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
div.block-container{padding:0 0 0 0!important;max-width:100%!important;}
/* Remove default streamlit gaps */
div[data-testid="stVerticalBlock"]>div{padding-top:0!important;padding-bottom:0!important;}
div[data-testid="stHorizontalBlock"]{gap:12px!important;align-items:flex-start!important;}
/* Card */
.cn-card{
  background:linear-gradient(145deg,rgba(12,24,44,0.92),rgba(8,18,34,0.88));
  border:1px solid var(--border);border-radius:14px;
  padding:16px 18px;margin-bottom:12px;
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
  padding:14px 16px;
  box-shadow:0 2px 16px rgba(0,0,0,0.45);backdrop-filter:blur(12px);
  transition:border-color .2s,transform .15s;cursor:default;
}
.kpi-card:hover{border-color:var(--border-a);transform:translateY(-1px);}
.kpi-label{font-size:10px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:8px;}
.kpi-value{font-size:1.9rem;font-weight:800;color:#FFFFFF;line-height:1;margin-bottom:6px;}
.kpi-value-sm{font-size:1.35rem;font-weight:700;color:#FFFFFF;line-height:1;margin-bottom:6px;}
.kpi-delta{display:inline-flex;align-items:center;gap:3px;font-size:11px;font-weight:600;
  padding:2px 7px;border-radius:20px;margin-bottom:4px;}
.delta-up{background:rgba(74,222,128,0.12);color:var(--green);border:1px solid rgba(74,222,128,0.2);}
.delta-watch{background:rgba(251,191,36,0.12);color:var(--yellow);border:1px solid rgba(251,191,36,0.2);}
.delta-down{background:rgba(248,113,113,0.12);color:var(--red);border:1px solid rgba(248,113,113,0.2);}
.kpi-sub{font-size:10px;color:var(--muted);}
/* Section label */
.sec-label{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:var(--cyan);margin-bottom:10px;padding-bottom:6px;
  border-bottom:1px solid rgba(34,211,238,0.12);display:flex;align-items:center;gap:6px;}
/* Pulse strip */
.pulse-wrap{
  background:linear-gradient(90deg,rgba(34,211,238,0.06),rgba(20,184,166,0.04),rgba(34,211,238,0.03));
  border:1px solid rgba(34,211,238,0.18);border-radius:10px;
  padding:9px 16px;display:flex;gap:0;align-items:center;margin-bottom:12px;
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
/* Status bar */
.status-bar{
  background:linear-gradient(90deg,rgba(9,20,36,0.95),rgba(7,16,28,0.9));
  border-top:1px solid rgba(34,211,238,0.1);border-radius:10px;
  padding:9px 18px;display:flex;gap:28px;align-items:center;
  flex-wrap:wrap;margin-top:10px;
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
  margin-bottom:14px!important;
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
</style>""", unsafe_allow_html=True)
    if extra_css:
        st.markdown(f"<style>{extra_css}</style>", unsafe_allow_html=True)

# ── DATA ──────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    try:
        csv_path = pathlib.Path(ENRICH_PATH)
        cache_needs_write = False
        if FAST_CACHE_PATH.exists() and FAST_CACHE_PATH.stat().st_mtime >= csv_path.stat().st_mtime:
            df = pd.read_pickle(FAST_CACHE_PATH)
        else:
            df = pd.read_csv(ENRICH_PATH, low_memory=False)
            cache_needs_write = True
        if "timestamp" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        if "date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        for c in ["is_bot","is_sadc","is_warm_lead","potential_customer_signal","has_demo_request"]:
            if c in df.columns: df[c] = df[c].astype(bool, errors="ignore")
        if cache_needs_write:
            try:
                df.to_pickle(FAST_CACHE_PATH)
            except Exception:
                pass
        return df
    except Exception: return None

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
        return f"${value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value/1_000:.0f}K"
    return f"${value:,.0f}"

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
         "s_cust":1248,"s_demos":312,"s_rev":82.6,
         "m_aud":3840,"m_visits":1240,"m_qual":78,
         "e_demand":9200,"e_ai":29,"e_alerts":3,"alert_count":2,
         "sales_drawer_open":True,
         "admin_drawer_open":False,
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
    """Restore auth session from URL query params — fixes browser back-button logout."""
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
        return "starting", "watch"
    diff = cur - base
    cls = "up" if diff >= 0 else "down"
    if mode == "rate":
        return f"{diff:+.1f} pts", cls
    pct = diff / base * 100
    return f"{pct:+.1f}%", cls

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

    # ── LOGIN CSS ──
    st.markdown("""
<style>
div.block-container{padding:0!important;max-width:100%!important;}
[data-testid="stApp"]{
  background:
    radial-gradient(ellipse at 22% 48%,rgba(0,245,212,0.08) 0%,transparent 50%),
    radial-gradient(ellipse at 78% 22%,rgba(118,255,54,0.06) 0%,transparent 46%),
    radial-gradient(ellipse at 55% 80%,rgba(0,200,230,0.04) 0%,transparent 40%),
    #020509 !important;
}
/* vertically centre the page content */
section[data-testid="stMain"]{display:flex;align-items:center;min-height:100vh;}
section[data-testid="stMain"] > div{width:100%;}

/* ── card top (HTML block) ── */
.lc-top{
  position:relative;overflow:hidden;
  background:
    radial-gradient(circle at 80% 20%,rgba(0,245,212,0.09),transparent 38%),
    radial-gradient(circle at 15% 80%,rgba(118,255,54,0.08),transparent 32%),
    rgba(7,14,22,0.90);
  border:1px solid rgba(255,255,255,0.10);
  border-bottom:none;
  border-radius:22px 22px 0 0;
  padding:32px 40px 24px;
  backdrop-filter:blur(24px);
  box-shadow:inset 0 1px 0 rgba(255,255,255,0.06);
}
.lc-top::before{
  content:'';position:absolute;top:-90px;right:-60px;
  width:320px;height:320px;border-radius:50%;
  border:1px solid rgba(0,245,212,0.05);
  animation:lcArc 10s ease-in-out infinite;pointer-events:none;
}
@keyframes lcArc{0%,100%{opacity:.3;transform:scale(1);}50%{opacity:.7;transform:scale(1.06);}}

/* ── card form body (Streamlit form sits here) ── */
div[data-testid="stForm"]{
  background:rgba(7,14,22,0.90)!important;
  border:none!important;
  border-left:1px solid rgba(255,255,255,0.10)!important;
  border-right:1px solid rgba(255,255,255,0.10)!important;
  padding:0 40px!important;
  border-radius:0!important;
  backdrop-filter:blur(24px);
}
/* ── card bottom (HTML block) ── */
.lc-bot{
  background:rgba(7,14,22,0.90);
  border:1px solid rgba(255,255,255,0.10);
  border-top:none;
  border-radius:0 0 22px 22px;
  padding:16px 40px 28px;
  backdrop-filter:blur(24px);
  box-shadow:0 24px 80px rgba(0,0,0,0.65);
}
/* error bar sits between top and form — give it card sides */
.lc-err-wrap{
  background:rgba(7,14,22,0.90);
  border-left:1px solid rgba(255,255,255,0.10);
  border-right:1px solid rgba(255,255,255,0.10);
  padding:0 40px 4px;
}
.lc-err{
  background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.28);
  border-radius:8px;padding:9px 13px;color:#F87171;font-size:12px;
  display:flex;align-items:center;gap:8px;
}

/* logo row */
.lc-logo-row{display:flex;align-items:center;gap:11px;margin-bottom:20px;}
.lc-wm-main{font-size:14px;font-weight:800;color:#F5F7FA;letter-spacing:.07em;line-height:1;}
.lc-wm-sub{font-size:9px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:#00F5D4;margin-top:3px;line-height:1;}
/* status pill */
.lc-status{display:inline-flex;align-items:center;gap:7px;height:30px;padding:0 12px;
  border-radius:8px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.09);
  margin-bottom:18px;float:right;margin-top:-4px;}
.lc-sdot{width:6px;height:6px;border-radius:50%;background:#76FF36;animation:lcDot 2s ease-in-out infinite;}
@keyframes lcDot{0%,100%{box-shadow:0 0 0 0 rgba(118,255,54,.4);}50%{box-shadow:0 0 0 5px rgba(118,255,54,0);}}
.lc-stext{font-size:11px;color:rgba(245,247,250,0.55);}
/* heading */
.lc-heading{font-size:26px;font-weight:800;color:#F5F7FA;line-height:1.15;letter-spacing:-.01em;
  margin-bottom:6px;clear:both;}
.lc-sub{font-size:12px;color:rgba(245,247,250,0.55);margin-bottom:18px;line-height:1.5;}
/* feature chips row */
.lc-chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px;}
.lc-chip{display:inline-flex;align-items:center;gap:5px;padding:5px 11px;border-radius:7px;
  font-size:11px;font-weight:600;}
.lc-chip.g{background:rgba(118,255,54,0.07);border:1px solid rgba(118,255,54,0.22);color:#76FF36;}
.lc-chip.c{background:rgba(0,245,212,0.07);border:1px solid rgba(0,245,212,0.22);color:#00F5D4;}
/* divider */
.lc-div{height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.12),transparent);
  margin-bottom:0;}
/* security note */
.lc-note{display:flex;gap:10px;align-items:flex-start;padding:12px 14px;
  border-radius:9px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);}
.lc-note-txt{font-size:11px;line-height:1.45;color:rgba(245,247,250,0.50);}

/* ── widget overrides ── */
div[data-testid="stSelectbox"] > label,
div[data-testid="stTextInput"] > label{
  color:rgba(245,247,250,0.55)!important;font-size:11px!important;
  font-weight:600!important;letter-spacing:.08em!important;
  text-transform:uppercase!important;margin-bottom:5px!important;
}
div[data-testid="stSelectbox"] > div > div{
  background:rgba(4,8,15,0.95)!important;
  border:1px solid rgba(255,255,255,0.11)!important;
  border-radius:9px!important;min-height:44px!important;
  color:#F5F7FA!important;font-size:13px!important;
}
div[data-testid="stSelectbox"] > div > div:focus-within{
  border-color:rgba(118,255,54,0.45)!important;
  box-shadow:0 0 0 2px rgba(118,255,54,0.09)!important;
}
div[data-testid="stTextInput"] > div{
  background:rgba(4,8,15,0.95)!important;
  border:1px solid rgba(255,255,255,0.11)!important;
  border-radius:9px!important;min-height:44px!important;
}
div[data-testid="stTextInput"] > div > input{
  background:transparent!important;color:#F5F7FA!important;
  font-size:13px!important;min-height:42px!important;padding:0 13px!important;
}
div[data-testid="stTextInput"] > div:focus-within{
  border-color:rgba(118,255,54,0.45)!important;
  box-shadow:0 0 0 2px rgba(118,255,54,0.09)!important;
}
div[data-testid="stFormSubmitButton"] > button{
  width:100%!important;height:48px!important;margin-top:4px!important;
  border-radius:9px!important;border:none!important;
  font-size:14px!important;font-weight:800!important;color:#021008!important;
  background:linear-gradient(90deg,#76FF36,#00F5D4)!important;
  transition:all .18s!important;animation:lcBtn 3.5s ease-in-out infinite!important;
}
div[data-testid="stFormSubmitButton"] > button:hover{
  filter:brightness(1.08)!important;transform:translateY(-1px)!important;
}
div[data-testid="stFormSubmitButton"] > button:active{transform:translateY(0)!important;}
@keyframes lcBtn{
  0%,100%{box-shadow:0 0 20px rgba(0,245,212,.14),0 0 20px rgba(118,255,54,.10);}
  50%{box-shadow:0 0 36px rgba(0,245,212,.24),0 0 36px rgba(118,255,54,.18);}
}
div[data-testid="stVerticalBlock"]>div{padding-top:3px!important;padding-bottom:3px!important;}
</style>""", unsafe_allow_html=True)

    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    # single centered column
    _, card_col, _ = st.columns([1, 1.4, 1])

    with card_col:
        _logo = logo_img(h=34) if LOGO_SRC else _ico_mark

        # ── CARD TOP ──────────────────────────────────────────────────────────────
        st.markdown(f"""
<div class="lc-top">
  <div class="lc-status">
    {_ico_shield_sm}
    <div class="lc-sdot"></div>
    <span class="lc-stext">All systems operational</span>
  </div>
  <div class="lc-logo-row">
    {_logo}
    <div>
      <div class="lc-wm-main">CYBERNOVA</div>
      <div class="lc-wm-sub">BI PORTAL</div>
    </div>
  </div>
  <div class="lc-heading">Sign in to your<br/>intelligence workspace</div>
  <div class="lc-sub">Your role unlocks the right dashboard, charts, and decisions.</div>
  <div class="lc-chips">
    <span class="lc-chip g">{_ico_pulse} Live Pulse</span>
    <span class="lc-chip c">{_ico_chart} Strategic Analytics</span>
    <span class="lc-chip g">{_ico_role} Role-Based Access</span>
  </div>
  <div class="lc-div"></div>
</div>""", unsafe_allow_html=True)

        # ── ERROR (card sides maintained) ─────────────────────────────────────────
        if st.session_state.get("login_error"):
            st.markdown(f"""
<div class="lc-err-wrap">
  <div class="lc-err">{_ico_lock_sm}<span>Invalid password for selected role.</span></div>
</div>""", unsafe_allow_html=True)

        # ── FORM (stForm CSS gives it matching card sides) ─────────────────────────
        with st.form("login_form", clear_on_submit=False):
            role = st.selectbox("Select your role", list(ROLE_PASSWORDS.keys()))
            pwd  = st.text_input("Password", type="password", placeholder="Enter your password")
            sub  = st.form_submit_button("Sign In to Dashboard  →", use_container_width=True)
            if sub:
                if ROLE_PASSWORDS.get(role, "") == pwd:
                    st.session_state.authenticated    = True
                    st.session_state.current_role     = role
                    st.session_state.active_dashboard = allowed(role)[0]
                    st.session_state.active_tab       = "Overview"
                    st.session_state.login_error      = False
                    st.query_params["role"] = role
                    st.rerun()
                else:
                    st.session_state.login_error = True
                    st.rerun()

        # ── CARD BOTTOM ───────────────────────────────────────────────────────────
        st.markdown(f"""
<div class="lc-bot">
  <div class="lc-note">
    {_ico_lock}
    <div class="lc-note-txt">
      Prototype access layer only. Production would require secure authentication,
      password hashing, audit logging, and full role-based access control.
    </div>
  </div>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
def render_header():
    v    = st.session_state
    dash = v.active_dashboard
    cfg  = DASH_CFG[dash]
    role = v.current_role or ""
    uname, _ = ROLE_META.get(role, ("Alex",""))
    fname = uname.split()[0]
    now   = datetime.datetime.now().strftime("%H:%M")

    hdr_col1, hdr_col2 = st.columns([8, 2])
    with hdr_col1:
        st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;
  background:linear-gradient(135deg,rgba(9,20,36,0.97),rgba(7,16,28,0.94));
  border:1px solid rgba(34,211,238,0.12);border-radius:14px;
  padding:14px 22px;margin-bottom:14px;
  box-shadow:0 2px 24px rgba(0,0,0,0.6),inset 0 1px 0 rgba(255,255,255,0.03);">

  <div style="display:flex;align-items:center;gap:14px;">
    {logo_img(h=34)}
    <div>
      <div style="font-size:10px;color:#6B7FA3;margin-bottom:2px;">
        Welcome back, {fname} &nbsp;·&nbsp;
        <span style="color:#22D3EE;">{now}</span>
        &nbsp;<span style="color:#4ADE80;">●</span>
      </div>
      <div style="font-size:22px;font-weight:800;color:{cfg['accent']};letter-spacing:.01em;line-height:1.1;">
        {cfg['title']}
      </div>
      <div style="font-size:11px;color:#6B7FA3;margin-top:2px;">{cfg['sub']}</div>
    </div>
  </div>

  <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
    <div style="background:rgba(9,20,36,0.8);border:1px solid rgba(34,211,238,0.15);
      border-radius:8px;padding:5px 12px;font-size:11px;color:#6B7FA3;">
      {dash} View &nbsp;▾
    </div>
    <div style="background:rgba(9,20,36,0.8);border:1px solid rgba(34,211,238,0.15);
      border-radius:8px;padding:5px 12px;font-size:11px;color:#6B7FA3;">
      Live Data Active
    </div>
    <span style="background:rgba(74,222,128,0.1);color:#4ADE80;
      border:1px solid rgba(74,222,128,0.25);border-radius:20px;
      padding:4px 12px;font-size:11px;font-weight:600;">
      ● All systems operational
    </span>
  </div>
</div>""", unsafe_allow_html=True)
    with hdr_col2:
        btn_left, btn_right = st.columns(2, gap="small", vertical_alignment="center")
        with btn_left:
            _drawer_label = "✕ Close" if st.session_state.get("admin_drawer_open") else "⚙ Filters"
            if st.button(_drawer_label, key="admin_drawer_toggle", use_container_width=True):
                st.session_state.admin_drawer_open = not st.session_state.get("admin_drawer_open", False)
                st.rerun()
        with btn_right:
            if st.button("⏻ Logout", key="header_logout", use_container_width=True):
                logout()
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN DRAWER — dashboard switcher + filters
# ═══════════════════════════════════════════════════════════════════════════════
def render_admin_drawer():
    v    = st.session_state
    role = v.current_role or ""
    uname, utitle = ROLE_META.get(role,("User","—"))

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
    <div style="font-size:9px;color:#4ADE80;margin-top:1px;">● Online</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Dashboard Switcher ──
    st.markdown('<div class="rp-label">Dashboard</div>', unsafe_allow_html=True)
    for d in allowed(role):
        cfg    = DASH_CFG[d]
        active = v.active_dashboard == d
        if st.button(f"{cfg['icon']}  {cfg['title']}", key=f"rp_dash_{d}", use_container_width=True):
            v.active_dashboard = d
            v.active_tab = "Overview"
            st.rerun()
        if active:
            st.markdown(f'<div style="height:2px;background:{cfg["accent"]};border-radius:2px;margin:-10px 0 6px;opacity:.5;"></div>', unsafe_allow_html=True)

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
  <div style="font-size:11px;color:#6B7FA3;margin-bottom:4px;">🔄 Live data active</div>
  <div style="font-size:11px;color:#6B7FA3;margin-bottom:4px;">🛡️ 96.4% data quality</div>
  <div style="font-size:11px;color:#F87171;">⚠ {v.alert_count} alert(s) active</div>
</div>""", unsafe_allow_html=True)

    if st.button("⇦ Logout", use_container_width=True, key="rp_logout"):
        logout(); st.rerun()

    st.markdown("""
<div style="margin-top:12px;font-size:9px;color:#1E2D3D;text-align:center;padding:0 4px;line-height:1.5;">
  Prototype v1.0 · Review only · Not for production use
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
<div style="margin-bottom:12px;">
  <span class="chip">Period: {period}</span>
  <span class="chip">Market: {v.selected_market}</span>
  <span class="chip">Service: {v.svc_filter}</span>
  <span class="chip">Segment: {v.seg_filter}</span>
  <span class="chip">Outcome: {v.outcome_filter}</span>
  <span class="chip">Filtered Noise: {noise:,}</span>
  <span class="chip">Quality: {quality}%</span>
  <span class="chip">Revenue: modelled opportunity, not booked sales</span>
</div>""", unsafe_allow_html=True)

@st.fragment(run_every=1)
def render_live_pulse():
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
    st.markdown(f"""
<div class="pulse-wrap">
  <div style="display:flex;align-items:center;font-size:9px;font-weight:700;letter-spacing:.14em;
    text-transform:uppercase;color:#3A4A5E;padding-right:16px;border-right:1px solid rgba(34,211,238,0.1);">
    <span class="live-dot"></span>LIVE
  </div>
  {html}
  <div style="margin-left:auto;font-size:9px;color:#66727D;white-space:nowrap;">Updated {now}<br>today stream</div>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SHARED SADC MAP
# ═══════════════════════════════════════════════════════════════════════════════
MAP_NODES = [
    {"city":"Cape Town","country":"South Africa","lat":-33.9,"lon":18.4,"status":"Core Market","customers":450,"demos":98,"conv":"21.8%","revenue":"$18.2M","ai":34,"risk":"Low","action":"Scale outreach","visitors":4200,"eng":"31%","invest":"Invest"},
    {"city":"Durban","country":"South Africa","lat":-29.9,"lon":30.9,"status":"High Growth","customers":112,"demos":28,"conv":"25%","revenue":"$6.1M","ai":28,"risk":"Low","action":"Expand campaign","visitors":1100,"eng":"27%","invest":"Invest"},
    {"city":"Lusaka","country":"Zambia","lat":-15.4,"lon":28.3,"status":"Strategic Hub","customers":180,"demos":41,"conv":"22.8%","revenue":"$9.5M","ai":41,"risk":"Low","action":"Deepen AI push","visitors":1800,"eng":"28%","invest":"Invest"},
    {"city":"Maputo","country":"Mozambique","lat":-25.9,"lon":32.6,"status":"Strategic Hub","customers":140,"demos":29,"conv":"20.7%","revenue":"$7.2M","ai":37,"risk":"Medium","action":"Strengthen brand","visitors":1400,"eng":"25%","invest":"Monitor"},
    {"city":"Gaborone","country":"Botswana","lat":-24.7,"lon":25.9,"status":"Stable","customers":95,"demos":18,"conv":"18.9%","revenue":"$4.8M","ai":22,"risk":"Low","action":"Maintain","visitors":950,"eng":"22%","invest":"Monitor"},
    {"city":"Harare","country":"Zimbabwe","lat":-17.8,"lon":31.0,"status":"High Growth","customers":120,"demos":31,"conv":"25.8%","revenue":"$6.8M","ai":31,"risk":"Medium","action":"Monitor closely","visitors":1100,"eng":"27%","invest":"Monitor"},
    {"city":"Luanda","country":"Angola","lat":-8.8,"lon":13.2,"status":"Emerging","customers":72,"demos":14,"conv":"19.4%","revenue":"$3.1M","ai":18,"risk":"Medium","action":"Pilot campaign","visitors":720,"eng":"24%","invest":"Review"},
    {"city":"Windhoek","country":"Namibia","lat":-22.6,"lon":17.1,"status":"Emerging","customers":55,"demos":11,"conv":"20%","revenue":"$2.3M","ai":15,"risk":"Low","action":"Explore","visitors":550,"eng":"20%","invest":"Review"},
    {"city":"Lilongwe","country":"Malawi","lat":-13.9,"lon":33.8,"status":"Emerging","customers":48,"demos":8,"conv":"16.7%","revenue":"$1.6M","ai":12,"risk":"Low","action":"Seed market","visitors":480,"eng":"18%","invest":"Review"},
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
        fig.add_trace(go.Scattermap(
            lat=grp.lat,lon=grp.lon,mode="markers",name=status,
            marker=dict(size=grp["sz"],color=COLOR_MAP[status],opacity=0.88,sizemode="area"),
            text=[hover[df_m.index.get_loc(i)] for i in grp.index],hoverinfo="text"))
    fig.update_layout(
        map=dict(style="carto-darkmatter",center=dict(lat=-20,lon=26),zoom=2.9),
        height=height,margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(9,20,36,0.85)",bordercolor="rgba(34,211,238,0.18)",
                    borderwidth=1,font=dict(color="#F0F4F8",size=10),orientation="v",x=0.01,y=0.98))
    st.markdown(f'<div class="cn-card"><div class="sec-label">{title}</div><div style="font-size:10px;color:#6B7FA3;margin-bottom:8px;">{sub} | map remains stable while regional counters update</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# ── CHART LAYOUT HELPER ───────────────────────────────────────────────────────
def _cl(fig, h=250):
    fig.update_layout(height=h,margin=dict(l=0,r=0,t=8,b=0),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(7,16,28,0.6)",
        font=dict(color="#6B7FA3",size=10),
        xaxis=dict(gridcolor="rgba(34,211,238,0.05)",color="#6B7FA3",showgrid=True),
        yaxis=dict(gridcolor="rgba(34,211,238,0.05)",color="#6B7FA3",showgrid=True),
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#6B7FA3",size=9),
                    orientation="h",y=-0.22,x=0))

def ph(title, icon="⬡", note="Coming in next build"):
    st.markdown(f'<div class="ph-card"><div style="font-size:22px;opacity:.4;">{icon}</div><div style="font-size:12px;font-weight:600;">{title}</div><div style="font-size:10px;color:#2A3A4E;">{note}</div></div>', unsafe_allow_html=True)

def ph_grid(cards, n=3):
    for i in range(0,len(cards),n):
        row=cards[i:i+n]
        cols=st.columns(len(row))
        for col,(t,ic) in zip(cols,row):
            with col: ph(t,ic)

# ═══════════════════════════════════════════════════════════════════════════════
# SALES OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
def _sales_growth(df):
    # Group df by month to derive monthly trend
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
            if "has_demo_request" in df2.columns:
                _human["_demo_signal"] = _truthy_series(_human, "has_demo_request").astype(int)
                _dr = _human.groupby("_month")["_demo_signal"].sum().reindex(_pc.index, fill_value=0).tail(6)
            else:
                _dr = (_pc * 0.25).astype(int)
            mo = [str(p) for p in _pc.index]
            pc_vals = [int(v) for v in _pc.tolist()]
            dr_vals = [int(v) for v in _dr.tolist()]
            target  = [max(v, 900) + 100 * i for i, v in enumerate(pc_vals)]
            prev    = [int(v * 0.88) for v in pc_vals[1:]] + [None] if len(pc_vals) > 1 else pc_vals
        except Exception:
            mo = ["Jan","Feb","Mar","Apr","May","Jun"]
            pc_vals = [820,940,1050,1180,1248,None]
            dr_vals = [210,245,275,295,312,None]
            target  = [900,950,1000,1100,1200,1300]
            prev    = [760,820,940,1050,1180,1248]
    else:
        mo = ["Jan","Feb","Mar","Apr","May","Jun"]
        pc_vals = [820,940,1050,1180,1248,None]
        dr_vals = [210,245,275,295,312,None]
        target  = [900,950,1000,1100,1200,1300]
        prev    = [760,820,940,1050,1180,1248]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=mo, y=pc_vals, name="Potential Customers", line=dict(color="#22D3EE",width=2), mode="lines+markers", marker=dict(size=4), hovertemplate="<b>%{x}</b><br>Customers: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=mo, y=dr_vals, name="Demo Requests",       line=dict(color="#4ADE80",width=2), mode="lines+markers", marker=dict(size=4), hovertemplate="<b>%{x}</b><br>Demos: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=mo, y=target,  name="Target",              line=dict(color="#A855F7",width=1.5,dash="dash"), mode="lines", hovertemplate="<b>%{x}</b><br>Target: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=mo, y=prev,    name="Prev. Month",         line=dict(color="#3A4A5E",width=1.5,dash="dot"),  mode="lines", hovertemplate="<b>%{x}</b><br>Prev: %{y}<extra></extra>"))
    _cl(fig, 230)
    st.markdown('<div class="cn-card"><div class="sec-label">Sales Growth Trend</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
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

    fig = go.Figure(go.Funnel(
        y=["Awareness","Engaged","Qualified","Proposal","Won"],
        x=[awareness, engaged, qualified, proposal, won],
        textinfo="value+percent initial",
        marker=dict(color=["#22D3EE","#14B8A6","#FBBF24","#F59E0B","#4ADE80"], line=dict(width=0)),
        textfont=dict(color="#F0F4F8", size=11),
        hovertemplate="<b>%{y}</b><br>%{x:,}<br>%{percentInitial:.1%}<extra></extra>"))
    fig.update_layout(height=230, margin=dict(l=0,r=0,t=8,b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#6B7FA3",size=10))
    st.markdown(f'<div class="cn-card"><div class="sec-label">Pipeline Funnel</div><div style="font-size:9px;color:#6B7FA3;margin-bottom:6px;">Overall Conversion: <b style=\'color:#4ADE80;\'>{conv}%</b></div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

def _service_donut(df):
    if df is not None and "service_name" in df.columns and "estimated_deal_value" in df.columns and len(df) > 0:
        try:
            human = _human_df(df)
            human["_deal_value_num"] = _num_series(human, "estimated_deal_value")
            rev = human.groupby("service_name")["_deal_value_num"].sum()
            total = rev.sum()
            labels = rev.index.tolist()
            values = [round(v / total * 100, 1) for v in rev.values]
            total_str = f"${total/1e6:.1f}M"
        except Exception:
            labels = ["AI Solutions","Cybersecurity","Cloud & Data","Advisory & Training","Other"]
            values = [38, 25, 20, 10, 7]
            total_str = "$82.6M"
    else:
        labels = ["AI Solutions","Cybersecurity","Cloud & Data","Advisory & Training","Other"]
        values = [38, 25, 20, 10, 7]
        total_str = "$82.6M"

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=["#22D3EE","#A855F7","#14B8A6","#FBBF24","#3A4A5E"], line=dict(color="rgba(0,0,0,0.4)",width=1)),
        textfont=dict(color="#F0F4F8", size=10),
        hovertemplate="<b>%{label}</b>: %{percent}<extra></extra>"))
    fig.add_annotation(text=total_str, x=0.5, y=0.58, font=dict(size=14,color="#FFFFFF",family="Inter"), showarrow=False)
    fig.add_annotation(text="Opportunity",  x=0.5, y=0.43, font=dict(size=9, color="#6B7FA3",family="Inter"), showarrow=False)
    fig.update_layout(height=230, margin=dict(l=0,r=0,t=8,b=0), paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#6B7FA3",size=9), orientation="v", x=1))
    st.markdown('<div class="cn-card"><div class="sec-label">Modelled Opportunity / Service Mix</div><div style="font-size:9px;color:#FBBF24;margin-bottom:6px;">Estimated deal value from synthetic signals, not confirmed revenue.</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

def _live_country_leaderboard(df):
    """Data-driven country leaderboard table from filtered df."""
    _ISO = {"South Africa":"za","Zambia":"zm","Mozambique":"mz","Botswana":"bw",
            "Angola":"ao","Zimbabwe":"zw","Namibia":"na","Malawi":"mw",
            "Democratic Republic of the Congo":"cd"}

    countries = ["South Africa","Zambia","Mozambique","Botswana","Angola","Namibia","Zimbabwe","Malawi"]

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
                rev_s = f"${rev_val:.1f}M"
            else:
                rev_s = f"${cust * 0.066:.1f}M"
        else:
            _mock = {"South Africa":(450,"$18.2M"),"Zambia":(180,"$9.5M"),"Mozambique":(140,"$7.2M"),
                     "Botswana":(95,"$4.8M"),"Angola":(72,"$3.1M"),"Namibia":(55,"$2.3M"),
                     "Zimbabwe":(88,"$4.2M"),"Malawi":(42,"$1.6M")}
            v = _mock.get(c, (0,"$0.0M"))
            cust, rev_s = v[0], v[1]

        iso  = _ISO.get(c, "za")
        flag = f'<img src="https://flagcdn.com/20x15/{iso}.png" alt="{c}" style="height:13px;width:auto;border-radius:1px;margin-right:6px;vertical-align:middle;" />'
        trend     = "▲" if cust > 50 else "▼"
        trend_col = "#76FF36" if trend == "▲" else "#F87171"
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
<div class="cn-card regional-live-card">
  <div class="sec-label" style="margin-bottom:10px;">Regional Live Leaderboard</div>
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

    pipeline_pct = min(99, int(pot_rev_m / 95 * 100)) if pot_rev_m else 87
    base_pipeline = min(99, int(float(baseline.get("opportunity", 0) or 0) / 1e6 / 95 * 100)) if baseline else 0
    pipeline_delta, pipeline_cls = _metric_delta({"pipeline": pipeline_pct}, {"pipeline": base_pipeline}, "pipeline", "rate")
    potential_delta, potential_cls = _metric_delta(stats, baseline, "potential")
    demo_delta, demo_cls = _metric_delta(stats, baseline, "demos")
    opp_delta, opp_cls = _metric_delta(stats, baseline, "opportunity")

    kpis = [
        ("Pipeline Target Attainment", f"{pipeline_pct}%", f"${pot_rev_m}M / $95M target", pipeline_delta, pipeline_cls, "anchor"),
        ("Potential Customers", f"{pot_cust:,}", f"today vs {baseline_label}", potential_delta, potential_cls, ""),
        ("Demo Requests", f"{demo_req:,}", f"today vs {baseline_label}", demo_delta, demo_cls, ""),
        ("Potential Opportunity Value", f"${pot_rev_m}M", f"modelled; today vs {baseline_label}", opp_delta, opp_cls, ""),
        ("Top Sales Market", f"{flag_img}{top_market}", f"{top_pct}% of today's potential", "", "", ""),
    ]
    cols = st.columns(5, gap="small")
    cls_map = {"up":"delta-up","watch":"delta-watch","down":"delta-down"}
    for col, (lbl, val, sub, chg, cls, extra) in zip(cols, kpis):
        with col:
            delta = f'<div class="kpi-delta {cls_map.get(cls,"")}">{chg}</div>' if chg else ""
            anchor_style = "border-color:rgba(34,211,238,0.45);box-shadow:0 0 22px rgba(34,211,238,0.15);" if extra == "anchor" else ""
            st.markdown(f'<div class="kpi-card" style="min-height:132px;{anchor_style}"><div class="kpi-label">{lbl}</div><div class="kpi-value live-count" style="font-size:1.75rem;">{val}</div>{delta}<div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

def render_sales_overview(df):
    # KPI/live counters intentionally use unfiltered data; filters affect charts/tables below.
    st.session_state["_sales_df_cache"] = st.session_state.get("_live_unfiltered_df", df)

    # ── Live KPI Section ──
    st.markdown("""
<div style="padding:16px 20px;border-radius:20px;border:1px solid rgba(255,255,255,0.10);
  background:rgba(7,14,22,0.74);margin-bottom:14px;">
  <div style="font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
    color:#00F5D4;margin-bottom:4px;">What is currently going on</div>
  <div style="font-size:12px;color:rgba(245,247,250,0.55);margin-bottom:14px;">
    Live Sales indicators for the selected period and market.</div>
""", unsafe_allow_html=True)

    # Try live fragment for KPI refresh
    try:
        @st.fragment(run_every=1)
        def _live_sales_kpis():
            _df = st.session_state.get("_sales_df_cache")
            if _df is not None:
                _live_today = _live_today_df(_df, "sales_kpi_cards")
                _sales_kpis(_live_today)
        _live_sales_kpis()
    except Exception:
        _sales_kpis(df)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Map + Leaderboard container ──
    st.markdown("""
<div style="margin-bottom:14px;">
  <div style="font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
    color:#00F5D4;margin-bottom:2px;">Potential Customer Hotzones</div>
  <div style="font-size:12px;color:rgba(245,247,250,0.55);margin-bottom:10px;">
    Stable market geography; live movement is shown in the regional leaderboard.</div>
</div>
""", unsafe_allow_html=True)

    map_col, tbl_col = st.columns([2.2, 1], gap="small")
    with map_col:
        render_sadc_map("sales", 420)
    with tbl_col:
        try:
            @st.fragment(run_every=1)
            def _live_sales_leaderboard():
                _live_country_leaderboard(_live_today_df(st.session_state.get("_sales_df_cache"), "sales_regional_leaderboard"))
            _live_sales_leaderboard()
        except Exception:
            _live_country_leaderboard(df)

    # ── Sales performance drivers label ──
    st.markdown("""
<div style="margin:14px 0 8px 0;">
  <div style="font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
    color:#00F5D4;margin-bottom:2px;">Sales performance drivers</div>
  <div style="font-size:12px;color:rgba(245,247,250,0.55);margin-bottom:10px;">
    Trend, funnel, and service mix explaining current sales movement.</div>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="small")
    with c1: _sales_growth(df)
    with c2: _pipeline_funnel(df)
    with c3: _service_donut(df)

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
    _cl(fig,220); fig.update_layout(xaxis_title="Visitors",yaxis_title="Engagement %")
    st.markdown('<div class="cn-card"><div class="sec-label">Market Opportunity Matrix</div><div style="font-size:9px;color:#6B7FA3;margin-bottom:6px;">Bubble size = Potential Customers</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

def _promo_gap():
    svcs=["AI Solutions","Cybersecurity","Cloud & Data","Advisory","Other"]
    fig=go.Figure()
    fig.add_trace(go.Bar(x=svcs,y=[35,28,22,10,5],name="Visit Share %",marker_color="#3A4A5E",hovertemplate="<b>%{x}</b><br>Visit Share: %{y}%<extra></extra>"))
    fig.add_trace(go.Bar(x=svcs,y=[42,24,18,12,4],name="Conversion Share %",marker_color="#22D3EE",hovertemplate="<b>%{x}</b><br>Conversion: %{y}%<extra></extra>"))
    _cl(fig,220); fig.update_layout(barmode="group",bargap=0.28)
    st.markdown('<div class="cn-card"><div class="sec-label">Service Promotion Gap</div><div style="font-size:9px;color:#FBBF24;margin-bottom:6px;">⚠ Cybersecurity: high conversion, low visit share → under-promoted</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

def _content_funnel():
    fig=go.Figure(go.Funnel(y=["Landing Page","Service Page","AI/Contact Interest","Demo / Event Action"],x=[8500,3800,1640,520],
        textinfo="value+percent initial",
        marker=dict(color=["#22D3EE","#14B8A6","#A855F7","#4ADE80"],line=dict(width=0)),
        textfont=dict(color="#F0F4F8",size=11),
        hovertemplate="<b>%{y}</b><br>%{x:,}<br>%{percentInitial:.1%}<extra></extra>"))
    fig.update_layout(height=220,margin=dict(l=0,r=0,t=8,b=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#6B7FA3",size=10))
    st.markdown('<div class="cn-card"><div class="sec-label">Content Journey Funnel</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

def _activity_heatmap():
    np.random.seed(7)
    z=np.random.randint(10,180,(7,24)); z[1:5,8:18]+=100
    fig=go.Figure(go.Heatmap(z=z,x=[f"{h:02d}:00" for h in range(24)],y=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
        colorscale=[[0,"rgba(7,16,28,0.9)"],[0.5,"rgba(34,211,238,0.4)"],[1,"#22D3EE"]],
        hovertemplate="<b>%{y} %{x}</b><br>Activity: %{z}<extra></extra>",showscale=False))
    fig.update_layout(height=220,margin=dict(l=0,r=0,t=8,b=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(7,16,28,0.6)",font=dict(color="#6B7FA3",size=9),xaxis=dict(tickangle=-45,color="#6B7FA3"),yaxis=dict(color="#6B7FA3"))
    st.markdown('<div class="cn-card"><div class="sec-label">Human Activity Timing</div><div style="font-size:9px;color:#6B7FA3;margin-bottom:6px;">Best: Tue–Thu, 09:00–17:00</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

def _mkt_right():
    st.markdown("""
<div class="cn-card">
  <div class="sec-label">Best Campaign Market</div>
  <div style="font-size:18px;font-weight:800;color:#14B8A6;">South Africa</div>
  <div style="font-size:10px;color:#6B7FA3;margin-top:4px;">31% engagement · Highest quality audience</div>
</div>
<div class="cn-card">
  <div class="sec-label">Campaign Signals</div>
  <div style="font-size:11px;margin-bottom:5px;color:#F0F4F8;"><span style="color:#4ADE80;">●</span> AI Solutions — <b>High Intent</b></div>
  <div style="font-size:11px;margin-bottom:5px;color:#F0F4F8;"><span style="color:#FBBF24;">●</span> Cybersecurity — <b>Under-Promoted</b></div>
  <div style="font-size:11px;color:#F0F4F8;"><span style="color:#22D3EE;">●</span> Cloud & Data — <b>Growing</b></div>
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
    kpis=[
        ("Engaged Visitors", f"{stats['engaged']:,}", f"today vs {baseline_label}", engaged_delta, engaged_cls),
        ("Engagement Rate", f"{stats['engagement_rate']:.1f}%", f"today vs {baseline_label}", engagement_delta, engagement_cls),
        ("Best Campaign Market", stats["top_market"], "highest current volume", "", ""),
        ("Best Landing Page", stats["top_service"], "top service demand", "", ""),
        ("Audience Quality", f"{stats['quality']}%", f"today vs {baseline_label}", quality_delta, quality_cls),
    ]
    cols=st.columns(5,gap="small")
    cls_map={"up":"delta-up","watch":"delta-watch","down":"delta-down"}
    for col,(lbl,val,sub,chg,cls) in zip(cols,kpis):
        with col:
            delta=f'<div class="kpi-delta {cls_map.get(cls,"")}">{chg}</div>' if chg else ""
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">{lbl}</div><div class="kpi-value-sm live-count" style="color:#14B8A6;">{val}</div>{delta}<div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

def render_marketing_overview(df):
    st.session_state["_marketing_df_cache"] = st.session_state.get("_live_unfiltered_df", df)
    try:
        @st.fragment(run_every=1)
        def _live_marketing_kpis():
            _mkt_kpis(st.session_state.get("_marketing_df_cache"))
        _live_marketing_kpis()
    except Exception:
        _mkt_kpis(df)
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    render_live_pulse()
    ml,mr=st.columns([1.7,1],gap="small")
    with ml:
        render_sadc_map("marketing", 380)
    with mr:
        if _MARKETING_VIEWS_OK:
            st.markdown(render_marketing_drawer(), unsafe_allow_html=True)
        else:
            _mkt_right()
    c1,c2,c3,c4=st.columns(4,gap="small")
    with c1: _opportunity_matrix()
    with c2: _promo_gap()
    with c3: _content_funnel()
    with c4: _activity_heatmap()

# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
def _strategic_growth():
    mo=["Jan","Feb","Mar","Apr","May","Jun"]
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=mo,y=[72,76,79,82,82.6,None],name="Revenue ($M)",line=dict(color="#22D3EE",width=2),mode="lines+markers",marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=mo,y=[28,32,35,38,40,None],name="AI Solutions",line=dict(color="#A855F7",width=2),mode="lines+markers",marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=mo,y=[44,44,44,44,42.6,None],name="Services",line=dict(color="#14B8A6",width=2),mode="lines+markers",marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=mo,y=[80,83,85,90,95,100],name="Target",line=dict(color="#A855F7",width=1.5,dash="dash"),mode="lines"))
    fig.add_trace(go.Scatter(x=mo,y=[68,72,76,79,82,82.6],name="Prev. Month",line=dict(color="#3A4A5E",width=1.5,dash="dot"),mode="lines"))
    _cl(fig,230)
    st.markdown('<div class="cn-card"><div class="sec-label">Strategic Growth Trend</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

def _ai_traction():
    mo=["Jan","Feb","Mar","Apr"]
    fig=go.Figure()
    fig.add_trace(go.Bar(x=mo,y=[22,25,27,29],name="AI Interest %",marker_color="rgba(34,211,238,0.7)"))
    fig.add_trace(go.Scatter(x=mo,y=[25,25,28,30],name="Target %",mode="lines+markers",line=dict(color="#A855F7",width=2,dash="dash"),marker=dict(size=5)))
    _cl(fig,230); fig.update_layout(barmode="group",bargap=0.3,yaxis_title="% Sessions")
    st.markdown('<div class="cn-card"><div class="sec-label">AI Assistant Traction</div><span style="background:rgba(168,85,247,0.12);color:#A855F7;border:1px solid rgba(168,85,247,0.25);border-radius:20px;padding:2px 9px;font-size:9px;font-weight:700;">Target Achievement: 97%</span>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
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
    _cl(fig,230)
    st.markdown('<div class="cn-card"><div class="sec-label">90-Day Forecast</div><div style="font-size:9px;color:#FBBF24;margin-bottom:6px;">⚠ Rule-based linear forecast, not predictive AI.</div>', unsafe_allow_html=True)
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

def _exec_right():
    st.markdown("""
<div class="cn-card">
  <div class="sec-label">Regional Priority</div>
  <div style="font-size:14px;font-weight:700;color:#A855F7;">South Africa + Zambia</div>
  <div style="font-size:10px;color:#6B7FA3;margin-top:4px;">Core + Strategic Hub anchors</div>
  <div style="font-size:11px;color:#4ADE80;margin-top:6px;font-weight:600;">✓ Invest — protect lead</div>
</div>
<div class="cn-card">
  <div class="sec-label">Strategic Signals</div>
  <div style="font-size:11px;margin-bottom:5px;color:#F0F4F8;"><span style="color:#4ADE80;">●</span> AI Solutions — <b>Accelerating</b></div>
  <div style="font-size:11px;margin-bottom:5px;color:#F0F4F8;"><span style="color:#22D3EE;">●</span> SADC Expansion — <b>On Track</b></div>
  <div style="font-size:11px;color:#F0F4F8;"><span style="color:#F87171;">●</span> Zimbabwe — <b>Monitor</b></div>
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
            delta=f'<div class="kpi-delta {cls_map.get(cls,"")}">{chg}</div>' if chg else ""
            st.markdown(f'<div class="kpi-card"><div class="kpi-label">{lbl}</div><div class="kpi-value-sm live-count" style="color:#A855F7;">{val}</div>{delta}<div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)
    st.markdown(f"""
<div style="background:linear-gradient(90deg,rgba(168,85,247,0.07),rgba(34,211,238,0.04));
  border:1px solid rgba(168,85,247,0.18);border-radius:10px;padding:10px 16px;margin:8px 0;">
  <span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.14em;color:#A855F7;">Board Summary · </span>
  <span style="font-size:12px;color:#F0F4F8;">
    Live simulation is based on the selected CyberNova dataset. Opportunity value is a modelled estimate, not audited revenue.
  </span>
</div>""", unsafe_allow_html=True)

def render_executive_overview(df):
    st.session_state["_executive_df_cache"] = st.session_state.get("_live_unfiltered_df", df)
    try:
        @st.fragment(run_every=1)
        def _live_executive_kpis():
            _exec_kpis(st.session_state.get("_executive_df_cache"))
        _live_executive_kpis()
    except Exception:
        _exec_kpis(df)
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    render_live_pulse()
    ml,mr=st.columns([1.7,1],gap="small")
    with ml:
        render_sadc_map("executive", 380)
    with mr:
        if _EXECUTIVE_VIEWS_OK:
            st.markdown(render_executive_drawer(), unsafe_allow_html=True)
        else:
            _exec_right()
    c1,c2,c3=st.columns([1.4,1,1],gap="small")
    with c1: _strategic_growth()
    with c2: _ai_traction()
    with c3: _forecast_90()

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTICS / FORECASTING / DATA TABS
# ═══════════════════════════════════════════════════════════════════════════════
def render_analytics_tab(dash):
    CARDS={"Sales":[("Funnel by Market","📊"),("Funnel by Service","📊"),("Repeat Visitor Conversion","🔄"),
                    ("Potential Customer Segment Quality","💎"),("Sales Insight Assistant","🤖"),("Sales Hotzones Map","🗺️"),
                    ("Top Service Demand","📈"),("Potential Customers by Country","🌍"),("Demo Intent by Hour","⏰"),("Conversion Rate by Stage","🎯")],
           "Marketing":[("Audience Segments Over Time","📈"),("Country Engagement Breakdown","🌍"),
                        ("Landing Page Performance","📄"),("SADC Reach Map + Ranking","🗺️"),("Service Promotion Gap Detail","📊"),("Marketing Insight Assistant","🤖")],
           "Executive":[("Regional Target Table","📋"),("Market Contribution Analysis","📊"),
                        ("AI Assistant by Market","🤖"),("Risk / Anomaly Trend","⚠️"),("Executive Insight Assistant","🌐")]}
    ph_grid(CARDS.get(dash,[]))

def render_forecasting_tab(dash):
    CARDS={"Sales":[("Forecast Summary","📋"),("Forecast Confidence","🎯"),("30-Day Potential Customer Forecast","📈"),
                    ("Demo Request Forecast","📊"),("AI-to-Demo What-If Analysis","🤖"),("Forecast vs Target","🏁"),
                    ("Sales Readiness Recommendations","💡"),("Market Outlook","🗺️"),("Risk Outlook","⚠️"),("Alert Center","🔔")],
           "Marketing":[("Audience Growth Forecast","📈"),("Engaged Sessions Forecast","📊"),
                        ("Campaign What-If Scenario","🤖"),("Campaign Target Tracker","🏁"),("Campaign Recommendation","💡")],
           "Executive":[("90-Day Potential Customer Forecast","📈"),("Regional Expansion Forecast","🗺️"),
                        ("AI Traction Forecast","🤖"),("Risk / Anomaly Outlook","⚠️"),("Investment Recommendation","💡"),("Forecast vs Target","🏁")]}
    ph_grid(CARDS.get(dash,[]))

def render_data_tab(dash,df):
    CARDS={"Sales":[("Sales Action Queue","✅"),("Potential Customers Table","📋"),("Evidence Snapshot","📂"),
                    ("Export Center","💾"),("Data Quality Summary","🔍"),("Methodology & Assumptions","📖"),
                    ("Potential Revenue by Region","💰"),("New Potential Customers Trend","📈"),("Top Customers by Revenue","🏆")],
           "Marketing":[("Campaign Opportunity Table","📋"),("Filtered Audience Data","📂"),("Evidence Pack CSV","💾"),
                        ("Weekly PDF Report","📄"),("Monthly PDF Report","📄"),("Methodology Note","📖"),("Landing Page Export","📑"),("Campaign Performance Export","📊")],
           "Executive":[("Executive Decision Brief","📋"),("Regional Priority Table","🗺️"),("Risk Evidence Table","⚠️"),
                        ("Executive Summary CSV","💾"),("Filtered Data CSV","📂"),("Weekly PDF Report","📄"),("Monthly PDF Report","📄"),("Methodology Note","📖")]}
    ph_grid(CARDS.get(dash,[]))
    if df is not None:
        st.markdown('<div class="cn-card"><div class="sec-label">Quick Export</div>', unsafe_allow_html=True)
        h=_human_df(df)
        st.download_button("⬇ Download Filtered Data (CSV)",h.head(5000).to_csv(index=False).encode(),f"cybernova_{dash.lower()}.csv","text/csv",use_container_width=True)
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
  <div style="margin-left:auto;font-size:10px;color:#2A3A4E;">CyberNova BI Portal · Prototype v1.0</div>
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

        with st.spinner(""):
            df = load_data()
            if df is None:
                st.toast("Using mock data — CSV not found", icon="⚠️")
                df = mock_data()

        st.session_state["_live_unfiltered_df"] = df

        # Apply date filter
        if "date" in df.columns or "timestamp" in df.columns:
            date_col = "date" if "date" in df.columns else "timestamp"
            d_start = st.session_state.get("date_start")
            d_end = st.session_state.get("date_end")
            if d_start and d_end:
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

        render_chips(df_f)

        dash = st.session_state.active_dashboard
        t_ov, t_an, t_fc, t_de = st.tabs(["Overview","Analytics","Forecasting","Data & Export"])
        with t_ov:
            if dash=="Sales":       render_sales_overview(df_f)
            elif dash=="Marketing": render_marketing_overview(df_f)
            else:                   render_executive_overview(df_f)
        with t_an:
            if dash=="Sales" and _SALES_VIEWS_OK:
                render_sales_analytics(df_f)
            elif dash=="Marketing" and _MARKETING_VIEWS_OK:
                render_marketing_analytics(df_f)
            elif dash=="Executive" and _EXECUTIVE_VIEWS_OK:
                render_executive_analytics(df_f)
            else:
                render_analytics_tab(dash)
        with t_fc:
            if dash=="Sales" and _SALES_VIEWS_OK:
                render_sales_forecasting(df_f)
            elif dash=="Marketing" and _MARKETING_VIEWS_OK:
                render_marketing_forecasting(df_f)
            elif dash=="Executive" and _EXECUTIVE_VIEWS_OK:
                render_executive_forecasting(df_f)
            else:
                render_forecasting_tab(dash)
        with t_de:
            d_start = st.session_state.get("date_start")
            d_end = st.session_state.get("date_end")
            if dash=="Sales" and _SALES_VIEWS_OK:
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

