"""
Streamlit AppTest coverage for the CyberNova dashboard.

These tests exercise the app through Streamlit's testing API:
- unauthenticated app startup
- authenticated dashboard startup
- drawer widgets and global filters
- KPI card rendering
- filter changes and empty-result safety
"""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "cybernovaapp.py"
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from streamlit.testing.v1 import AppTest


def _new_app(timeout: int = 90) -> AppTest:
    return AppTest.from_file(str(APP_PATH), default_timeout=timeout)


def _authenticate(at: AppTest, *, drawer_open: bool = False, **state) -> AppTest:
    at.session_state["authenticated"] = True
    at.session_state["current_role"] = state.pop("current_role", "Admin / Lecturer View")
    at.session_state["active_dashboard"] = state.pop("active_dashboard", "Sales")
    at.session_state["active_tab"] = state.pop("active_tab", "Overview")
    at.session_state["admin_drawer_open"] = drawer_open
    for key, value in state.items():
        at.session_state[key] = value
    return at


def _assert_no_exceptions(at: AppTest) -> None:
    messages = [str(exception.value) for exception in at.exception]
    assert not messages, "Streamlit app raised exceptions:\n" + "\n".join(messages)


def _selectbox_by_key(at: AppTest, key: str):
    for selectbox in at.selectbox:
        if selectbox.key == key:
            return selectbox
    raise AssertionError(f"Selectbox with key {key!r} was not found.")


def _markdown_contains(at: AppTest, needle: str) -> bool:
    return any(needle in getattr(markdown, "value", "") for markdown in at.markdown)


def test_app_loads_without_exceptions_and_shows_login_widgets() -> None:
    at = _new_app().run()

    _assert_no_exceptions(at)
    assert len(at.selectbox) >= 1
    assert at.selectbox[0].label == "Role"
    assert "Admin / Lecturer View" in at.selectbox[0].options
    assert len(at.text_input) >= 1
    assert at.text_input[0].label == "Password"
    assert any(button.label == "Log in" for button in at.button)


def test_authenticated_dashboard_key_widgets_are_present() -> None:
    at = _authenticate(_new_app(), drawer_open=True).run()

    _assert_no_exceptions(at)
    assert any(button.key == "admin_drawer_toggle" for button in at.button)
    assert any(button.key == "header_logout" for button in at.button)
    assert {date_input.label for date_input in at.date_input} >= {"Start Date", "End Date"}
    assert {selectbox.key for selectbox in at.selectbox} >= {
        "rp_mkt",
        "rp_svc",
        "rp_seg",
        "rp_out",
        "rp_status",
    }
    assert len(at.radio) == 1
    assert at.radio[0].label == "Dashboard section"
    assert list(at.radio[0].options) == ["Overview", "Analytics", "Forecasting", "Data & Export"]


def test_sales_kpi_elements_render_on_overview() -> None:
    at = _authenticate(_new_app(), drawer_open=False).run()

    _assert_no_exceptions(at)
    assert _markdown_contains(at, "kpi-card")
    for label in [
        "People Waiting for a Demo",
        "Potential Customers Today",
        "Sales Progress This Month",
        "Estimated Revenue if Leads Convert",
        "Hottest Market Right Now",
    ]:
        assert _markdown_contains(at, label), f"Expected KPI label did not render: {label}"


def test_global_filters_can_be_changed_without_crashing() -> None:
    at = _authenticate(_new_app(), drawer_open=True).run()
    _assert_no_exceptions(at)

    _selectbox_by_key(at, "rp_mkt").set_value("Botswana")
    _selectbox_by_key(at, "rp_svc").set_value("Cybersecurity")
    _selectbox_by_key(at, "rp_out").set_value("Engaged")
    _selectbox_by_key(at, "rp_status").set_value("200")
    at.run()

    _assert_no_exceptions(at)
    assert at.session_state["selected_market"] == "Botswana"
    assert at.session_state["svc_filter"] == "Cybersecurity"
    assert at.session_state["outcome_filter"] == "Engaged"
    assert at.session_state["status_filter"] == "200"
    assert _markdown_contains(at, "Market: Botswana")
    assert _markdown_contains(at, "Service: Cybersecurity")
    assert _markdown_contains(at, "Outcome: Engaged")
    assert _markdown_contains(at, "Status: 200")


def test_empty_filter_results_do_not_crash_dashboard() -> None:
    at = _authenticate(
        _new_app(),
        drawer_open=False,
        status_filter="999",
        selected_market="All",
        svc_filter="All Services",
        seg_filter="All Segments",
        outcome_filter="All",
    ).run()

    _assert_no_exceptions(at)
    assert _markdown_contains(at, "kpi-card")
    assert _markdown_contains(at, "People Waiting for a Demo")
    assert _markdown_contains(at, "Status: 999")
