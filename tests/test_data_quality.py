"""
Pytest data quality checks for the CyberNova Streamlit BI dashboard dataset.

Run for school report evidence:
    pytest -v -s -p no:cacheprovider tests/test_data_quality.py

The tests intentionally use clear names and assertion messages so pytest output
can be copied into a validation/report appendix.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "output" / "cybernova_enriched_logs.csv"


REQUIRED_COLUMNS = [
    "request_id",
    "timestamp",
    "date",
    "time",
    "hour",
    "ip_address",
    "country",
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
    "segment",
    "is_warm_lead",
    "response_time_ms",
    "bytes_transferred",
    "potential_customer_score",
    "risk_score",
    "data_quality_score",
]

REQUIRED_NON_NULL_COLUMNS = [
    "request_id",
    "timestamp",
    "date",
    "time",
    "hour",
    "ip_address",
    "country",
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
    "segment",
    "is_warm_lead",
]

NUMERIC_COLUMNS = [
    "hour",
    "week_of_year",
    "status_code",
    "response_time_ms",
    "bytes_transferred",
    "duration_seconds",
    "request_count_session",
    "distinct_pages_session",
    "latitude",
    "longitude",
    "potential_customer_score",
    "intent_score",
    "engagement_score",
    "conversion_score",
    "service_value_score",
    "recency_score",
    "risk_score",
    "data_quality_score",
    "estimated_deal_value",
    "pipeline_value",
]

BOOLEAN_COLUMNS = [
    "is_weekend",
    "is_sadc",
    "is_bot",
    "is_warm_lead",
    "converted_to_lead",
    "is_campaign_period",
    "is_anomaly",
    "is_business_hours",
    "is_service_page",
    "is_landing_page",
    "is_conversion_page",
    "is_ai_assistant_page",
    "potential_customer_signal",
    "has_landed",
    "has_service_interest",
    "has_ai_interest",
    "has_contact_interest",
    "has_demo_request",
    "has_event_signup",
    "converted_to_potential_customer",
    "is_engaged_session",
    "is_repeat_visitor",
    "requires_review",
    "invalid_status_flag",
    "duplicate_session_flag",
]

ALLOWED_COUNTRIES = {
    "Botswana",
    "South Africa",
    "Zambia",
    "Namibia",
    "Zimbabwe",
    "Lesotho",
    "Eswatini",
    "Mozambique",
    "Malawi",
    "Tanzania",
}

ALLOWED_SEGMENTS = {"High-intent", "Product-curious", "General browser", "Bot"}
ALLOWED_STATUS_CODES = {200, 304, 404, 500}
ALLOWED_STATUS_CLASSES = {"2xx", "3xx", "4xx", "5xx"}
ALLOWED_METHODS = {"GET", "POST", "HEAD"}
ALLOWED_RISK_LEVELS = {"Low", "Medium", "High", "Critical"}
ALLOWED_MARKET_STATUS = {"Above Target", "On Watch", "Below Target", "Below expansion target"}
ALLOWED_INVESTMENT_RECOMMENDATIONS = {"Invest", "Monitor", "Review", "Hold"}
ALLOWED_DATA_FRESHNESS = {"Current", "Stale", "Needs Refresh"}

EXPECTED_SERVICE_CATEGORY_BY_SERVICE = {
    "AI Cyber Assistant": "AI Advisory",
    "Automated Risk Assessment": "Cybersecurity",
    "Bot or Invalid Request": "Bot/Security",
    "Contact": "Lead Conversion",
    "Cybersecurity Monitoring": "Cybersecurity",
    "Digital Transformation": "Digital Transformation",
    "Event Signup": "Lead Conversion",
    "Events and Promotions": "Marketing",
    "General Website": "General",
    "Predictive Maintenance": "Infrastructure",
    "Rapid Prototyping": "Prototyping",
    "Schedule Demo": "Lead Conversion",
    "Static Asset": "Static Asset",
    "Unknown": "Unknown",
}


@pytest.fixture(scope="session")
def dataset() -> pd.DataFrame:
    assert DATASET_PATH.exists(), (
        f"FAIL: Dataset file was not found at {DATASET_PATH}. "
        "Run python generate_logs.py before running data quality tests."
    )

    df = pd.read_csv(DATASET_PATH, low_memory=False)

    print("\nCYBERNOVA DATA QUALITY TEST SUMMARY")
    print(f"Dataset path: {DATASET_PATH}")
    print(f"Rows loaded: {len(df):,}")
    print(f"Columns loaded: {len(df.columns):,}")
    if "date" in df.columns:
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    if "country" in df.columns:
        print(f"Markets: {df['country'].nunique(dropna=True)}")
    if "service_name" in df.columns:
        print(f"Services: {df['service_name'].nunique(dropna=True)}")
    print(
        "Use pytest -v -s -p no:cacheprovider tests/test_data_quality.py "
        "for report-friendly output.\n"
    )

    return df


def _missing_counts(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    return df[columns].isna().sum().loc[lambda s: s > 0]


def _unexpected_values(series: pd.Series, allowed: set) -> set:
    return set(series.dropna().unique()) - allowed


def _as_bool_strings(series: pd.Series) -> pd.Series:
    return series.dropna().astype(str).str.strip().str.lower()


def test_dataset_file_loads_and_has_records(dataset: pd.DataFrame) -> None:
    assert not dataset.empty, "FAIL: Dataset loaded, but it contains zero rows."
    assert len(dataset) >= 1_000, (
        f"FAIL: Dataset has {len(dataset):,} rows; SRS requires at least 1,000 rows."
    )


def test_required_columns_are_present(dataset: pd.DataFrame) -> None:
    missing = sorted(set(REQUIRED_COLUMNS) - set(dataset.columns))
    assert not missing, f"FAIL: Required dataset columns are missing: {missing}"


def test_required_values_are_not_missing(dataset: pd.DataFrame) -> None:
    missing = _missing_counts(dataset, REQUIRED_NON_NULL_COLUMNS)
    assert missing.empty, (
        "FAIL: Required fields contain missing values. "
        f"Missing counts by column: {missing.to_dict()}"
    )


def test_request_ids_are_unique_and_no_full_duplicate_rows(dataset: pd.DataFrame) -> None:
    duplicate_request_ids = int(dataset["request_id"].duplicated().sum())
    duplicate_rows = int(dataset.duplicated().sum())

    assert duplicate_request_ids == 0, (
        f"FAIL: Found {duplicate_request_ids:,} duplicate request_id values. "
        "Each log request must have a unique request_id."
    )
    assert duplicate_rows == 0, (
        f"FAIL: Found {duplicate_rows:,} fully duplicated records in the dataset."
    )


def test_timestamp_and_date_columns_are_valid_dates(dataset: pd.DataFrame) -> None:
    timestamp = pd.to_datetime(dataset["timestamp"], errors="coerce")
    date = pd.to_datetime(dataset["date"], errors="coerce")

    bad_timestamps = int(timestamp.isna().sum())
    bad_dates = int(date.isna().sum())

    assert bad_timestamps == 0, (
        f"FAIL: Found {bad_timestamps:,} timestamp values that cannot be parsed as dates."
    )
    assert bad_dates == 0, (
        f"FAIL: Found {bad_dates:,} date values that cannot be parsed as dates."
    )
    assert timestamp.min() <= timestamp.max(), "FAIL: Timestamp range is invalid."


def test_numeric_columns_have_correct_data_types(dataset: pd.DataFrame) -> None:
    conversion_failures: dict[str, int] = {}

    for column in NUMERIC_COLUMNS:
        if column not in dataset.columns:
            continue
        converted = pd.to_numeric(dataset[column], errors="coerce")
        invalid_count = int(converted.isna().sum() - dataset[column].isna().sum())
        if invalid_count > 0:
            conversion_failures[column] = invalid_count

    assert not conversion_failures, (
        "FAIL: Some numeric columns contain non-numeric values. "
        f"Invalid counts by column: {conversion_failures}"
    )


def test_boolean_columns_are_consistent_true_false_values(dataset: pd.DataFrame) -> None:
    allowed_bool_values = {"true", "false", "1", "0", "yes", "no"}
    invalid_values: dict[str, list[str]] = {}

    for column in BOOLEAN_COLUMNS:
        if column not in dataset.columns:
            continue
        values = set(_as_bool_strings(dataset[column]).unique())
        unexpected = sorted(values - allowed_bool_values)
        if unexpected:
            invalid_values[column] = unexpected

    assert not invalid_values, (
        "FAIL: Boolean columns contain values outside true/false style values. "
        f"Unexpected values: {invalid_values}"
    )


@pytest.mark.parametrize(
    ("column", "minimum", "maximum"),
    [
        ("hour", 0, 23),
        ("week_of_year", 1, 53),
        ("response_time_ms", 1, 10_000),
        ("bytes_transferred", 0, 1_000_000),
        ("duration_seconds", 0, 86_400),
        ("request_count_session", 1, 500),
        ("distinct_pages_session", 1, 100),
        ("latitude", -35, -5),
        ("longitude", 15, 42),
        ("potential_customer_score", 0, 100),
        ("intent_score", 0, 100),
        ("engagement_score", 0, 100),
        ("conversion_score", 0, 100),
        ("service_value_score", 0, 100),
        ("recency_score", 0, 100),
        ("risk_score", 0, 100),
        ("data_quality_score", 0, 100),
        ("estimated_deal_value", 0, 1_000_000),
        ("pipeline_value", 0, 1_000_000),
    ],
)
def test_numeric_ranges_are_valid(
    dataset: pd.DataFrame, column: str, minimum: float, maximum: float
) -> None:
    if column not in dataset.columns:
        pytest.skip(f"{column} is not present in this dataset version.")

    values = pd.to_numeric(dataset[column], errors="coerce")
    invalid = dataset.loc[~values.between(minimum, maximum, inclusive="both"), column]

    assert invalid.empty, (
        f"FAIL: Column '{column}' has {len(invalid):,} values outside "
        f"the expected range [{minimum}, {maximum}]. "
        f"Sample invalid values: {invalid.head(10).tolist()}"
    )


def test_status_code_and_status_class_are_consistent(dataset: pd.DataFrame) -> None:
    status_code = pd.to_numeric(dataset["status_code"], errors="coerce")
    unexpected_codes = set(status_code.dropna().astype(int).unique()) - ALLOWED_STATUS_CODES
    unexpected_classes = _unexpected_values(dataset["status_class"], ALLOWED_STATUS_CLASSES)

    expected_class = (status_code // 100).astype("Int64").astype(str) + "xx"
    mismatches = dataset.loc[dataset["status_class"].astype(str) != expected_class, [
        "request_id",
        "status_code",
        "status_class",
    ]]

    assert not unexpected_codes, f"FAIL: Unexpected HTTP status codes found: {unexpected_codes}"
    assert not unexpected_classes, (
        f"FAIL: Unexpected HTTP status classes found: {unexpected_classes}"
    )
    assert mismatches.empty, (
        "FAIL: status_class does not match status_code for some records. "
        f"Sample mismatches: {mismatches.head(10).to_dict(orient='records')}"
    )


def test_core_category_values_are_valid(dataset: pd.DataFrame) -> None:
    category_checks = {
        "country": ALLOWED_COUNTRIES,
        "method": ALLOWED_METHODS,
        "segment": ALLOWED_SEGMENTS,
        "risk_level": ALLOWED_RISK_LEVELS,
        "market_status": ALLOWED_MARKET_STATUS,
        "investment_recommendation": ALLOWED_INVESTMENT_RECOMMENDATIONS,
        "data_freshness_status": ALLOWED_DATA_FRESHNESS,
    }
    unexpected_by_column: dict[str, set] = {}

    for column, allowed in category_checks.items():
        if column not in dataset.columns:
            continue
        unexpected = _unexpected_values(dataset[column], allowed)
        if unexpected:
            unexpected_by_column[column] = unexpected

    assert not unexpected_by_column, (
        "FAIL: Category consistency check found unexpected values. "
        f"Unexpected values by column: {unexpected_by_column}"
    )


def test_service_names_match_expected_service_categories(dataset: pd.DataFrame) -> None:
    service_pairs = dataset[["service_name", "service_category"]].drop_duplicates()
    invalid_pairs = service_pairs[
        service_pairs.apply(
            lambda row: EXPECTED_SERVICE_CATEGORY_BY_SERVICE.get(row["service_name"])
            != row["service_category"],
            axis=1,
        )
    ]

    assert invalid_pairs.empty, (
        "FAIL: Some service_name values are mapped to unexpected service_category values. "
        f"Invalid mappings: {invalid_pairs.to_dict(orient='records')}"
    )


def test_segment_and_bot_flag_are_consistent(dataset: pd.DataFrame) -> None:
    is_bot = _as_bool_strings(dataset["is_bot"]).eq("true")
    bot_segment_mismatches = dataset.loc[is_bot & dataset["segment"].ne("Bot"), [
        "request_id",
        "is_bot",
        "segment",
    ]]
    human_segment_mismatches = dataset.loc[~is_bot & dataset["segment"].eq("Bot"), [
        "request_id",
        "is_bot",
        "segment",
    ]]

    assert bot_segment_mismatches.empty, (
        "FAIL: Some bot records are not assigned to the Bot segment. "
        f"Sample: {bot_segment_mismatches.head(10).to_dict(orient='records')}"
    )
    assert human_segment_mismatches.empty, (
        "FAIL: Some non-bot records are assigned to the Bot segment. "
        f"Sample: {human_segment_mismatches.head(10).to_dict(orient='records')}"
    )


def test_lead_flags_match_conversion_uris(dataset: pd.DataFrame) -> None:
    demo_rows = dataset["uri"].astype(str).eq("/scheduledemo.php")
    event_signup_rows = dataset["uri"].astype(str).eq("/event.php")

    demo_flag = _as_bool_strings(dataset["has_demo_request"]).eq("true")
    event_flag = _as_bool_strings(dataset["has_event_signup"]).eq("true")

    missed_demo_flags = int((demo_rows & ~demo_flag).sum())
    missed_event_signup_flags = int((event_signup_rows & ~event_flag).sum())

    assert missed_demo_flags == 0, (
        f"FAIL: Found {missed_demo_flags:,} /scheduledemo.php rows without has_demo_request=True."
    )
    assert missed_event_signup_flags == 0, (
        f"FAIL: Found {missed_event_signup_flags:,} /event.php rows without "
        "has_event_signup=True."
    )


def test_srs_distribution_rules_are_satisfied(dataset: pd.DataFrame) -> None:
    bots = _as_bool_strings(dataset["is_bot"]).eq("true")
    bot_ratio = bots.mean()
    botswana_share = dataset["country"].eq("Botswana").mean()

    assert botswana_share >= 0.30, (
        f"FAIL: Botswana traffic share is {botswana_share:.2%}; SRS requires at least 30%."
    )
    assert 0.08 <= bot_ratio <= 0.12, (
        f"FAIL: Bot traffic ratio is {bot_ratio:.2%}; expected range is 8% to 12%."
    )
