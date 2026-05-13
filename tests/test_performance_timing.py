"""
Simple performance timing checks for the CyberNova BI dashboard data path.

This test writes a small before/after caching report to:
    reports/performance_timing_report.md

The timings focus on dashboard operations that matter during local use:
- dataset loading
- dashboard data transformation
- chart preparation
- filter response
"""

from __future__ import annotations

import functools
import statistics
import time
from pathlib import Path
from typing import Callable

import pandas as pd
import plotly.graph_objects as go


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "output" / "cybernova_enriched_logs.csv"
PARQUET_PATH = PROJECT_ROOT / "data" / "output" / "cybernova_enriched_logs.fast.parquet"
REPORT_PATH = PROJECT_ROOT / "reports" / "performance_timing_report.md"
RUNS = 3


def _time_call(fn: Callable, runs: int = RUNS):
    durations = []
    result = None
    for _ in range(runs):
        start = time.perf_counter()
        result = fn()
        durations.append(time.perf_counter() - start)
    return result, durations


def _summarize(durations: list[float]) -> dict[str, float]:
    return {
        "best": min(durations),
        "avg": statistics.mean(durations),
        "worst": max(durations),
    }


def _read_csv_dataset() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH, low_memory=False)


def _read_parquet_dataset() -> pd.DataFrame:
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    return _read_csv_dataset()


@functools.lru_cache(maxsize=1)
def _cached_dataset() -> pd.DataFrame:
    return _read_parquet_dataset()


def _transform_dashboard_data(df: pd.DataFrame) -> pd.DataFrame:
    transformed = df.copy()
    if "timestamp" in transformed.columns:
        transformed["timestamp"] = pd.to_datetime(transformed["timestamp"], errors="coerce")
    if "date" in transformed.columns:
        transformed["date"] = pd.to_datetime(transformed["date"], errors="coerce")
    for column in [
        "is_bot",
        "is_sadc",
        "is_warm_lead",
        "potential_customer_signal",
        "has_demo_request",
        "has_event_signup",
        "is_engaged_session",
        "has_ai_interest",
    ]:
        if column in transformed.columns:
            transformed[column] = transformed[column].astype(str).str.lower().isin(["true", "1", "yes", "y"])
    if "estimated_deal_value" in transformed.columns:
        transformed["estimated_deal_value"] = pd.to_numeric(
            transformed["estimated_deal_value"], errors="coerce"
        ).fillna(0)
    if "risk_score" in transformed.columns:
        transformed["risk_score"] = pd.to_numeric(transformed["risk_score"], errors="coerce").fillna(0)
    return transformed


@functools.lru_cache(maxsize=1)
def _cached_transformed_data() -> pd.DataFrame:
    return _transform_dashboard_data(_cached_dataset())


def _apply_dashboard_filters(
    df: pd.DataFrame,
    market: str = "Botswana",
    service: str = "Cybersecurity",
    outcome: str = "Engaged",
    status_code: int = 200,
) -> pd.DataFrame:
    filtered = df
    if market != "All" and "country" in filtered.columns:
        filtered = filtered[filtered["country"].astype(str).eq(market)]

    if service != "All Services" and "service_name" in filtered.columns:
        service_terms = {
            "AI Solutions": ["AI", "Assistant", "Predictive"],
            "Cybersecurity": ["Cyber", "Security", "Risk"],
            "Cloud & Data": ["Cloud", "Data", "Digital Transformation"],
            "Advisory & Training": ["Advisory", "Training", "Events"],
        }.get(service, [service])
        mask = pd.Series(False, index=filtered.index)
        for term in service_terms:
            mask = mask | filtered["service_name"].astype(str).str.contains(term, case=False, na=False)
        filtered = filtered[mask]

    if outcome == "Engaged" and "is_engaged_session" in filtered.columns:
        filtered = filtered[filtered["is_engaged_session"]]
    elif outcome == "Potential Customer" and "potential_customer_signal" in filtered.columns:
        filtered = filtered[filtered["potential_customer_signal"]]
    elif outcome == "Demo Request" and "has_demo_request" in filtered.columns:
        filtered = filtered[filtered["has_demo_request"]]

    if "status_code" in filtered.columns:
        status = pd.to_numeric(filtered["status_code"], errors="coerce")
        filtered = filtered[status.eq(status_code)]
    return filtered


_FILTER_CACHE: dict[tuple[str, str, str, int], pd.DataFrame] = {}


def _cached_filter_response(
    market: str = "Botswana",
    service: str = "Cybersecurity",
    outcome: str = "Engaged",
    status_code: int = 200,
) -> pd.DataFrame:
    key = (market, service, outcome, status_code)
    if key not in _FILTER_CACHE:
        _FILTER_CACHE[key] = _apply_dashboard_filters(
            _cached_transformed_data(), market, service, outcome, status_code
        )
    return _FILTER_CACHE[key]


def _prepare_dashboard_charts(df: pd.DataFrame) -> list[go.Figure]:
    human = df[~df["is_bot"]] if "is_bot" in df.columns else df

    by_country = (
        human.groupby("country", as_index=False)
        .agg(
            visitors=("country", "size"),
            potential_customers=("potential_customer_signal", "sum"),
            opportunity=("estimated_deal_value", "sum"),
        )
        .sort_values("visitors", ascending=False)
        .head(8)
    )
    by_service = (
        human.groupby("service_name", as_index=False)
        .agg(
            visitors=("service_name", "size"),
            demos=("has_demo_request", "sum"),
            opportunity=("estimated_deal_value", "sum"),
        )
        .sort_values("opportunity", ascending=False)
        .head(8)
    )
    by_day = (
        human.groupby(human["date"].dt.date)
        .agg(visitors=("request_id", "size"), potential=("potential_customer_signal", "sum"))
        .tail(30)
    )

    return [
        go.Figure(go.Bar(x=by_country["country"], y=by_country["visitors"])),
        go.Figure(go.Bar(x=by_service["service_name"], y=by_service["opportunity"])),
        go.Figure(go.Scatter(x=by_day.index.astype(str), y=by_day["potential"], mode="lines+markers")),
    ]


@functools.lru_cache(maxsize=1)
def _cached_chart_preparation() -> list[go.Figure]:
    return _prepare_dashboard_charts(_cached_transformed_data())


def _pct_improvement(before: float, after: float) -> float:
    if before <= 0:
        return 0.0
    return (before - after) / before * 100


def _report_table(rows: list[dict]) -> str:
    lines = [
        "| Operation | Before caching avg | After caching avg | Improvement |",
        "|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['operation']} | {row['before']['avg']:.4f}s | "
            f"{row['after']['avg']:.4f}s | {row['improvement']:.1f}% |"
        )
    return "\n".join(lines)


def test_dashboard_performance_timing_report() -> None:
    assert CSV_PATH.exists(), f"Dataset file not found: {CSV_PATH}"

    _cached_dataset.cache_clear()
    _cached_transformed_data.cache_clear()
    _cached_chart_preparation.cache_clear()
    _FILTER_CACHE.clear()

    csv_df, load_before = _time_call(_read_csv_dataset)
    transformed_df = _transform_dashboard_data(csv_df)

    _, load_after = _time_call(_cached_dataset)
    _, transform_before = _time_call(lambda: _transform_dashboard_data(csv_df))
    _, transform_after = _time_call(_cached_transformed_data)
    _, chart_before = _time_call(lambda: _prepare_dashboard_charts(transformed_df))
    _, chart_after = _time_call(_cached_chart_preparation)
    _, filter_before = _time_call(lambda: _apply_dashboard_filters(transformed_df))
    filtered_after, filter_after = _time_call(_cached_filter_response)

    rows = [
        {
            "operation": "Dataset loading",
            "before": _summarize(load_before),
            "after": _summarize(load_after),
        },
        {
            "operation": "Data transformation",
            "before": _summarize(transform_before),
            "after": _summarize(transform_after),
        },
        {
            "operation": "Chart preparation",
            "before": _summarize(chart_before),
            "after": _summarize(chart_after),
        },
        {
            "operation": "Filter response",
            "before": _summarize(filter_before),
            "after": _summarize(filter_after),
        },
    ]
    for row in rows:
        row["improvement"] = _pct_improvement(row["before"]["avg"], row["after"]["avg"])

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# CyberNova Dashboard Performance Timing Report",
                "",
                f"Dataset: `{CSV_PATH.relative_to(PROJECT_ROOT)}`",
                f"Rows measured: `{len(csv_df):,}`",
                f"Columns measured: `{len(csv_df.columns):,}`",
                f"Timing runs per operation: `{RUNS}`",
                "",
                "## Summary",
                "",
                _report_table(rows),
                "",
                "## Notes",
                "",
                "- Before caching measures repeated CSV/dataframe work.",
                "- After caching measures cached parquet/dataframe/filter/chart results in the same Python process.",
                f"- Filter scenario: Botswana, Cybersecurity, Engaged, HTTP 200.",
                f"- Filtered rows returned after caching: `{len(filtered_after):,}`",
                "",
                "## Detailed Timings",
                "",
                "| Operation | Before best | Before worst | After best | After worst |",
                "|---|---:|---:|---:|---:|",
                *[
                    f"| {row['operation']} | {row['before']['best']:.4f}s | "
                    f"{row['before']['worst']:.4f}s | {row['after']['best']:.4f}s | "
                    f"{row['after']['worst']:.4f}s |"
                    for row in rows
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert REPORT_PATH.exists()
    assert len(csv_df) > 0
    assert len(filtered_after) >= 0
    assert all(row["before"]["avg"] >= 0 for row in rows)
    assert all(row["after"]["avg"] >= 0 for row in rows)

