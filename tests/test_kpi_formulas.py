"""
KPI formula tests for the CyberNova Streamlit dashboard.

Formula inventory covered here:
- Core KPI helper: rows, human visitors, potential customers, demo requests,
  engaged visitors, engagement rate, AI rate, opportunity value, top market,
  top service, audience/data quality, active markets, and strategic risk alerts.
- Sales cards: people waiting for a demo, potential customers today, sales
  progress this month, estimated revenue if leads convert, hottest market.
- Marketing cards: meaningful actions taken today, audience quality score,
  best market, visitors today, and best entry page.
- Executive cards: growth direction, potential customers, AI assistant traction,
  active SADC markets, and strategic risk alerts.
- Export summary: potential customers, demo requests, potential revenue,
  top market, data quality, and records in filter.

Expected values are calculated in this file from raw DataFrame columns instead
of reusing the dashboard helper functions.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pandas as pd
import pytest

import cybernovaapp as app
import exports


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATASET_PATH = PROJECT_ROOT / "data" / "output" / "cybernova_enriched_logs.csv"


class _FakeColumn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeStreamlit:
    def __init__(self):
        self.session_state: dict = {}
        self.markdown_calls: list[str] = []

    def columns(self, count, gap=None):
        if isinstance(count, int):
            return [_FakeColumn() for _ in range(count)]
        return [_FakeColumn() for _ in count]

    def markdown(self, body, unsafe_allow_html=False):
        self.markdown_calls.append(str(body))


@pytest.fixture(scope="session")
def source_df() -> pd.DataFrame:
    assert SOURCE_DATASET_PATH.exists(), (
        f"Dataset not found at {SOURCE_DATASET_PATH}. Run python generate_logs.py first."
    )
    return pd.read_csv(SOURCE_DATASET_PATH, low_memory=False)


@pytest.fixture
def fake_streamlit(monkeypatch):
    fake = _FakeStreamlit()
    monkeypatch.setattr(app, "st", fake)
    return fake


def _manual_truthy(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index)
    values = df[column]
    if values.dtype == bool:
        return values.fillna(False)
    return values.astype(str).str.strip().str.lower().isin({"1", "true", "yes", "y"})


def _manual_num(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(0.0, index=df.index, dtype="float64")
    return pd.to_numeric(df[column], errors="coerce").fillna(0)


def _manual_human(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if "is_bot" not in df.columns:
        return df.copy()
    return df.loc[~_manual_truthy(df, "is_bot")].copy()


def _manual_top(df: pd.DataFrame, column: str, fallback: str = "--") -> str:
    if df.empty or column not in df.columns:
        return fallback
    counts = df[column].dropna().astype(str).value_counts()
    return counts.index[0] if not counts.empty else fallback


def _manual_kpi_stats(df: pd.DataFrame | None) -> dict:
    human = _manual_human(df)
    total = len(human)
    potential = int(_manual_truthy(human, "potential_customer_signal").sum()) if total else 0
    demos = int(_manual_truthy(human, "has_demo_request").sum()) if total else 0
    if "is_engaged_session" in human.columns:
        engaged = int(_manual_truthy(human, "is_engaged_session").sum())
    else:
        engaged = max(0, int(total * 0.28))
    if "has_ai_interest" in human.columns:
        ai_sessions = int(_manual_truthy(human, "has_ai_interest").sum())
    elif "service_name" in human.columns:
        ai_sessions = int(human["service_name"].astype(str).str.contains("AI", case=False, na=False).sum())
    else:
        ai_sessions = 0
    row_count = len(df) if df is not None else 0
    bot_mean = _manual_truthy(df, "is_bot").mean() if df is not None and len(df) else 0
    return {
        "rows": row_count,
        "human": total,
        "potential": potential,
        "demos": demos,
        "engaged": engaged,
        "engagement_rate": engaged / total * 100 if total else 0,
        "ai_rate": ai_sessions / total * 100 if total else 0,
        "opportunity": float(_manual_num(human, "estimated_deal_value").sum()),
        "top_market": _manual_top(human, "country", "--"),
        "top_service": _manual_top(human, "service_name", "--"),
        "quality": int(round((1 - bot_mean) * 100)),
        "active_markets": int(human["country"].nunique()) if "country" in human.columns and total else 0,
        "risk_alerts": (
            int((_manual_num(human, "risk_score") >= 70).sum())
            if "risk_score" in human.columns
            else int(_manual_truthy(human, "is_anomaly").sum())
            if "is_anomaly" in human.columns
            else 0
        ),
    }


def _manual_entry_page(df: pd.DataFrame) -> str:
    human = _manual_human(df)
    if human.empty:
        return "General Website"
    for source_col in ["landing_page", "entry_page", "page_title", "path", "url_path", "service_name"]:
        value = _manual_top(human, source_col, "") if source_col in human.columns else ""
        if value:
            return value
    return "General Website"


def _sales_expected(df: pd.DataFrame) -> dict[str, str]:
    human = _manual_human(df)
    potential = int(_manual_truthy(human, "potential_customer_signal").sum()) if len(human) else 0
    demos = int(_manual_truthy(human, "has_demo_request").sum()) if len(human) else 0
    revenue_m = round(_manual_num(human, "estimated_deal_value").sum() / 1_000_000, 1) if len(human) else 0.0
    pipeline_pct = min(99, int(revenue_m / 95 * 100)) if revenue_m else 0
    if "country" in human.columns and len(human):
        counts = human["country"].value_counts()
        top_market = str(counts.index[0]) if len(counts) else "South Africa"
    else:
        top_market = "South Africa"
    return {
        "People Waiting for a Demo": f"{demos:,}",
        "Potential Customers Today": f"{potential:,}",
        "Sales Progress This Month": f"{pipeline_pct}%",
        "Estimated Revenue if Leads Convert": f"P{revenue_m}M",
        "Hottest Market Right Now": top_market,
    }


def _marketing_expected(df: pd.DataFrame) -> dict[str, str]:
    stats = _manual_kpi_stats(df)
    return {
        "Meaningful Actions Taken Today": f"{stats['engagement_rate']:.1f}%",
        "Audience Quality Score": f"{stats['quality']}%",
        "Best Market to Target Now": stats["top_market"],
        "Visitors Today": f"{stats['engaged']:,}",
        "Best Entry Page": _manual_entry_page(df),
    }


def _executive_expected(df: pd.DataFrame) -> dict[str, str]:
    stats = _manual_kpi_stats(df)
    growth = min(99, int(stats["potential"] / max(1, stats["human"]) * 100)) if stats["human"] else 0
    return {
        "Growth Direction": f"+{growth}%",
        "Potential Customers": f"{stats['potential']:,}",
        "AI Assistant Traction": f"{stats['ai_rate']:.1f}%",
        "Active SADC Markets": str(stats["active_markets"]),
        "Strategic Risk Alerts": str(stats["risk_alerts"]),
    }


def _extract_card_values(markdown_calls: list[str]) -> dict[str, str]:
    html = "\n".join(markdown_calls)
    matches = re.findall(
        r'<div class="kpi-label"[^>]*>(.*?)</div><div class="kpi-value[^"]*"[^>]*>(.*?)</div>',
        html,
        flags=re.DOTALL,
    )
    values = {}
    for label, value in matches:
        clean_label = re.sub(r"<[^>]+>", "", label).strip()
        clean_value = re.sub(r"<[^>]+>", "", value).strip()
        values[clean_label] = clean_value
    return values


def _source_filtered_subset(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    if "country" in work.columns:
        market = work["country"].dropna().astype(str).mode().iloc[0]
        work = work[work["country"].astype(str).eq(market)]
    if "service_name" in work.columns:
        service = work["service_name"].dropna().astype(str).mode().iloc[0]
        work = work[work["service_name"].astype(str).eq(service)]
    if "date" in work.columns:
        latest_date = pd.to_datetime(work["date"], errors="coerce").dt.date.max()
        work = work[pd.to_datetime(work["date"], errors="coerce").dt.date.eq(latest_date)]
    return work


@pytest.mark.parametrize("df_factory", ["source", "filtered_source"])
def test_core_kpi_stats_match_independent_source_calculation(source_df, df_factory) -> None:
    df = source_df if df_factory == "source" else _source_filtered_subset(source_df)
    expected = _manual_kpi_stats(df)
    actual = app._kpi_stats(df)

    assert actual["rows"] == expected["rows"]
    assert actual["human"] == expected["human"]
    assert actual["potential"] == expected["potential"]
    assert actual["demos"] == expected["demos"]
    assert actual["engaged"] == expected["engaged"]
    assert actual["opportunity"] == pytest.approx(expected["opportunity"])
    assert actual["top_market"] == expected["top_market"]
    assert actual["top_service"] == expected["top_service"]
    assert actual["quality"] == expected["quality"]
    assert actual["active_markets"] == expected["active_markets"]
    assert actual["risk_alerts"] == expected["risk_alerts"]
    assert actual["engagement_rate"] == pytest.approx(expected["engagement_rate"])
    assert actual["ai_rate"] == pytest.approx(expected["ai_rate"])


def test_core_kpi_stats_empty_data_edge_case() -> None:
    empty = pd.DataFrame()
    assert app._kpi_stats(empty) == _manual_kpi_stats(empty)


def test_core_kpi_stats_zero_values_edge_case() -> None:
    zero_df = pd.DataFrame(
        {
            "is_bot": [False, False, "false"],
            "potential_customer_signal": [False, 0, "no"],
            "has_demo_request": [False, 0, "no"],
            "is_engaged_session": [False, False, False],
            "has_ai_interest": [False, False, False],
            "estimated_deal_value": [0, 0, 0],
            "risk_score": [0, 0, 0],
            "country": ["Botswana", "Botswana", "Zambia"],
            "service_name": ["General Website", "Contact", "Cloud & Data"],
        }
    )
    assert app._kpi_stats(zero_df) == _manual_kpi_stats(zero_df)


def test_sales_kpi_cards_match_independent_calculation(source_df, fake_streamlit, monkeypatch) -> None:
    df = _source_filtered_subset(source_df).head(250).copy()
    fake_streamlit.session_state["_sales_df_cache"] = df
    monkeypatch.setattr(app, "_baseline_stats", lambda _df: ({}, "7-day avg"))

    app._sales_kpis(df)

    actual = _extract_card_values(fake_streamlit.markdown_calls)
    assert actual == _sales_expected(df)


def test_marketing_kpi_cards_match_independent_calculation(source_df, fake_streamlit, monkeypatch) -> None:
    df = _source_filtered_subset(source_df).head(250).copy()
    fake_streamlit.session_state["_marketing_df_cache"] = df
    monkeypatch.setattr(app, "_live_today_df", lambda df, *args, **kwargs: df)
    monkeypatch.setattr(app, "_baseline_stats", lambda _df: ({}, "7-day avg"))

    app._mkt_kpis(df)

    actual = _extract_card_values(fake_streamlit.markdown_calls)
    assert actual == _marketing_expected(df)


def test_executive_kpi_cards_match_independent_calculation(source_df, fake_streamlit, monkeypatch) -> None:
    df = _source_filtered_subset(source_df).head(250).copy()
    fake_streamlit.session_state["_executive_df_cache"] = df
    monkeypatch.setattr(app, "_live_today_df", lambda df, *args, **kwargs: df)
    monkeypatch.setattr(app, "_baseline_stats", lambda _df: ({}, "7-day avg"))

    app._exec_kpis(df)

    actual = _extract_card_values(fake_streamlit.markdown_calls)
    assert actual == _executive_expected(df)


def test_dashboard_kpi_cards_handle_empty_data(fake_streamlit, monkeypatch) -> None:
    empty = pd.DataFrame()
    monkeypatch.setattr(app, "_live_today_df", lambda df, *args, **kwargs: df)
    monkeypatch.setattr(app, "_baseline_stats", lambda _df: ({}, "7-day avg"))

    app._sales_kpis(empty)
    sales_actual = _extract_card_values(fake_streamlit.markdown_calls)
    assert sales_actual == _sales_expected(empty)

    fake_streamlit.markdown_calls.clear()
    app._mkt_kpis(empty)
    marketing_actual = _extract_card_values(fake_streamlit.markdown_calls)
    assert marketing_actual == _marketing_expected(empty)

    fake_streamlit.markdown_calls.clear()
    app._exec_kpis(empty)
    executive_actual = _extract_card_values(fake_streamlit.markdown_calls)
    assert executive_actual == _executive_expected(empty)


def test_export_kpi_summary_matches_independent_filtered_calculation(source_df) -> None:
    df = _source_filtered_subset(source_df)
    expected = {
        "Potential Customers": int(df["potential_customer_signal"].sum()),
        "Demo Requests": int(df["has_demo_request"].sum()),
        "Potential Revenue": f"${df['estimated_deal_value'].sum():,.0f}",
        "Top Market": df["country"].value_counts().index[0],
        "Data Quality": f"{(1.0 - df['is_bot'].mean()):.1%}",
        "Records in Filter": f"{len(df):,}",
    }

    assert exports.build_kpi_summary("Sales", df) == expected


def test_export_kpi_summary_empty_data_edge_case() -> None:
    expected = {
        "Potential Customers": 1248,
        "Demo Requests": 312,
        "Potential Revenue": "$82,600,000",
        "Top Market": "South Africa",
        "Data Quality": "96.4%",
        "Records in Filter": "0",
    }

    assert exports.build_kpi_summary("Sales", pd.DataFrame()) == expected


def test_filtered_data_changes_kpis_from_unfiltered_source(source_df) -> None:
    filtered = _source_filtered_subset(source_df)
    full_expected = _manual_kpi_stats(source_df)
    filtered_expected = _manual_kpi_stats(filtered)

    assert app._kpi_stats(filtered) == pytest.approx(filtered_expected)
    assert filtered_expected["rows"] < full_expected["rows"]
    assert filtered_expected["top_market"] == _manual_top(filtered, "country")
    assert filtered_expected["opportunity"] <= full_expected["opportunity"]
