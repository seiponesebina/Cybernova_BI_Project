"""
Playwright screenshot test for the locally running CyberNova Streamlit dashboard.

Run the dashboard first, for example:
    streamlit run cybernovaapp.py

Then run:
    pytest -q -p no:cacheprovider tests/test_playwright_dashboard.py

Optional:
    set STREAMLIT_APP_URL=http://localhost:8505

Screenshots are saved under reports/playwright_screenshots/.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - depends on local optional install
    sync_playwright = None
    PlaywrightError = Exception
    PlaywrightTimeoutError = Exception


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = PROJECT_ROOT / "reports" / "playwright_screenshots"
DEFAULT_URLS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:8505",
    "http://127.0.0.1:8505",
]
KEY_HEADINGS = [
    "CyberNova Pulse",
    "People Waiting for a Demo",
    "Potential Customers Today",
    "Sales Progress This Month",
    "Estimated Revenue if Leads Convert",
    "Hottest Market Right Now",
]


def _url_is_reachable(url: str) -> bool:
    try:
        request = Request(url, headers={"User-Agent": "pytest-playwright"})
        with urlopen(request, timeout=2) as response:
            return 200 <= response.status < 500
    except (OSError, URLError):
        return False


def _dashboard_url() -> str:
    configured = os.environ.get("STREAMLIT_APP_URL")
    candidates = [configured] if configured else DEFAULT_URLS

    for url in candidates:
        if url and _url_is_reachable(url):
            return url.rstrip("/")

    pytest.skip(
        "No locally running Streamlit dashboard found. Start it with "
        "`streamlit run cybernovaapp.py` or set STREAMLIT_APP_URL."
    )


def test_local_streamlit_dashboard_loads_and_screenshots_all_browsers() -> None:
    if sync_playwright is None:
        pytest.skip("Playwright is not installed. Run `pip install -r requirements.txt`.")

    dashboard_url = _dashboard_url()
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        playwright_context = sync_playwright()
        playwright = playwright_context.__enter__()
    except (PlaywrightError, OSError, PermissionError) as exc:
        pytest.skip(f"Playwright could not start in this local environment: {exc}")

    try:
        browsers = {
            "chromium": playwright.chromium,
            "firefox": playwright.firefox,
            "webkit": playwright.webkit,
        }

        for browser_name, browser_type in browsers.items():
            try:
                browser = browser_type.launch(headless=True)
            except PlaywrightError as exc:
                pytest.skip(
                    f"{browser_name} browser binaries are not installed. "
                    "Run `python -m playwright install`."
                    f" Details: {exc}"
                )

            page = browser.new_page(viewport={"width": 1440, "height": 1100})
            authenticated_url = f"{dashboard_url}/?role={quote('Admin / Lecturer View')}"
            try:
                page.goto(authenticated_url, wait_until="networkidle", timeout=60_000)
            except PlaywrightTimeoutError:
                page.goto(authenticated_url, wait_until="domcontentloaded", timeout=60_000)

            assert "CyberNova" in page.title()

            for heading in KEY_HEADINGS:
                page.get_by_text(heading, exact=False).first.wait_for(
                    state="visible",
                    timeout=30_000,
                )

            screenshot_path = SCREENSHOT_DIR / f"cybernova_dashboard_{browser_name}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            assert screenshot_path.exists()
            assert screenshot_path.stat().st_size > 0

            browser.close()
    finally:
        playwright_context.__exit__(None, None, None)
