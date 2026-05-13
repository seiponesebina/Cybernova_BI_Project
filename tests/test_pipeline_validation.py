"""
Pipeline validation tests for the CyberNova BI dashboard datasets.

These tests validate the data chain from the raw IIS-style log export to the
enriched BI dataset and grouped dashboard/report outputs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import exports
from generate_logs import PAGE_TYPE_MAP, URI_TO_BUSINESS, status_class


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "output" / "cybernova_iis_raw_logs.csv"
ENRICHED_PATH = PROJECT_ROOT / "data" / "output" / "cybernova_enriched_logs.csv"
SUMMARY_PATH = PROJECT_ROOT / "data" / "output" / "generation_summary.csv"

RAW_REQUIRED_COLUMNS = [
    "date",
    "time",
    "ip_address",
    "method",
    "uri",
    "status_code",
    "user_agent",
    "bytes_transferred",
    "response_time_ms",
]

ENRICHED_REQUIRED_COLUMNS = [
    "request_id",
    "timestamp",
    "date",
    "time",
    "hour",
    "day_of_week",
    "month_name",
    "week_of_year",
    "is_weekend",
    "ip_address",
    "country",
    "is_sadc",
    "method",
    "uri",
    "service_name",
    "service_category",
    "request_type",
    "status_code",
    "status_class",
    "user_agent",
    "is_bot",
    "session_id",
    "first_request_ts",
    "last_request_ts",
    "duration_seconds",
    "request_count_session",
    "distinct_pages_session",
    "entry_page",
    "exit_page",
    "segment",
    "is_warm_lead",
    "converted_to_lead",
    "is_business_hours",
    "business_service_name",
    "business_page_type",
    "is_service_page",
    "is_landing_page",
    "is_conversion_page",
    "is_ai_assistant_page",
    "potential_customer_signal",
    "potential_customer_score",
    "has_landed",
    "has_service_interest",
    "has_ai_interest",
    "has_contact_interest",
    "has_demo_request",
    "has_event_signup",
    "converted_to_potential_customer",
    "is_engaged_session",
    "risk_score",
    "risk_level",
    "requires_review",
    "data_quality_flag",
    "data_quality_score",
    "missing_required_fields",
    "invalid_status_flag",
    "duplicate_session_flag",
    "estimated_deal_value",
    "estimated_monthly_value",
    "expected_conversion_value",
    "pipeline_value",
]


@pytest.fixture(scope="session")
def raw_df() -> pd.DataFrame:
    assert RAW_PATH.exists(), f"Raw dataset not found at {RAW_PATH}"
    return pd.read_csv(RAW_PATH, low_memory=False)


@pytest.fixture(scope="session")
def enriched_df() -> pd.DataFrame:
    assert ENRICHED_PATH.exists(), f"Enriched dataset not found at {ENRICHED_PATH}"
    return pd.read_csv(ENRICHED_PATH, low_memory=False)


@pytest.fixture(scope="session")
def summary_df() -> pd.DataFrame:
    assert SUMMARY_PATH.exists(), f"Generation summary not found at {SUMMARY_PATH}"
    return pd.read_csv(SUMMARY_PATH, low_memory=False)


def _truthy(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin({"1", "true", "yes", "y"})


def _status_class_series(status_codes: pd.Series) -> pd.Series:
    return pd.to_numeric(status_codes, errors="coerce").astype(int).map(status_class)


def test_raw_dataset_loads_correctly(raw_df: pd.DataFrame) -> None:
    assert not raw_df.empty, "Raw IIS dataset loaded but contains no rows."
    assert raw_df.columns.tolist() == RAW_REQUIRED_COLUMNS
    assert not raw_df[RAW_REQUIRED_COLUMNS].isna().any().any()
    assert pd.to_datetime(raw_df["date"] + " " + raw_df["time"], errors="coerce").notna().all()
    assert pd.to_numeric(raw_df["status_code"], errors="coerce").notna().all()
    assert pd.to_numeric(raw_df["bytes_transferred"], errors="coerce").ge(0).all()
    assert pd.to_numeric(raw_df["response_time_ms"], errors="coerce").gt(0).all()


def test_required_pipeline_columns_exist(
    raw_df: pd.DataFrame, enriched_df: pd.DataFrame, summary_df: pd.DataFrame
) -> None:
    missing_raw = sorted(set(RAW_REQUIRED_COLUMNS) - set(raw_df.columns))
    missing_enriched = sorted(set(ENRICHED_REQUIRED_COLUMNS) - set(enriched_df.columns))
    missing_summary = sorted({"date", "actual_requests"} - set(summary_df.columns))

    assert not missing_raw, f"Raw dataset is missing columns: {missing_raw}"
    assert not missing_enriched, f"Enriched dataset is missing columns: {missing_enriched}"
    assert not missing_summary, f"Generation summary is missing columns: {missing_summary}"


def test_row_counts_are_reconciled_before_and_after_cleaning(
    raw_df: pd.DataFrame, enriched_df: pd.DataFrame, summary_df: pd.DataFrame
) -> None:
    assert len(raw_df) == len(enriched_df), (
        f"Raw/enriched row count mismatch: raw={len(raw_df):,}, enriched={len(enriched_df):,}"
    )
    assert len(enriched_df) == int(summary_df["actual_requests"].sum())
    assert enriched_df["request_id"].is_unique
    assert int(enriched_df["request_id"].min()) == 1
    assert int(enriched_df["request_id"].max()) == len(enriched_df)

    raw_projection = raw_df[RAW_REQUIRED_COLUMNS].reset_index(drop=True).copy()
    enriched_projection = enriched_df[RAW_REQUIRED_COLUMNS].reset_index(drop=True).copy()
    for col in ["status_code", "bytes_transferred", "response_time_ms"]:
        raw_projection[col] = pd.to_numeric(raw_projection[col], errors="coerce").astype("int64")
        enriched_projection[col] = pd.to_numeric(enriched_projection[col], errors="coerce").astype("int64")

    pd.testing.assert_frame_equal(raw_projection, enriched_projection, check_dtype=False)


def test_time_and_status_calculated_columns_are_correct(enriched_df: pd.DataFrame) -> None:
    timestamp = pd.to_datetime(enriched_df["timestamp"], errors="coerce")

    assert timestamp.notna().all()
    assert enriched_df["date"].astype(str).equals(timestamp.dt.date.astype(str))
    assert enriched_df["time"].astype(str).equals(timestamp.dt.strftime("%H:%M:%S"))
    pd.testing.assert_series_equal(
        pd.to_numeric(enriched_df["hour"]),
        timestamp.dt.hour,
        check_names=False,
        check_dtype=False,
    )
    assert enriched_df["day_of_week"].astype(str).equals(timestamp.dt.day_name())
    assert enriched_df["month_name"].astype(str).equals(timestamp.dt.month_name())
    pd.testing.assert_series_equal(
        pd.to_numeric(enriched_df["week_of_year"]),
        timestamp.dt.isocalendar().week.astype(int),
        check_names=False,
        check_dtype=False,
    )
    assert _truthy(enriched_df["is_weekend"]).equals(timestamp.dt.weekday >= 5)
    assert enriched_df["status_class"].astype(str).equals(_status_class_series(enriched_df["status_code"]))
    assert _truthy(enriched_df["is_business_hours"]).equals(
        timestamp.dt.hour.between(8, 17) & (timestamp.dt.weekday < 5)
    )


def test_session_level_calculated_columns_are_correct(enriched_df: pd.DataFrame) -> None:
    work = enriched_df.copy()
    work["_timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")
    session = work.groupby("session_id", sort=False).agg(
        first_request_ts=("_timestamp", "min"),
        last_request_ts=("_timestamp", "max"),
        request_count_session=("uri", "count"),
        distinct_pages_session=("uri", "nunique"),
        entry_page=("uri", "first"),
        exit_page=("uri", "last"),
        converted_to_lead=("uri", lambda x: set(x) & {"/scheduledemo.php", "/event.php", "/contact.php"}),
    )
    expected = work["session_id"].map(session["request_count_session"])
    assert pd.to_numeric(work["request_count_session"]).equals(expected)

    expected = work["session_id"].map(session["distinct_pages_session"])
    assert pd.to_numeric(work["distinct_pages_session"]).equals(expected)

    assert work["entry_page"].astype(str).equals(work["session_id"].map(session["entry_page"]).astype(str))
    assert work["exit_page"].astype(str).equals(work["session_id"].map(session["exit_page"]).astype(str))
    assert pd.to_datetime(work["first_request_ts"]).equals(work["session_id"].map(session["first_request_ts"]))
    assert pd.to_datetime(work["last_request_ts"]).equals(work["session_id"].map(session["last_request_ts"]))

    duration = (session["last_request_ts"] - session["first_request_ts"]).dt.total_seconds().astype(int)
    assert pd.to_numeric(work["duration_seconds"]).equals(work["session_id"].map(duration))

    expected_lead = work["session_id"].map(session["converted_to_lead"]).astype(bool)
    assert _truthy(work["converted_to_lead"]).equals(expected_lead)
    assert _truthy(work["is_engaged_session"]).equals(
        (pd.to_numeric(work["distinct_pages_session"]) >= 3)
        | (pd.to_numeric(work["request_count_session"]) >= 4)
    )


def test_business_flag_and_value_calculated_columns_are_correct(enriched_df: pd.DataFrame) -> None:
    business_service = enriched_df["uri"].map(URI_TO_BUSINESS).fillna("Other")
    page_type = business_service.map(PAGE_TYPE_MAP).fillna("Other")
    deal_value = pd.to_numeric(enriched_df["estimated_deal_value"], errors="coerce").fillna(0).astype(int)
    score = pd.to_numeric(enriched_df["potential_customer_score"], errors="coerce").fillna(0)
    signal = pd.to_numeric(enriched_df["potential_customer_signal"], errors="coerce").fillna(0).astype(int)

    assert enriched_df["business_service_name"].astype(str).equals(business_service.astype(str))
    assert enriched_df["business_page_type"].astype(str).equals(page_type.astype(str))
    assert _truthy(enriched_df["is_service_page"]).equals(page_type.eq("Service Page"))
    assert _truthy(enriched_df["is_landing_page"]).equals(page_type.eq("Landing Page"))
    assert _truthy(enriched_df["is_conversion_page"]).equals(page_type.eq("Conversion Page"))
    assert _truthy(enriched_df["is_ai_assistant_page"]).equals(business_service.eq("AI Cyber Assistant"))
    assert _truthy(enriched_df["has_landed"]).all()
    assert _truthy(enriched_df["converted_to_potential_customer"]).equals(signal.eq(1))
    assert pd.to_numeric(enriched_df["estimated_monthly_value"]).equals((deal_value / 12).astype(int))
    assert pd.to_numeric(enriched_df["expected_conversion_value"]).equals((deal_value * score / 100).astype(int))
    assert pd.to_numeric(enriched_df["pipeline_value"]).equals(pd.Series(np.where(signal.eq(1), deal_value, 0)))


def test_risk_and_data_quality_calculated_columns_are_correct(enriched_df: pd.DataFrame) -> None:
    status = pd.to_numeric(enriched_df["status_code"], errors="coerce").fillna(0)
    response_time = pd.to_numeric(enriched_df["response_time_ms"], errors="coerce").fillna(0)
    expected_risk = (
        _truthy(enriched_df["is_anomaly"]).astype(int) * 40
        + _truthy(enriched_df["is_bot"]).astype(int) * 20
        + np.where(status >= 500, 25, np.where(status >= 400, 10, 0))
        + np.where(response_time > 1000, 15, 0)
    ).clip(0, 100).astype(int)
    expected_level = pd.cut(
        expected_risk,
        bins=[-1, 20, 45, 70, 100],
        labels=["Low", "Medium", "High", "Critical"],
    ).astype(str)
    expected_quality_flag = np.where(
        enriched_df["country"].isna() | enriched_df["country"].astype(str).eq(""),
        "Review Needed",
        "Good",
    )
    expected_missing = (
        enriched_df["country"].isna()
        | enriched_df["uri"].isna()
        | enriched_df["session_id"].isna()
    )
    expected_duplicate = enriched_df.duplicated(subset=["session_id", "uri", "timestamp"], keep=False)

    assert pd.to_numeric(enriched_df["risk_score"]).equals(pd.Series(expected_risk, index=enriched_df.index))
    assert enriched_df["risk_level"].astype(str).equals(pd.Series(expected_level, index=enriched_df.index))
    assert _truthy(enriched_df["requires_review"]).equals(enriched_df["risk_level"].isin(["High", "Critical"]))
    assert enriched_df["data_quality_flag"].astype(str).equals(pd.Series(expected_quality_flag, index=enriched_df.index))
    assert pd.to_numeric(enriched_df["data_quality_score"]).equals(
        pd.Series(np.where(expected_quality_flag == "Good", 95, 70), index=enriched_df.index)
    )
    assert _truthy(enriched_df["missing_required_fields"]).equals(expected_missing)
    assert _truthy(enriched_df["invalid_status_flag"]).equals(~enriched_df["status_code"].isin([200, 304, 404, 500]))
    assert _truthy(enriched_df["duplicate_session_flag"]).equals(expected_duplicate)


def test_grouped_country_dashboard_output_matches_source_data(enriched_df: pd.DataFrame) -> None:
    expected = (
        enriched_df.groupby("country", as_index=False)
        .agg(
            visitors=("country", "count"),
            potential_customers=("potential_customer_signal", lambda s: int((s == True).sum())),
            opportunity_value=("estimated_deal_value", "sum"),
        )
        .sort_values("visitors", ascending=False)
        .reset_index(drop=True)
    )
    actual = pd.DataFrame(exports.build_country_summary("Sales", enriched_df)).reset_index(drop=True)

    pd.testing.assert_series_equal(actual["country"], expected["country"], check_names=False)
    pd.testing.assert_series_equal(actual["visitors"], expected["visitors"], check_names=False)
    pd.testing.assert_series_equal(actual["potential_customers"], expected["potential_customers"], check_names=False)
    pd.testing.assert_series_equal(
        pd.to_numeric(actual["opportunity_value"]),
        pd.to_numeric(expected["opportunity_value"]),
        check_names=False,
    )


def test_grouped_daily_dashboard_output_matches_source_data(
    raw_df: pd.DataFrame, enriched_df: pd.DataFrame
) -> None:
    expected = (
        raw_df.groupby("date", as_index=False)
        .size()
        .rename(columns={"size": "actual_requests"})
        .sort_values("date")
        .reset_index(drop=True)
    )
    actual = (
        enriched_df.groupby("date", as_index=False)
        .size()
        .rename(columns={"size": "actual_requests"})
        .sort_values("date")
        .reset_index(drop=True)
    )

    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)
