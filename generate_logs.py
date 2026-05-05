"""
CyberNova Analytics Ltd
Synthetic IIS Web Server Log Generator

This script generates:
1. Raw IIS-style web server logs
2. Enriched BI-ready web logs
3. Excel workbook with all generated sheets
4. Daily generation summary

Run:
    python generate_logs.py
"""

from __future__ import annotations

import hashlib
import os
import random
from datetime import datetime, date, time, timedelta
from typing import Any

import numpy as np
import pandas as pd
import yaml


# ============================================================
# BASIC UTILITIES
# ============================================================

def load_config(path: str = "config.yaml") -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def ensure_output_folder(filepath: str) -> None:
    folder = os.path.dirname(filepath)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)


def weighted_choice(options: dict[str, float]) -> str:
    names = list(options.keys())
    weights = np.array(list(options.values()), dtype=float)
    weights = weights / weights.sum()
    return str(np.random.choice(names, p=weights))


def status_class(status_code: int) -> str:
    if 200 <= status_code < 300:
        return "2xx"
    if 300 <= status_code < 400:
        return "3xx"
    if 400 <= status_code < 500:
        return "4xx"
    if 500 <= status_code < 600:
        return "5xx"
    return "other"


def stable_session_id(ip: str, user_agent: str, start_ts: datetime) -> str:
    raw = f"{ip}|{user_agent}|{start_ts.isoformat()}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ============================================================
# TIME GENERATION
# ============================================================

def random_time_for_human_session(day: date) -> datetime:
    peak = np.random.choice(
        ["morning", "afternoon", "off_peak"],
        p=[0.42, 0.38, 0.20],
    )
    if peak == "morning":
        hour = int(np.clip(np.random.normal(10, 1), 7, 12))
    elif peak == "afternoon":
        hour = int(np.clip(np.random.normal(15, 1), 12, 18))
    else:
        off_peak_hours = [6, 7, 8, 18, 19, 20, 21]
        off_peak_probs = np.array([0.08, 0.12, 0.18, 0.22, 0.18, 0.14, 0.08], dtype=float)
        off_peak_probs = off_peak_probs / off_peak_probs.sum()
        hour = int(np.random.choice(off_peak_hours, p=off_peak_probs))
    minute = int(np.random.randint(0, 60))
    second = int(np.random.randint(0, 60))
    return datetime.combine(day, time(hour, minute, second))


def random_time_for_bot_session(day: date) -> datetime:
    hours = list(range(24))
    probabilities = np.array([
        0.07, 0.07, 0.07, 0.06, 0.05, 0.04,
        0.03, 0.03, 0.03, 0.03, 0.03, 0.03,
        0.03, 0.03, 0.03, 0.03, 0.03, 0.04,
        0.05, 0.06, 0.07, 0.07, 0.06, 0.06,
    ], dtype=float)
    probabilities = probabilities / probabilities.sum()
    hour = int(np.random.choice(hours, p=probabilities))
    minute = int(np.random.randint(0, 60))
    second = int(np.random.randint(0, 60))
    return datetime.combine(day, time(hour, minute, second))


# ============================================================
# CYBERNOVA DOMAIN MODEL
# ============================================================

HUMAN_USER_AGENTS = [
    ("Mozilla/5.0 Chrome Windows", "Desktop", "Chrome"),
    ("Mozilla/5.0 Safari MacOS", "Desktop", "Safari"),
    ("Mozilla/5.0 Firefox Windows", "Desktop", "Firefox"),
    ("Mozilla/5.0 Chrome Android", "Mobile", "Chrome Mobile"),
    ("Mozilla/5.0 Safari iPhone", "Mobile", "Mobile Safari"),
    ("Mozilla/5.0 Edge Windows", "Desktop", "Edge"),
]

BOT_USER_AGENTS = [
    ("Googlebot/2.1", "Bot", "Search Bot"),
    ("Bingbot/2.0", "Bot", "Search Bot"),
    ("curl/8.1.0", "Bot", "Script"),
    ("python-requests/2.31", "Bot", "Script"),
    ("CyberProbeScanner/1.0", "Bot", "Suspicious Scanner"),
    ("AhrefsBot/7.0", "Bot", "SEO Bot"),
]

STATIC_ASSETS = [
    "/images/logo.png",
    "/images/events.jpg",
    "/images/cyber-assistant-banner.png",
    "/css/site.css",
    "/js/main.js",
    "/favicon.ico",
]

GENERAL_PAGES = [
    "/index.html",
    "/pricing.php",
    "/case-studies.php",
    "/resources.php",
    "/contact.php",
]

SADC_COUNTRIES = {
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

# ============================================================
# BI ENRICHMENT CONSTANTS
# ============================================================

URI_TO_BUSINESS = {
    "/index.html": "Homepage",
    "/ai-assistant.php": "AI Cyber Assistant",
    "/scheduledemo.php": "Demo Requests",
    "/contact.php": "Contact Requests",
    "/event.php": "Promotional Events",
    "/events.php": "Events and Promotions",
    "/prototype.php": "AI Prototype Interest",
    "/risk-assessment.php": "Automated Risk Assessment",
    "/predictive-maintenance.php": "Predictive Maintenance",
    "/digital-transformation.php": "Digital Transformation",
    "/cybersecurity-monitoring.php": "Cybersecurity Monitoring",
    "/rapid-prototyping.php": "Rapid Prototyping",
    "/pricing.php": "Pricing",
    "/case-studies.php": "Case Studies",
    "/resources.php": "Resources",
    "/robots.txt": "Bot Probe",
    "/wp-admin.php": "Invalid Admin Probe",
    "/admin.php": "Invalid Admin Probe",
    "/login.php": "Invalid Admin Probe",
}

PAGE_TYPE_MAP = {
    "Homepage": "Landing Page",
    "AI Cyber Assistant": "Service Page",
    "Automated Risk Assessment": "Service Page",
    "Predictive Maintenance": "Service Page",
    "Digital Transformation": "Service Page",
    "Rapid Prototyping": "Service Page",
    "AI Prototype Interest": "Service Page",
    "Cybersecurity Monitoring": "Service Page",
    "Events and Promotions": "Service Page",
    "Demo Requests": "Conversion Page",
    "Contact Requests": "Conversion Page",
    "Promotional Events": "Conversion Page",
    "Pricing": "Supporting Page",
    "Case Studies": "Supporting Page",
    "Resources": "Supporting Page",
    "Bot Probe": "Bot/Security",
    "Invalid Admin Probe": "Bot/Security",
}

SERVICE_GROUP_MAP = {
    "AI Cyber Assistant": "AI & Advisory",
    "Cybersecurity Monitoring": "Cybersecurity",
    "Automated Risk Assessment": "Cybersecurity",
    "Predictive Maintenance": "Infrastructure",
    "Digital Transformation": "Digital Transformation",
    "Rapid Prototyping": "Prototyping",
    "AI Prototype Interest": "Prototyping",
    "Events and Promotions": "Marketing",
    "Demo Requests": "Sales Conversion",
    "Contact Requests": "Sales Conversion",
    "Promotional Events": "Sales Conversion",
    "Homepage": "General",
    "Pricing": "General",
    "Case Studies": "General",
    "Resources": "General",
}

COUNTRY_CITIES = {
    "Botswana": [("Gaborone", -24.6282, 25.9231)],
    "South Africa": [
        ("Johannesburg", -26.2041, 28.0473),
        ("Cape Town", -33.9249, 18.4241),
        ("Durban", -29.8587, 31.0218),
    ],
    "Zambia": [("Lusaka", -15.3875, 28.3228)],
    "Zimbabwe": [("Harare", -17.8252, 31.0335)],
    "Namibia": [("Windhoek", -22.5609, 17.0658)],
    "Mozambique": [("Maputo", -25.9692, 32.5732)],
    "Malawi": [("Lilongwe", -13.9626, 33.7741)],
    "Tanzania": [("Dar es Salaam", -6.7924, 39.2083)],
    "Lesotho": [("Maseru", -29.3158, 27.4869)],
    "Eswatini": [("Mbabane", -26.3054, 31.1367)],
}

SERVICE_VALUE_RANGES = {
    "AI Cyber Assistant": (40_000, 120_000),
    "Cybersecurity Monitoring": (50_000, 150_000),
    "Automated Risk Assessment": (35_000, 100_000),
    "Predictive Maintenance": (45_000, 130_000),
    "Digital Transformation": (80_000, 250_000),
    "Rapid Prototyping": (20_000, 70_000),
    "AI Prototype Interest": (20_000, 70_000),
    "Demo Requests": (40_000, 140_000),
    "Contact Requests": (30_000, 90_000),
    "Promotional Events": (15_000, 60_000),
    "Events and Promotions": (15_000, 60_000),
    "Homepage": (5_000, 25_000),
    "default": (5_000, 25_000),
}

SALES_OWNERS = ["Alex M.", "Adele Johnson", "Mark Smith", "Sarah Jacobs", "Tom Nhamo"]

SOURCE_CHANNELS = [
    "Organic Search", "Paid Search", "Paid Social",
    "Email Campaign", "Referral", "Direct", "Event Campaign", "Partner Referral",
]

CAMPAIGN_OBJECTIVES = {
    "SME Cyber Risk Week": "Lead Generation",
    "AI Cyber Assistant Launch Push": "AI Assistant Promotion",
    "Government Digital Transformation Expo": "Regional Expansion",
    "None": "Awareness",
}

MARKET_CONFIG = {
    "Botswana":      {"node_type": "Core Market",    "priority": "Invest",  "target_traffic": 0.32, "target_pc": 0.30, "maturity": "Mature"},
    "South Africa":  {"node_type": "Core Market",    "priority": "Invest",  "target_traffic": 0.20, "target_pc": 0.18, "maturity": "Mature"},
    "Zambia":        {"node_type": "Strategic Hub",  "priority": "Monitor", "target_traffic": 0.12, "target_pc": 0.12, "maturity": "Growing"},
    "Namibia":       {"node_type": "Emerging",       "priority": "Monitor", "target_traffic": 0.09, "target_pc": 0.08, "maturity": "Developing"},
    "Zimbabwe":      {"node_type": "High Growth",    "priority": "Monitor", "target_traffic": 0.08, "target_pc": 0.10, "maturity": "Growing"},
    "Mozambique":    {"node_type": "Emerging",       "priority": "Review",  "target_traffic": 0.04, "target_pc": 0.05, "maturity": "Early"},
    "Malawi":        {"node_type": "Emerging",       "priority": "Review",  "target_traffic": 0.04, "target_pc": 0.05, "maturity": "Early"},
    "Tanzania":      {"node_type": "Emerging",       "priority": "Review",  "target_traffic": 0.03, "target_pc": 0.04, "maturity": "Early"},
    "Lesotho":       {"node_type": "Stable",         "priority": "Review",  "target_traffic": 0.04, "target_pc": 0.04, "maturity": "Stable"},
    "Eswatini":      {"node_type": "Stable",         "priority": "Review",  "target_traffic": 0.04, "target_pc": 0.04, "maturity": "Stable"},
}


def classify_sadc(country: str) -> bool:
    return country in SADC_COUNTRIES


def generate_ip_for_country(country: str) -> str:
    country_prefixes = {
        "Botswana": "102.128",
        "South Africa": "105.245",
        "Zambia": "154.120",
        "Namibia": "196.44",
        "Zimbabwe": "197.211",
        "Lesotho": "41.203",
        "Eswatini": "102.212",
        "Mozambique": "197.249",
        "Malawi": "41.70",
        "Tanzania": "154.72",
    }
    prefix = country_prefixes.get(country, "198.51")
    third = int(np.random.randint(0, 255))
    fourth = int(np.random.randint(1, 255))
    return f"{prefix}.{third}.{fourth}"


# ============================================================
# CAMPAIGNS AND ANOMALIES
# ============================================================

def get_campaign_for_day(config: dict[str, Any], current_day: date) -> dict[str, Any] | None:
    for campaign in config.get("campaigns", []):
        start = datetime.strptime(campaign["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(campaign["end_date"], "%Y-%m-%d").date()
        if start <= current_day <= end:
            return campaign
    return None


def get_anomalies_for_day(config: dict[str, Any], current_day: date) -> list[dict[str, Any]]:
    active_anomalies = []
    for anomaly in config.get("anomalies", []):
        anomaly_date = datetime.strptime(anomaly["date"], "%Y-%m-%d").date()
        if anomaly_date == current_day:
            active_anomalies.append(anomaly)
    return active_anomalies


# ============================================================
# TRAFFIC PLANNING
# ============================================================

def estimate_daily_request_count(config: dict[str, Any], current_day: date, day_index: int) -> int:
    traffic = config["traffic"]
    base = float(traffic["base_daily_requests"])
    weekday_factor = (
        float(traffic["weekday_factor"])
        if current_day.weekday() < 5
        else float(traffic["weekend_factor"])
    )
    monthly_growth = float(traffic["monthly_growth_rate"])
    growth_factor = (1 + monthly_growth) ** (day_index / 30.0)
    variation = float(traffic["daily_random_variation"])
    random_noise = float(np.random.normal(loc=1.0, scale=variation))
    random_noise = float(np.clip(random_noise, 0.45, 1.85))
    campaign = get_campaign_for_day(config, current_day)
    campaign_multiplier = float(campaign["traffic_multiplier"]) if campaign else 1.0
    anomaly_multiplier = 1.0
    anomalies = get_anomalies_for_day(config, current_day)
    for anomaly in anomalies:
        anomaly_multiplier *= float(anomaly.get("multiplier", 1.0))
    anomaly_multiplier = min(anomaly_multiplier, 2.2)
    estimate = base * weekday_factor * growth_factor * random_noise * campaign_multiplier * anomaly_multiplier
    return max(50, int(round(estimate)))


def estimate_session_count(config: dict[str, Any], daily_requests: int) -> int:
    mean_requests = float(config["traffic"]["mean_requests_per_session"])
    return max(10, int(round(daily_requests / mean_requests)))


# ============================================================
# PAGE AND SESSION BEHAVIOUR
# ============================================================

def choose_service(config: dict[str, Any], campaign: dict[str, Any] | None) -> str:
    services = config["services"]
    weights = {
        service_name: float(service_cfg["weight"])
        for service_name, service_cfg in services.items()
    }
    if campaign:
        boosted_services = set(campaign.get("boosted_services", []))
        for service_name in boosted_services:
            if service_name in weights:
                weights[service_name] *= 2.2
    return weighted_choice(weights)


def build_human_journey(config: dict[str, Any], campaign: dict[str, Any] | None) -> list[str]:
    journey = ["/index.html"]
    service_name = choose_service(config, campaign)
    service_cfg = config["services"][service_name]
    service_uri = service_cfg["uri"]
    if np.random.random() < 0.70:
        journey.append(service_uri)
    else:
        if np.random.random() < 0.45:
            journey.append(str(np.random.choice(GENERAL_PAGES)))
        return journey
    if np.random.random() < 0.22:
        journey.append(str(np.random.choice(STATIC_ASSETS)))
    if np.random.random() < 0.25:
        second_service_name = choose_service(config, campaign)
        second_uri = config["services"][second_service_name]["uri"]
        if second_uri != service_uri:
            journey.append(second_uri)
    if service_name == "Events and Promotions":
        event_probability = float(service_cfg.get("event_probability", 0.15))
        if np.random.random() < event_probability:
            journey.append("/event.php")
    else:
        demo_probability = float(service_cfg.get("demo_probability", 0.05))
        if np.random.random() < demo_probability:
            if np.random.random() < 0.30:
                journey.append("/pricing.php")
            journey.append("/scheduledemo.php")
    if np.random.random() < 0.08:
        journey.append("/contact.php")
    return journey


def build_bot_journey(anomalies: list[dict[str, Any]]) -> list[str]:
    if anomalies:
        anomaly = anomalies[0]
        target_uri = anomaly.get("uri", "/prototype.php")
        if anomaly["type"] in {"suspicious_bot_spike", "broken_campaign_link"}:
            repeats = int(np.random.randint(2, 8))
            return ["/robots.txt"] + [target_uri] * repeats
    bot_patterns = [
        ["/robots.txt", "/index.html"],
        ["/index.html"],
        ["/index.html", "/images/logo.png", "/css/site.css"],
        ["/pricing.php", "/contact.php"],
        ["/prototype.php"] * int(np.random.randint(1, 5)),
        ["/wp-admin.php", "/admin.php", "/login.php"],
    ]
    return list(random.choice(bot_patterns))


def service_metadata_from_uri(config: dict[str, Any], uri: str) -> tuple[str, str, str]:
    for service_name, service_cfg in config["services"].items():
        if service_cfg["uri"] == uri:
            request_type = service_name.lower().replace(" ", "_") + "_interest"
            return service_name, service_cfg["category"], request_type
    if uri == "/scheduledemo.php":
        return "Schedule Demo", "Lead Conversion", "demo_request"
    if uri == "/event.php":
        return "Event Signup", "Lead Conversion", "event_signup"
    if uri == "/contact.php":
        return "Contact", "Lead Conversion", "contact_request"
    if uri in STATIC_ASSETS:
        return "Static Asset", "Static Asset", "static_asset"
    if uri in ["/robots.txt", "/wp-admin.php", "/admin.php", "/login.php"]:
        return "Bot or Invalid Request", "Bot/Security", "bot_request"
    if uri in GENERAL_PAGES:
        return "General Website", "General", "general_browse"
    return "Unknown", "Unknown", "unknown_request"


def choose_status_code(is_bot: bool, uri: str, anomalies: list[dict[str, Any]]) -> int:
    for anomaly in anomalies:
        if anomaly["type"] == "broken_campaign_link" and uri == anomaly.get("uri"):
            return int(anomaly.get("status_code", 404))
    if uri in ["/wp-admin.php", "/admin.php", "/login.php"]:
        return 404
    if uri in STATIC_ASSETS and np.random.random() < 0.35:
        return 304
    if is_bot:
        status_options = [200, 304, 404, 500]
        status_probs = np.array([0.70, 0.14, 0.15, 0.01], dtype=float)
    else:
        status_options = [200, 304, 404, 500]
        status_probs = np.array([0.83, 0.13, 0.038, 0.002], dtype=float)
    status_probs = status_probs / status_probs.sum()
    return int(np.random.choice(status_options, p=status_probs))


def generate_response_time_ms(status_code: int, is_bot: bool) -> int:
    if status_code >= 500:
        value = np.random.normal(1500, 350)
    elif status_code == 404:
        value = np.random.normal(280, 80)
    elif is_bot:
        value = np.random.normal(120, 35)
    else:
        value = np.random.normal(240, 90)
    return max(1, int(value))


def generate_bytes_transferred(uri: str, status_code: int) -> int:
    if status_code == 304:
        return 0
    if uri.endswith((".png", ".jpg", ".ico")):
        value = np.random.normal(180_000, 55_000)
    elif uri.endswith((".css", ".js")):
        value = np.random.normal(45_000, 12_000)
    else:
        value = np.random.normal(18_000, 7_000)
    return max(0, int(value))


# ============================================================
# SESSION GENERATION
# ============================================================

def generate_session(config: dict[str, Any], current_day: date, is_bot: bool) -> list[dict[str, Any]]:
    country = weighted_choice(config["countries"])
    ip_address = generate_ip_for_country(country)
    if is_bot:
        user_agent, device_type, browser = random.choice(BOT_USER_AGENTS)
        start_ts = random_time_for_bot_session(current_day)
    else:
        user_agent, device_type, browser = random.choice(HUMAN_USER_AGENTS)
        start_ts = random_time_for_human_session(current_day)
    session_id = stable_session_id(ip_address, user_agent, start_ts)
    campaign = get_campaign_for_day(config, current_day)
    anomalies = get_anomalies_for_day(config, current_day)
    if is_bot:
        journey = build_bot_journey(anomalies)
    else:
        journey = build_human_journey(config, campaign)
    requests = []
    timestamp = start_ts
    for step_index, uri in enumerate(journey):
        if step_index > 0:
            timestamp = timestamp + timedelta(seconds=int(np.random.randint(20, 420)))
        status_code = choose_status_code(is_bot, uri, anomalies)
        service_name, service_category, request_type = service_metadata_from_uri(config, uri)
        request = {
            "timestamp": timestamp,
            "ip_address": ip_address,
            "country": country,
            "is_sadc": classify_sadc(country),
            "method": "GET",
            "uri": uri,
            "status_code": status_code,
            "status_class": status_class(status_code),
            "user_agent": user_agent,
            "device_type": device_type,
            "browser": browser,
            "is_bot": is_bot,
            "session_id": session_id,
            "service_name": service_name,
            "service_category": service_category,
            "request_type": request_type,
            "campaign_name": campaign["name"] if campaign else "None",
            "is_campaign_period": campaign is not None,
            "is_anomaly": len(anomalies) > 0,
            "anomaly_name": anomalies[0]["name"] if anomalies else "None",
            "response_time_ms": generate_response_time_ms(status_code, is_bot),
            "bytes_transferred": generate_bytes_transferred(uri, status_code),
        }
        requests.append(request)
    return requests


# ============================================================
# ENRICHMENT — EXISTING
# ============================================================

def add_date_time_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date.astype(str)
    df["time"] = df["timestamp"].dt.strftime("%H:%M:%S")
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["month"] = df["timestamp"].dt.month
    df["month_name"] = df["timestamp"].dt.month_name()
    df["week_of_year"] = df["timestamp"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["timestamp"].dt.weekday >= 5
    return df


def assign_session_level_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["session_id", "timestamp"]).copy()
    session_summary = (
        df.groupby("session_id")
        .agg(
            first_request_ts=("timestamp", "min"),
            last_request_ts=("timestamp", "max"),
            request_count_session=("uri", "count"),
            distinct_pages_session=("uri", "nunique"),
            entry_page=("uri", "first"),
            exit_page=("uri", "last"),
            converted_to_lead=(
                "uri",
                lambda x: any(v in {"/scheduledemo.php", "/event.php", "/contact.php"} for v in x),
            ),
            has_demo=("uri", lambda x: "/scheduledemo.php" in set(x)),
            has_event=("uri", lambda x: "/event.php" in set(x)),
            has_ai_assistant=("uri", lambda x: "/ai-assistant.php" in set(x)),
            has_prototype=("uri", lambda x: "/prototype.php" in set(x)),
            session_is_bot=("is_bot", "max"),
        )
        .reset_index()
    )
    session_summary["duration_seconds"] = (
        session_summary["last_request_ts"] - session_summary["first_request_ts"]
    ).dt.total_seconds().astype(int)
    session_summary["segment"] = np.select(
        [
            session_summary["session_is_bot"].astype(bool),
            session_summary["has_demo"].astype(bool) | session_summary["has_event"].astype(bool),
            session_summary["has_ai_assistant"].astype(bool) | session_summary["has_prototype"].astype(bool),
        ],
        ["Bot", "High-intent", "Product-curious"],
        default="General browser",
    )
    session_order = (
        df.groupby(["ip_address", "session_id"])["timestamp"]
        .min()
        .reset_index()
        .sort_values(["ip_address", "timestamp"])
    )
    session_order["session_number_for_ip"] = session_order.groupby("ip_address").cumcount() + 1
    session_summary = session_summary.merge(
        session_order[["session_id", "session_number_for_ip"]],
        on="session_id",
        how="left",
    )
    df = df.merge(
        session_summary[[
            "session_id", "first_request_ts", "last_request_ts", "duration_seconds",
            "request_count_session", "distinct_pages_session", "entry_page", "exit_page",
            "converted_to_lead", "segment", "session_number_for_ip",
        ]],
        on="session_id",
        how="left",
    )
    df["is_warm_lead"] = df["uri"].isin(["/scheduledemo.php", "/event.php", "/contact.php"])
    df["event_type"] = np.select(
        [
            df["uri"].eq("/scheduledemo.php"),
            df["uri"].eq("/event.php"),
            df["uri"].eq("/contact.php"),
            df["uri"].eq("/ai-assistant.php"),
        ],
        ["demo_request", "event_signup", "contact_request", "ai_assistant_inquiry"],
        default="page_request",
    )
    return df


# ============================================================
# ENRICHMENT — BI DECISION ENGINE
# ============================================================

def add_bi_enrichment(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(333)
    df = df.copy()
    ts = pd.to_datetime(df["timestamp"])

    # A. Extended time fields
    df["day_name"] = ts.dt.day_name()
    df["week_start_date"] = (ts - pd.to_timedelta(ts.dt.weekday, unit="D")).dt.date.astype(str)
    df["quarter"] = ts.dt.quarter.map({1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"})
    df["is_business_hours"] = ts.dt.hour.between(8, 17) & (ts.dt.weekday < 5)

    # B. Business-friendly service fields
    df["business_service_name"] = df["uri"].map(URI_TO_BUSINESS).fillna("Other")
    df["service_group"] = df["business_service_name"].map(SERVICE_GROUP_MAP).fillna("General")
    df["business_page_type"] = df["business_service_name"].map(PAGE_TYPE_MAP).fillna("Other")
    df["is_service_page"] = df["business_page_type"] == "Service Page"
    df["is_landing_page"] = df["business_page_type"] == "Landing Page"
    df["is_conversion_page"] = df["business_page_type"] == "Conversion Page"
    df["is_ai_assistant_page"] = df["business_service_name"] == "AI Cyber Assistant"

    # G. Geography — assign city/lat/lon at session level for consistency
    session_country = df.groupby("session_id")["country"].first()
    session_cities = {}
    for sid, country in session_country.items():
        cities = COUNTRY_CITIES.get(country, [("Unknown", 0.0, 0.0)])
        chosen = cities[int(rng.integers(0, len(cities)))]
        session_cities[sid] = chosen
    df["city"] = df["session_id"].map(lambda s: session_cities.get(s, ("Unknown", 0.0, 0.0))[0])
    df["latitude"] = df["session_id"].map(lambda s: session_cities.get(s, ("Unknown", 0.0, 0.0))[1])
    df["longitude"] = df["session_id"].map(lambda s: session_cities.get(s, ("Unknown", 0.0, 0.0))[2])
    df["region_group"] = df["is_sadc"].map({True: "SADC", False: "Outside SADC"})

    # Market node fields (row-level from MARKET_CONFIG)
    df["market_node_type"] = df["country"].map(lambda c: MARKET_CONFIG.get(c, {}).get("node_type", "Unknown"))
    df["regional_priority"] = df["country"].map(lambda c: MARKET_CONFIG.get(c, {}).get("priority", "Review"))

    # C. Potential customer scoring (session-level aggregation)
    session_stats = df.groupby("session_id").agg(
        _has_demo=("uri", lambda x: "/scheduledemo.php" in set(x)),
        _has_contact=("uri", lambda x: "/contact.php" in set(x)),
        _has_event=("uri", lambda x: "/event.php" in set(x)),
        _has_ai=("uri", lambda x: "/ai-assistant.php" in set(x)),
        _has_service=("is_service_page", "max") if "is_service_page" in df.columns else ("uri", lambda x: False),
        _pages=("distinct_pages_session", "first"),
        _reqs=("request_count_session", "first"),
        _is_bot=("is_bot", "max"),
        _session_num=("session_number_for_ip", "first"),
        _is_biz_hrs=("is_business_hours", "max"),
        _has_error=("status_code", lambda x: any(s >= 400 for s in x)),
        _segment=("segment", "first"),
        _country=("country", "first"),
        _converted=("converted_to_lead", "first"),
        _is_warm=("is_warm_lead", "max"),
        _entry=("entry_page", "first"),
        _exit=("exit_page", "first"),
        _duration=("duration_seconds", "first"),
        _first_ts=("first_request_ts", "first"),
        _last_ts=("last_request_ts", "first"),
        _campaign=("campaign_name", "first"),
        _is_campaign=("is_campaign_period", "first"),
    ).reset_index()

    # Recompute is_service_page inside aggregation safely
    service_page_uris = {k for k, v in PAGE_TYPE_MAP.items() if v == "Service Page"}
    service_page_uri_raw = {k for k, v in URI_TO_BUSINESS.items() if v in service_page_uris}
    session_stats["_has_service"] = df.groupby("session_id")["uri"].apply(
        lambda x: bool(set(x) & service_page_uri_raw)
    ).values

    def compute_pc_score(row):
        if row["_is_bot"]:
            return 0
        score = 0
        if row["_has_demo"]:
            score += 35
        if row["_has_contact"]:
            score += 30
        if row["_has_event"]:
            score += 25
        if row["_has_ai"]:
            score += 20
        if row["_has_service"]:
            score += 15
        if row["_pages"] >= 3:
            score += 10
        if row["_session_num"] > 1:
            score += 10
        if row["_is_biz_hrs"]:
            score += 5
        if row["_has_error"]:
            score -= 10
        return int(np.clip(score, 0, 100))

    session_stats["pc_score"] = session_stats.apply(compute_pc_score, axis=1)

    def pc_signal(row):
        if row["_is_bot"]:
            return 0
        if (row["_has_demo"] or row["_has_contact"] or row["_has_event"]
                or row["_converted"] or row["_is_warm"]
                or row["_segment"] == "High-intent"
                or (row["_has_ai"] and row["_pages"] >= 3)
                or (row["_has_service"] and row["_pages"] >= 2)):
            return 1
        return 0

    session_stats["pc_signal"] = session_stats.apply(pc_signal, axis=1)

    def pc_type(row):
        if row["_is_bot"]:
            return "Filtered Noise"
        if row["_has_demo"]:
            return "Demo Interested"
        if row["_has_contact"]:
            return "Contact Interested"
        if row["_has_event"]:
            return "Event Interested"
        if row["_has_ai"]:
            return "AI Assistant Interested"
        if row["_has_service"]:
            return "Service Interested"
        if row["_segment"] == "High-intent":
            return "High-Intent Visitor"
        return "General Visitor"

    session_stats["pc_type"] = session_stats.apply(pc_type, axis=1)

    def pc_reason(row):
        reasons = []
        if row["_has_demo"]:
            reasons.append("Demo request")
        if row["_has_contact"]:
            reasons.append("Contact request")
        if row["_has_event"]:
            reasons.append("Event signup")
        if row["_has_ai"]:
            reasons.append("AI Assistant interest")
        if row["_has_service"]:
            reasons.append("Service page visited")
        if row["_pages"] >= 3:
            reasons.append("3+ pages browsed")
        if row["_session_num"] > 1:
            reasons.append("Repeat visitor")
        return "; ".join(reasons) if reasons else "General browse"

    session_stats["pc_reason"] = session_stats.apply(pc_reason, axis=1)

    # Assign PC IDs to signalled sessions
    pc_sessions = session_stats[session_stats["pc_signal"] == 1]["session_id"].reset_index(drop=True)
    pc_id_map = {sid: f"PC-{str(i+1).zfill(6)}" for i, sid in enumerate(pc_sessions)}

    # Sub-scores
    session_stats["intent_score"] = session_stats.apply(
        lambda r: min(100, (35 if r["_has_demo"] else 0) + (25 if r["_has_event"] else 0) + (20 if r["_has_ai"] else 0) + (30 if r["_has_contact"] else 0)), axis=1
    )
    session_stats["engagement_score"] = session_stats.apply(
        lambda r: min(100, int(r["_pages"]) * 15 + (10 if r["_session_num"] > 1 else 0) + (5 if r["_is_biz_hrs"] else 0)), axis=1
    )
    session_stats["conversion_score"] = session_stats.apply(
        lambda r: min(100, (50 if r["_has_demo"] else 0) + (40 if r["_has_contact"] else 0) + (30 if r["_has_event"] else 0)), axis=1
    )
    session_stats["service_value_score"] = session_stats.apply(
        lambda r: min(100, (30 if r["_has_ai"] else 0) + (20 if r["_has_service"] else 0) + (10 if r["_pages"] >= 2 else 0)), axis=1
    )
    session_stats["recency_score"] = 50  # placeholder, all data is in range

    # Map session stats back to row-level
    sid_to_stats = session_stats.set_index("session_id")

    df["potential_customer_signal"] = df["session_id"].map(sid_to_stats["pc_signal"]).fillna(0).astype(int)
    df["potential_customer_id"] = df["session_id"].map(pc_id_map).fillna("")
    df["potential_customer_type"] = df["session_id"].map(sid_to_stats["pc_type"]).fillna("General Visitor")
    df["potential_customer_score"] = df["session_id"].map(sid_to_stats["pc_score"]).fillna(0).astype(int)
    df["intent_score"] = df["session_id"].map(sid_to_stats["intent_score"]).fillna(0).astype(int)
    df["engagement_score"] = df["session_id"].map(sid_to_stats["engagement_score"]).fillna(0).astype(int)
    df["conversion_score"] = df["session_id"].map(sid_to_stats["conversion_score"]).fillna(0).astype(int)
    df["service_value_score"] = df["session_id"].map(sid_to_stats["service_value_score"]).fillna(0).astype(int)
    df["recency_score"] = 50
    df["potential_customer_reason"] = df["session_id"].map(sid_to_stats["pc_reason"]).fillna("General browse")

    # D. Funnel and conversion fields
    def get_conversion_stage(row):
        if row["uri"] in ("/scheduledemo.php", "/contact.php", "/event.php"):
            return "Demo / Event Request"
        if row["uri"] in ("/ai-assistant.php", "/contact.php"):
            return "AI / Contact Interest"
        if row["is_service_page"]:
            return "Service Interest"
        return "Website Visit"

    df["conversion_stage"] = df.apply(get_conversion_stage, axis=1)
    stage_order = {"Website Visit": 1, "Service Interest": 2, "AI / Contact Interest": 3, "Demo / Event Request": 4}
    df["funnel_stage_order"] = df["conversion_stage"].map(stage_order).fillna(1).astype(int)
    df["has_landed"] = True
    df["has_service_interest"] = df["session_id"].map(sid_to_stats["_has_service"]).fillna(False).astype(bool)
    df["has_ai_interest"] = df["session_id"].map(sid_to_stats["_has_ai"]).fillna(False).astype(bool)
    df["has_contact_interest"] = df["session_id"].map(sid_to_stats["_has_contact"]).fillna(False).astype(bool)
    df["has_demo_request"] = df["session_id"].map(sid_to_stats["_has_demo"]).fillna(False).astype(bool)
    df["has_event_signup"] = df["session_id"].map(sid_to_stats["_has_event"]).fillna(False).astype(bool)
    df["converted_to_potential_customer"] = df["potential_customer_signal"] == 1

    def build_conversion_path(row):
        steps = ["Homepage"]
        if row["has_service_interest"]:
            steps.append("Service Page")
        if row["has_ai_interest"]:
            steps.append("AI Assistant")
        if row["has_demo_request"]:
            steps.append("Demo Request")
        elif row["has_contact_interest"]:
            steps.append("Contact")
        elif row["has_event_signup"]:
            steps.append("Event Signup")
        return " > ".join(steps)

    df["conversion_path"] = df.apply(build_conversion_path, axis=1)
    df["dropoff_stage"] = np.where(df["converted_to_potential_customer"], "Converted", df["conversion_stage"])

    # E. Session quality fields
    df["is_engaged_session"] = (df["distinct_pages_session"] >= 3) | (df["request_count_session"] >= 4)

    def depth_cat(n):
        if n <= 1:
            return "Single page"
        if n == 2:
            return "2 pages"
        if n <= 5:
            return "3-5 pages"
        return "6+ pages"

    df["session_depth_category"] = df["distinct_pages_session"].apply(depth_cat)

    def dur_cat(d):
        if d < 60:
            return "< 1 min"
        if d < 300:
            return "1-5 min"
        if d < 900:
            return "5-15 min"
        return "15+ min"

    df["session_duration_category"] = df["duration_seconds"].apply(dur_cat)

    def quality_cat(row):
        if row["is_bot"]:
            return "Bot"
        s = row["potential_customer_score"]
        if s >= 60:
            return "Very High"
        if s >= 35:
            return "High"
        if s >= 15:
            return "Medium"
        return "Low"

    df["session_quality"] = df.apply(quality_cat, axis=1)
    df["is_repeat_visitor"] = df["session_number_for_ip"] > 1

    def session_count_bucket(n):
        if n == 1:
            return "1 visit"
        if n <= 3:
            return "2-3 visits"
        if n <= 7:
            return "4-7 visits"
        return "8+ visits"

    df["session_count_bucket"] = df["session_number_for_ip"].apply(session_count_bucket)

    def visitor_type_fn(row):
        if row["is_bot"]:
            return "Bot"
        if row["session_number_for_ip"] == 1:
            return "First-time visitor"
        if row["session_number_for_ip"] > 3 and row["potential_customer_score"] >= 35:
            return "Repeat high-intent visitor"
        return "Returning visitor"

    df["visitor_type"] = df.apply(visitor_type_fn, axis=1)

    # F. Campaign and marketing fields
    channel_pool = SOURCE_CHANNELS
    df["source_channel"] = rng.choice(channel_pool, size=len(df), replace=True)
    df["campaign_objective"] = df["campaign_name"].map(CAMPAIGN_OBJECTIVES).fillna("Awareness")

    campaign_targets = {
        "SME Cyber Risk Week": ("Botswana; South Africa", "Automated Risk Assessment; Cybersecurity Monitoring"),
        "AI Cyber Assistant Launch Push": ("All SADC", "AI Cyber Assistant"),
        "Government Digital Transformation Expo": ("Botswana; Zambia", "Digital Transformation"),
        "None": ("All SADC", "All Services"),
    }
    df["campaign_target_country"] = df["campaign_name"].map(lambda c: campaign_targets.get(c, ("All SADC", "All Services"))[0])
    df["campaign_target_service"] = df["campaign_name"].map(lambda c: campaign_targets.get(c, ("All SADC", "All Services"))[1])

    df["campaign_period"] = np.where(df["is_campaign_period"], df["campaign_name"], "No Campaign")
    df["campaign_week"] = np.where(df["is_campaign_period"], df["week_start_date"], "N/A")

    campaign_costs = {
        "SME Cyber Risk Week": 35_000,
        "AI Cyber Assistant Launch Push": 55_000,
        "Government Digital Transformation Expo": 45_000,
        "None": 0,
    }
    df["campaign_cost_estimate"] = df["campaign_name"].map(campaign_costs).fillna(0)
    df["campaign_impression_estimate"] = (df["campaign_cost_estimate"] / 0.05).astype(int)
    df["campaign_click_estimate"] = (df["campaign_impression_estimate"] * 0.035).astype(int)
    df["campaign_roi_estimate"] = np.where(
        df["campaign_cost_estimate"] > 0,
        (df["potential_customer_score"] * 500 - df["campaign_cost_estimate"]) / df["campaign_cost_estimate"].clip(lower=1),
        0.0,
    ).round(2)
    df["campaign_quality_score"] = np.clip(df["campaign_roi_estimate"] * 10 + 50, 0, 100).round(1)

    df["landing_page_group"] = df["entry_page"].map(URI_TO_BUSINESS).fillna("Other")
    df["content_group"] = df["service_group"]

    total_requests = len(df)
    country_counts = df.groupby("country")["session_id"].transform("count")
    df["visit_share"] = (country_counts / total_requests).round(4)

    pc_per_country = df[df["potential_customer_signal"] == 1].groupby("country")["session_id"].transform("count")
    total_pc = df["potential_customer_signal"].sum()
    df["conversion_share"] = (df["potential_customer_signal"] / max(total_pc, 1)).round(6)

    def promo_gap(row):
        if row["is_service_page"] and not row["is_campaign_period"]:
            return round(float(rng.uniform(0.3, 0.8)), 2)
        return 0.0

    df["promotion_gap_score"] = df.apply(promo_gap, axis=1)

    # H. Executive strategy fields
    total_rows = len(df)
    country_traffic = df.groupby("country").size() / total_rows
    country_pc_signals = df[df["potential_customer_signal"] == 1].groupby("country").size()
    total_pc_signals = max(df["potential_customer_signal"].sum(), 1)
    country_pc_share = country_pc_signals / total_pc_signals

    def map_exec_fields(country):
        cfg = MARKET_CONFIG.get(country, {})
        t_traffic = cfg.get("target_traffic", 0.05)
        t_pc = cfg.get("target_pc", 0.05)
        a_traffic = float(country_traffic.get(country, 0.0))
        a_pc = float(country_pc_share.get(country, 0.0))
        traffic_var = round(a_traffic - t_traffic, 4)
        pc_var = round(a_pc - t_pc, 4)
        pc_ratio = a_pc / max(t_pc, 0.001)
        if pc_ratio >= 1.0:
            mstatus = "Above Target"
            invest_rec = "Invest"
        elif pc_ratio >= 0.70:
            mstatus = "On Watch"
            invest_rec = "Monitor"
        elif a_pc > 0.01:
            mstatus = "Below Target"
            invest_rec = "Review"
        else:
            mstatus = "Below Target"
            invest_rec = "Pause"
        growth = cfg.get("maturity", "Developing")
        strategic_score = min(100, int(a_pc * 500 + a_traffic * 200))
        return t_traffic, t_pc, a_traffic, a_pc, traffic_var, pc_var, 0.08, strategic_score, mstatus, invest_rec, growth

    exec_map = {c: map_exec_fields(c) for c in df["country"].unique()}
    exec_cols = [
        "target_traffic_share", "target_potential_customer_share",
        "actual_traffic_share", "actual_potential_customer_share",
        "traffic_share_variance", "potential_customer_share_variance",
        "market_growth_rate", "strategic_score", "market_status",
        "investment_recommendation", "executive_note",
    ]
    exec_df = pd.DataFrame.from_dict(exec_map, orient="index", columns=exec_cols).reset_index()
    exec_df.columns = ["country"] + exec_cols
    df = df.merge(exec_df, on="country", how="left")

    # I. Risk and anomaly fields
    def anomaly_cat(row):
        if row["is_anomaly"]:
            name = str(row["anomaly_name"]).lower()
            if "bot" in name or "spike" in name:
                return "Traffic Spike"
            if "broken" in name or "link" in name:
                return "High Error Rate"
            if "viral" in name:
                return "Traffic Spike"
            return "Suspicious Pattern"
        if row["status_code"] >= 500:
            return "High Error Rate"
        if row["response_time_ms"] > 1000:
            return "Slow Response"
        if row["is_bot"]:
            return "Bot Noise"
        return "Normal"

    df["anomaly_category"] = df.apply(anomaly_cat, axis=1)

    def compute_risk_score(row):
        score = 0
        if row["is_anomaly"]:
            score += 40
        if row["is_bot"]:
            score += 20
        if row["status_code"] >= 500:
            score += 25
        elif row["status_code"] >= 400:
            score += 10
        if row["response_time_ms"] > 1000:
            score += 15
        return int(np.clip(score, 0, 100))

    df["risk_score"] = df.apply(compute_risk_score, axis=1)
    df["risk_level"] = pd.cut(
        df["risk_score"],
        bins=[-1, 20, 45, 70, 100],
        labels=["Low", "Medium", "High", "Critical"],
    )

    def risk_reason(row):
        reasons = []
        if row["is_anomaly"]:
            reasons.append(f"Anomaly: {row['anomaly_name']}")
        if row["is_bot"]:
            reasons.append("Bot traffic")
        if row["status_code"] >= 500:
            reasons.append("Server error")
        elif row["status_code"] >= 400:
            reasons.append("Client error")
        if row["response_time_ms"] > 1000:
            reasons.append("Slow response")
        return "; ".join(reasons) if reasons else "Normal"

    df["risk_reason"] = df.apply(risk_reason, axis=1)
    df["requires_review"] = df["risk_level"].isin(["High", "Critical"])
    df["operational_note"] = np.where(df["requires_review"], "Flag for operations review", "No action required")

    # J. Data quality fields
    df["data_quality_flag"] = "Good"
    df.loc[df["country"].isna() | (df["country"] == ""), "data_quality_flag"] = "Review Needed"
    df.loc[df["is_bot"], "data_quality_flag"] = np.where(
        df.loc[df["is_bot"], "data_quality_flag"] == "Good", "Good", "Review Needed"
    )
    df["data_quality_score"] = np.where(df["data_quality_flag"] == "Good", 95, 70)
    df["missing_required_fields"] = (df["country"].isna() | df["uri"].isna() | df["session_id"].isna())
    df["invalid_status_flag"] = ~df["status_code"].isin([200, 304, 404, 500])
    df["duplicate_session_flag"] = df.duplicated(subset=["session_id", "uri", "timestamp"], keep=False)
    df["bot_noise_level"] = np.where(df["is_bot"], "High", "None")
    df["data_freshness_status"] = "Current"
    df["quality_note"] = np.where(
        df["data_quality_flag"] == "Good",
        "Passes all quality checks",
        "Review flagged field values",
    )

    # K. Estimated value fields
    def get_value_range(bsn):
        return SERVICE_VALUE_RANGES.get(bsn, SERVICE_VALUE_RANGES["default"])

    def sample_value(bsn, signal, rng_local):
        lo, hi = get_value_range(bsn)
        if signal == 0:
            lo, hi = lo // 4, hi // 4
        return int(rng_local.integers(lo, hi + 1))

    deal_vals = np.array([
        sample_value(bsn, sig, rng)
        for bsn, sig in zip(df["business_service_name"], df["potential_customer_signal"])
    ])
    df["estimated_deal_value"] = deal_vals
    df["estimated_monthly_value"] = (deal_vals / 12).astype(int)
    df["expected_conversion_value"] = (deal_vals * df["potential_customer_score"] / 100).astype(int)
    df["pipeline_value"] = np.where(df["potential_customer_signal"] == 1, deal_vals, 0)

    def value_band(v):
        if v < 30_000:
            return "Small (<30K)"
        if v < 80_000:
            return "Mid (30K-80K)"
        if v < 150_000:
            return "Large (80K-150K)"
        return "Enterprise (150K+)"

    df["service_value_band"] = df["estimated_deal_value"].apply(value_band)

    return df


# ============================================================
# SHEET BUILDERS
# ============================================================

def build_potential_customers_sheet(enriched: pd.DataFrame) -> pd.DataFrame:
    pc_rows = enriched[enriched["potential_customer_signal"] == 1].copy()

    session_agg = (
        pc_rows.groupby("session_id")
        .agg(
            potential_customer_id=("potential_customer_id", "first"),
            first_seen_timestamp=("first_request_ts", "first"),
            last_seen_timestamp=("last_request_ts", "first"),
            country=("country", "first"),
            city=("city", "first"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            primary_uri=("uri", "first"),
            segment=("segment", "first"),
            potential_customer_type=("potential_customer_type", "first"),
            potential_customer_score=("potential_customer_score", "first"),
            intent_score=("intent_score", "first"),
            engagement_score=("engagement_score", "first"),
            conversion_stage=("conversion_stage", "max"),
            estimated_deal_value=("estimated_deal_value", "max"),
            estimated_monthly_value=("estimated_monthly_value", "max"),
            expected_conversion_value=("expected_conversion_value", "max"),
            pipeline_value=("pipeline_value", "max"),
            campaign_name=("campaign_name", "first"),
            has_demo=("has_demo_request", "max"),
            has_contact=("has_contact_interest", "max"),
            has_event=("has_event_signup", "max"),
            distinct_pages=("distinct_pages_session", "first"),
            duration_seconds=("duration_seconds", "first"),
            session_number=("session_number_for_ip", "first"),
            conversion_path=("conversion_path", "first"),
        )
        .reset_index()
    )

    rng = np.random.default_rng(444)

    def primary_service(row):
        bsn = URI_TO_BUSINESS.get(row["primary_uri"], "General")
        return bsn

    session_agg["service_interest"] = session_agg["primary_uri"].map(URI_TO_BUSINESS).fillna("General")
    session_agg["primary_service"] = session_agg["service_interest"]
    session_agg["secondary_service"] = rng.choice(
        ["Cybersecurity Monitoring", "AI Cyber Assistant", "Digital Transformation", "Automated Risk Assessment", "None"],
        size=len(session_agg), replace=True,
    )

    def pipeline_stage(row):
        if row["has_demo"]:
            return "Demo Requested"
        if row["has_contact"]:
            return "Qualified"
        if row["has_event"]:
            return "Engaged"
        if row["potential_customer_score"] >= 50:
            return "Engaged"
        return "New"

    session_agg["pipeline_stage"] = session_agg.apply(pipeline_stage, axis=1)

    def priority_level(score):
        if score >= 70:
            return "High"
        if score >= 40:
            return "Medium"
        if score >= 20:
            return "Low"
        return "Review"

    session_agg["priority_level"] = session_agg["potential_customer_score"].apply(priority_level)

    session_agg["sales_owner"] = rng.choice(SALES_OWNERS, size=len(session_agg), replace=True)

    def recommended_action(row):
        if row["has_demo"]:
            return "Follow up within 24 hours"
        if row["has_contact"]:
            return "Send AI Assistant case study"
        if row["has_event"]:
            return "Invite to next event"
        if row["potential_customer_score"] >= 50:
            return "Invite to demo"
        if row["potential_customer_score"] >= 30:
            return "Nurture with campaign content"
        return "Monitor activity"

    session_agg["recommended_action"] = session_agg.apply(recommended_action, axis=1)

    ref_date = pd.Timestamp("2026-06-30")
    session_agg["first_seen_timestamp"] = pd.to_datetime(session_agg["first_seen_timestamp"])
    session_agg["lead_age_days"] = (ref_date - session_agg["first_seen_timestamp"]).dt.days
    session_agg["follow_up_due_date"] = (session_agg["first_seen_timestamp"] + pd.Timedelta(days=3)).dt.date.astype(str)

    session_agg["status"] = np.select(
        [
            session_agg["pipeline_stage"] == "Demo Requested",
            session_agg["pipeline_stage"] == "Qualified",
            session_agg["pipeline_stage"] == "Engaged",
        ],
        ["Active", "Active", "Nurture"],
        default="New",
    )

    def last_activity(row):
        parts = []
        if row["has_demo"]:
            parts.append("Requested demo")
        if row["has_contact"]:
            parts.append("Submitted contact form")
        if row["has_event"]:
            parts.append("Registered for event")
        parts.append(f"Browsed {row['distinct_pages']} pages")
        if row["duration_seconds"] > 0:
            parts.append(f"Session duration {row['duration_seconds']}s")
        return "; ".join(parts)

    session_agg["last_activity_summary"] = session_agg.apply(last_activity, axis=1)

    out_cols = [
        "potential_customer_id", "session_id", "first_seen_timestamp", "last_seen_timestamp",
        "country", "city", "latitude", "longitude",
        "service_interest", "primary_service", "secondary_service",
        "segment", "potential_customer_type", "potential_customer_score",
        "intent_score", "engagement_score", "conversion_stage", "pipeline_stage",
        "estimated_deal_value", "estimated_monthly_value", "expected_conversion_value",
        "sales_owner", "recommended_action", "follow_up_due_date", "lead_age_days",
        "priority_level", "status", "last_activity_summary",
    ]
    return session_agg[[c for c in out_cols if c in session_agg.columns]]


def build_market_reference_sheet() -> pd.DataFrame:
    rows = []
    market_notes = {
        "Botswana": "Home market, highest traffic concentration, strong AI Assistant interest",
        "South Africa": "Largest regional economy, strong enterprise demand for cybersecurity",
        "Zambia": "Growing digital adoption, government sector opportunity",
        "Namibia": "Emerging market, infrastructure modernisation underway",
        "Zimbabwe": "High growth potential despite economic constraints",
        "Mozambique": "Early-stage market, limited digital infrastructure",
        "Malawi": "Early-stage market, low current traction",
        "Tanzania": "Large population, early digital economy",
        "Lesotho": "Small market, government-linked opportunities",
        "Eswatini": "Small stable market, limited volume",
    }
    dept_actions = {
        "Botswana": "Deepen AI Assistant and Risk Assessment penetration; grow demo pipeline",
        "South Africa": "Expand Cybersecurity Monitoring; target enterprise accounts",
        "Zambia": "Run targeted campaigns; monitor campaign ROI",
        "Namibia": "Introduce AI Assistant; test pilot campaigns",
        "Zimbabwe": "Increase digital outreach; monitor conversion trends",
        "Mozambique": "Low priority; review quarterly",
        "Malawi": "Low priority; review quarterly",
        "Tanzania": "Emerging opportunity; monitor traffic trends",
        "Lesotho": "Government-focused outreach only",
        "Eswatini": "Maintain presence; no major investment recommended",
    }
    for i, (country, cfg) in enumerate(MARKET_CONFIG.items(), start=1):
        cities = COUNTRY_CITIES.get(country, [("Unknown", 0.0, 0.0)])
        for city, lat, lon in cities:
            rows.append({
                "market_id": f"MKT-{str(i).zfill(3)}",
                "country": country,
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "is_sadc": country in SADC_COUNTRIES,
                "region_group": "SADC",
                "market_node_type": cfg["node_type"],
                "regional_priority": cfg["priority"],
                "target_traffic_share": cfg["target_traffic"],
                "target_potential_customer_share": cfg["target_pc"],
                "target_ai_share": round(cfg["target_pc"] * 0.35, 3),
                "market_maturity": cfg["maturity"],
                "market_notes": market_notes.get(country, ""),
                "recommended_department_action": dept_actions.get(country, "Monitor"),
            })
    return pd.DataFrame(rows)


def build_targets_sheet() -> pd.DataFrame:
    rows = [
        # Sales
        ("Potential Customers per Week", "Sales", 50, 35, 20, "count", "Sessions with PC signal = 1 per calendar week", "Track warm pipeline health weekly"),
        ("Demo Requests per Week", "Sales", 50, 35, 20, "count", "Sessions reaching /scheduledemo.php per week", "Core sales conversion metric"),
        ("AI-to-Demo Conversion", "Sales", 0.10, 0.07, 0.05, "ratio", "Demo requests / AI Assistant sessions", "Measures AI Assistant funnel effectiveness"),
        ("Potential Customer Score", "Sales", 60, 40, 25, "score (0-100)", "Average PC score across all PC-flagged sessions", "Higher score = more commercial intent"),
        ("Follow-up Aging Days", "Sales", 3, 5, 7, "days", "Days since first session for uncontacted PCs", "Aging leads lose conversion probability"),
        # Marketing
        ("Engagement Rate", "Marketing", 0.35, 0.25, 0.15, "ratio", "Engaged sessions / total human sessions", "Benchmark for content effectiveness"),
        ("Campaign Conversion Rate", "Marketing", 0.04, 0.025, 0.01, "ratio", "PC signals generated during campaign / total campaign sessions", "Measures campaign efficiency"),
        ("Campaign ROI Estimate", "Marketing", 3.0, 1.5, 0.5, "ratio", "Estimated pipeline value / campaign cost", "Synthetic ROI for BI demonstration"),
        ("Service Promotion Gap", "Marketing", 0.0, 0.4, 0.7, "score (0-1)", "Score measuring under-promoted services vs traffic share", "Higher score = missed promotion opportunity"),
        ("Human Audience Share", "Marketing", 0.90, 0.85, 0.80, "ratio", "Human sessions / total sessions", "Monitor bot pollution of audience"),
        # Executive
        ("AI Assistant Share", "Executive", 0.25, 0.15, 0.10, "ratio", "AI Assistant page sessions / total human sessions", "Flagship product traction indicator"),
        ("Active SADC Markets", "Executive", 8, 5, 3, "count", "Number of SADC countries with PC signals in period", "Regional breadth of commercial activity"),
        ("Regional Potential Customer Share", "Executive", 0.70, 0.50, 0.30, "ratio", "PC signals from SADC vs total PC signals", "Strategic market concentration measure"),
        ("Growth Direction", "Executive", 1, 0, -1, "direction (+1/-1)", "Month-on-month PC trend direction", "Positive = growing pipeline"),
        ("Anomaly Days", "Executive", 0, 3, 7, "count", "Days with active anomaly flags in period", "High anomaly days signal operational risk"),
        ("Strategic Risk Score", "Executive", 20, 50, 75, "score (0-100)", "Average risk score across all sessions", "Composite operational risk indicator"),
    ]
    return pd.DataFrame(rows, columns=[
        "metric_name", "department", "target_value", "warning_threshold",
        "critical_threshold", "unit", "calculation_note", "business_reason",
    ])


def build_forecast_sheet(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    fid = 1

    # Group by week for forecasting base
    enriched = enriched.copy()
    enriched["week_start"] = pd.to_datetime(enriched["week_start_date"])

    dept_metrics = [
        ("Sales", "Potential Customers", lambda df: df[df["potential_customer_signal"] == 1].groupby("week_start")["session_id"].nunique()),
        ("Sales", "Demo Requests", lambda df: df[df["uri"] == "/scheduledemo.php"].groupby("week_start")["session_id"].nunique()),
        ("Marketing", "Engaged Sessions", lambda df: df[df["is_engaged_session"] == True].groupby("week_start")["session_id"].nunique()),
        ("Marketing", "Campaign Leads", lambda df: df[(df["is_campaign_period"] == True) & (df["potential_customer_signal"] == 1)].groupby("week_start")["session_id"].nunique()),
        ("Executive", "AI Assistant Traction", lambda df: df[df["is_ai_assistant_page"] == True].groupby("week_start")["session_id"].nunique()),
        ("Executive", "Regional Risk Score", lambda df: df.groupby("week_start")["risk_score"].mean()),
    ]

    dept_targets = {
        ("Sales", "Potential Customers"): 50,
        ("Sales", "Demo Requests"): 50,
        ("Marketing", "Engaged Sessions"): 200,
        ("Marketing", "Campaign Leads"): 30,
        ("Executive", "AI Assistant Traction"): 100,
        ("Executive", "Regional Risk Score"): 20,
    }

    for dept, metric, agg_fn in dept_metrics:
        series = agg_fn(enriched).sort_index()
        if len(series) < 2:
            continue
        x = np.arange(len(series))
        y = series.values.astype(float)
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs

        # Generate 4-week forecast
        last_week = series.index.max()
        for i in range(1, 5):
            fw = last_week + pd.Timedelta(weeks=i)
            fv = max(0.0, slope * (len(series) + i - 1) + intercept)
            std_err = float(np.std(y) * 0.15)
            lb = max(0.0, fv - 1.96 * std_err)
            ub = fv + 1.96 * std_err
            target = dept_targets.get((dept, metric), 0)
            variance = round(fv - target, 2)
            rows.append({
                "forecast_id": f"FC-{str(fid).zfill(5)}",
                "department": dept,
                "metric_name": metric,
                "forecast_date": fw.date().isoformat(),
                "forecast_period": f"Week of {fw.date().isoformat()}",
                "actual_value": None,
                "forecast_value": round(fv, 1),
                "forecast_lower_bound": round(lb, 1),
                "forecast_upper_bound": round(ub, 1),
                "target_value": target,
                "variance_to_target": variance,
                "forecast_confidence": "Medium",
                "forecast_model": "Linear Trend",
                "forecast_note": f"Rule-based linear projection from {len(series)} weeks of historical data. Not a predictive AI model.",
            })
            fid += 1

        # Include historical actuals
        for week_ts, actual in series.items():
            rows.append({
                "forecast_id": f"FC-{str(fid).zfill(5)}",
                "department": dept,
                "metric_name": metric,
                "forecast_date": week_ts.date().isoformat(),
                "forecast_period": f"Week of {week_ts.date().isoformat()}",
                "actual_value": int(actual),
                "forecast_value": None,
                "forecast_lower_bound": None,
                "forecast_upper_bound": None,
                "target_value": dept_targets.get((dept, metric), 0),
                "variance_to_target": round(float(actual) - dept_targets.get((dept, metric), 0), 2),
                "forecast_confidence": "Actual",
                "forecast_model": "Historical",
                "forecast_note": "Observed value from synthetic dataset.",
            })
            fid += 1

    return pd.DataFrame(rows)


def build_data_quality_sheet(enriched: pd.DataFrame) -> pd.DataFrame:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(enriched)

    checks = []

    # Missing country
    missing_country = int(enriched["country"].isna().sum())
    checks.append(("Missing country values", "Completeness", f"{missing_country} rows missing", round(1 - missing_country / max(total, 1), 4), "Good" if missing_country == 0 else "Review Needed", missing_country, now_str, "Verify country enrichment logic"))

    # Missing service
    missing_service = int((enriched["service_name"].isna() | (enriched["service_name"] == "")).sum())
    checks.append(("Missing service values", "Completeness", f"{missing_service} rows missing", round(1 - missing_service / max(total, 1), 4), "Good" if missing_service < total * 0.01 else "Review Needed", missing_service, now_str, "Check URI-to-service mapping"))

    # Duplicate sessions
    dup_sessions = int(enriched.duplicated(subset=["session_id", "uri", "timestamp"]).sum())
    checks.append(("Duplicate session-URI-timestamp rows", "Uniqueness", f"{dup_sessions} duplicates", round(1 - dup_sessions / max(total, 1), 4), "Good" if dup_sessions == 0 else "Review Needed", dup_sessions, now_str, "Review deduplication logic"))

    # Bot noise level
    bot_count = int(enriched["is_bot"].sum())
    bot_ratio = bot_count / max(total, 1)
    checks.append(("Bot noise level", "Data Purity", f"{bot_ratio:.1%} of requests are bots", round(1 - bot_ratio, 4), "Good" if bot_ratio < 0.15 else "Review Needed", bot_count, now_str, "Monitor bot filtering in dashboard"))

    # Failed visit rate
    failed = int((enriched["status_code"] >= 400).sum())
    failed_ratio = failed / max(total, 1)
    checks.append(("Failed visit rate (4xx+5xx)", "Reliability", f"{failed_ratio:.1%} of requests failed", round(1 - failed_ratio, 4), "Good" if failed_ratio < 0.10 else "Review Needed", failed, now_str, "Check anomaly and broken link flags"))

    # Forecast data sufficiency
    weeks = enriched["week_start_date"].nunique()
    checks.append(("Forecast data sufficiency", "Completeness", f"{weeks} weeks of data available", min(1.0, weeks / 12), "Good" if weeks >= 8 else "Limited Data", 0, now_str, "More weeks improves forecast accuracy"))

    # Potential customer scoring completeness
    pc_with_score = int((enriched["potential_customer_score"] > 0).sum())
    checks.append(("Potential customer scoring completeness", "Completeness", f"{pc_with_score:,} rows scored", round(pc_with_score / max(total, 1), 4), "Good", 0, now_str, "All rows receive a score (0 for bots/low-intent)"))

    # Coordinate mapping completeness
    mapped = int((enriched["latitude"] != 0.0).sum())
    checks.append(("Coordinate mapping completeness", "Completeness", f"{mapped:,} rows with coordinates", round(mapped / max(total, 1), 4), "Good" if mapped / max(total, 1) > 0.90 else "Review Needed", total - mapped, now_str, "Extend COUNTRY_CITIES mapping for unmapped countries"))

    # Campaign field completeness
    campaign_filled = int((enriched["campaign_name"] != "None").sum())
    checks.append(("Campaign field completeness", "Completeness", f"{campaign_filled:,} rows in campaign periods", round(campaign_filled / max(total, 1), 4), "Good", 0, now_str, "Campaign fields populated for all campaign-period rows"))

    # Status code validity
    valid_codes = {200, 304, 404, 500}
    invalid_sc = int((~enriched["status_code"].isin(valid_codes)).sum()) if "status_code" in enriched.columns else 0
    checks.append(("Status code validity", "Validity", f"{invalid_sc} rows with unexpected status codes", round(1 - invalid_sc / max(total, 1), 4), "Good" if invalid_sc == 0 else "Review Needed", invalid_sc, now_str, "Verify status code generation logic"))

    return pd.DataFrame(checks, columns=[
        "check_name", "check_category", "result", "score",
        "status", "affected_rows", "last_checked", "recommended_action",
    ])


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_dataset(config_path: str = "config.yaml") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    config = load_config(config_path)
    seed = int(config["project"]["random_seed"])
    random.seed(seed)
    np.random.seed(seed)

    start_date = datetime.strptime(config["date_range"]["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(config["date_range"]["end_date"], "%Y-%m-%d").date()

    all_requests = []
    summary_rows = []
    current_day = start_date
    day_index = 0

    while current_day <= end_date:
        daily_request_target = estimate_daily_request_count(config, current_day, day_index)
        session_count = estimate_session_count(config, daily_request_target)
        bot_ratio = float(np.random.uniform(
            float(config["traffic"]["bot_ratio_min"]),
            float(config["traffic"]["bot_ratio_max"]),
        ))
        bot_sessions = int(round(session_count * bot_ratio))
        human_sessions = max(1, session_count - bot_sessions)
        before_count = len(all_requests)
        for _ in range(human_sessions):
            all_requests.extend(generate_session(config, current_day, is_bot=False))
        for _ in range(bot_sessions):
            all_requests.extend(generate_session(config, current_day, is_bot=True))
        after_count = len(all_requests)
        actual_requests = after_count - before_count
        campaign = get_campaign_for_day(config, current_day)
        anomalies = get_anomalies_for_day(config, current_day)
        summary_rows.append({
            "date": current_day.isoformat(),
            "target_requests": daily_request_target,
            "actual_requests": actual_requests,
            "estimated_sessions": session_count,
            "human_sessions": human_sessions,
            "bot_sessions": bot_sessions,
            "bot_ratio": round(bot_sessions / max(session_count, 1), 4),
            "campaign_name": campaign["name"] if campaign else "None",
            "anomaly_count": len(anomalies),
            "anomaly_names": ", ".join(a["name"] for a in anomalies) if anomalies else "None",
        })
        current_day += timedelta(days=1)
        day_index += 1

    enriched = pd.DataFrame(all_requests)
    if enriched.empty:
        raise ValueError("No data was generated. Please check config.yaml settings.")

    enriched = enriched.sort_values("timestamp").reset_index(drop=True)
    enriched.insert(0, "request_id", range(1, len(enriched) + 1))
    enriched = add_date_time_fields(enriched)
    enriched = assign_session_level_fields(enriched)

    enriched_columns = [
        "request_id", "timestamp", "date", "time", "hour", "day_of_week",
        "month_name", "week_of_year", "is_weekend", "ip_address", "country", "is_sadc",
        "method", "uri", "service_name", "service_category", "request_type",
        "status_code", "status_class", "user_agent", "device_type", "browser",
        "is_bot", "session_id", "session_number_for_ip", "first_request_ts",
        "last_request_ts", "duration_seconds", "request_count_session",
        "distinct_pages_session", "entry_page", "exit_page", "segment",
        "is_warm_lead", "event_type", "converted_to_lead", "campaign_name",
        "is_campaign_period", "is_anomaly", "anomaly_name",
        "response_time_ms", "bytes_transferred",
    ]
    enriched = enriched[enriched_columns]

    # Apply BI enrichment
    enriched = add_bi_enrichment(enriched)

    raw_iis = enriched[[
        "date", "time", "ip_address", "method", "uri", "status_code",
        "user_agent", "bytes_transferred", "response_time_ms",
    ]].copy()

    summary = pd.DataFrame(summary_rows)
    return raw_iis, enriched, summary


def save_outputs(config_path: str = "config.yaml") -> None:
    config = load_config(config_path)
    output = config["output"]

    raw_iis, enriched, summary = generate_dataset(config_path)

    ensure_output_folder(output["raw_iis_csv"])
    ensure_output_folder(output["enriched_csv"])
    ensure_output_folder(output["excel_file"])
    ensure_output_folder(output["summary_csv"])

    raw_iis.to_csv(output["raw_iis_csv"], index=False)
    enriched.to_csv(output["enriched_csv"], index=False)
    summary.to_csv(output["summary_csv"], index=False)

    # Build supporting sheets
    print("Building supporting sheets...")
    pc_sheet = build_potential_customers_sheet(enriched)
    market_sheet = build_market_reference_sheet()
    targets_sheet = build_targets_sheet()
    forecast_sheet = build_forecast_sheet(enriched)
    dq_sheet = build_data_quality_sheet(enriched)

    # Old workbook (backward compat)
    with pd.ExcelWriter(output["excel_file"], engine="openpyxl") as writer:
        raw_iis.to_excel(writer, sheet_name="Raw_IIS_Logs", index=False)
        enriched.to_excel(writer, sheet_name="Enriched_BI_Logs", index=False)
        summary.to_excel(writer, sheet_name="Generation_Summary", index=False)

    # New decision engine workbook
    decision_engine_path = "data/output/cybernova_decision_engine_dataset.xlsx"
    ensure_output_folder(decision_engine_path)
    with pd.ExcelWriter(decision_engine_path, engine="openpyxl") as writer:
        raw_iis.to_excel(writer, sheet_name="Raw_IIS_Logs", index=False)
        enriched.to_excel(writer, sheet_name="Enriched_BI_Logs", index=False)
        pc_sheet.to_excel(writer, sheet_name="Potential_Customers", index=False)
        market_sheet.to_excel(writer, sheet_name="Market_Reference", index=False)
        targets_sheet.to_excel(writer, sheet_name="Targets_and_Assumptions", index=False)
        forecast_sheet.to_excel(writer, sheet_name="Forecast_Outputs", index=False)
        dq_sheet.to_excel(writer, sheet_name="Data_Quality_Summary", index=False)

    print()
    print("CyberNova synthetic log generation complete.")
    print("=" * 60)
    print(f"Raw IIS logs:          {output['raw_iis_csv']} | rows: {len(raw_iis):,}")
    print(f"Enriched BI logs:      {output['enriched_csv']} | rows: {len(enriched):,}")
    print(f"Old Excel workbook:    {output['excel_file']}")
    print(f"Decision engine XLSX:  {decision_engine_path}")
    print(f"Potential customers:   {len(pc_sheet):,} sessions")
    print(f"Market reference:      {len(market_sheet):,} market nodes")
    print(f"Forecast outputs:      {len(forecast_sheet):,} rows")
    print(f"Data quality checks:   {len(dq_sheet):,} checks")
    print(f"Generation summary:    {output['summary_csv']}")

    sessions = enriched["session_id"].nunique()
    human_sessions = enriched.loc[~enriched["is_bot"], "session_id"].nunique()
    warm_leads = int(enriched["is_warm_lead"].sum())
    warm_lead_rate = warm_leads / max(human_sessions, 1)
    bot_request_ratio = enriched["is_bot"].mean()
    pc_count = int(enriched["potential_customer_signal"].sum())

    print()
    print("Quick validation")
    print("=" * 60)
    print(f"Unique sessions:       {sessions:,}")
    print(f"Human sessions:        {human_sessions:,}")
    print(f"Warm lead events:      {warm_leads:,}")
    print(f"Warm lead rate:        {warm_lead_rate:.2%}")
    print(f"Potential customers:   {pc_count:,} row signals")
    print(f"Unique PCs:            {len(pc_sheet):,} sessions")
    print(f"Bot request ratio:     {bot_request_ratio:.2%}")
    print()


if __name__ == "__main__":
    save_outputs("config.yaml")
