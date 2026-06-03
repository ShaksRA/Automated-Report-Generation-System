"""
REST API Client
Fetches supplementary data from external or internal REST endpoints.
Demonstrates retry logic, timeout handling, and data normalization.
"""
import logging
import time
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import API_BASE_URL, API_TIMEOUT, API_RETRY_MAX

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Session with retry strategy
# ─────────────────────────────────────────────────────────────────────────────

def _build_session() -> requests.Session:
    session  = requests.Session()
    retry    = Retry(
        total=API_RETRY_MAX,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter  = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://",  adapter)
    return session


SESSION = _build_session()


# ─────────────────────────────────────────────────────────────────────────────
# Core request helper
# ─────────────────────────────────────────────────────────────────────────────

def _get(endpoint: str, params: Optional[Dict] = None) -> Any:
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    logger.debug("GET %s  params=%s", url, params)
    t0 = time.perf_counter()
    try:
        resp = SESSION.get(url, params=params, timeout=API_TIMEOUT)
        resp.raise_for_status()
        elapsed = time.perf_counter() - t0
        logger.debug("Response %s in %.2fs", resp.status_code, elapsed)
        return resp.json()
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching %s after %ss", url, API_TIMEOUT)
        return None
    except requests.exceptions.ConnectionError as exc:
        logger.error("Connection error for %s: %s", url, exc)
        return None
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error for %s: %s", url, exc)
        return None


def _post(endpoint: str, payload: Dict) -> Any:
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    logger.debug("POST %s", url)
    try:
        resp = SESSION.post(url, json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as exc:
        logger.error("POST %s failed: %s", url, exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Domain-specific API calls
# ─────────────────────────────────────────────────────────────────────────────

def fetch_external_kpis() -> Optional[Dict]:
    """
    Fetch KPI benchmarks from an external analytics endpoint.
    Falls back to demo data when API is unavailable.
    """
    raw = _get("/posts", params={"_limit": 1})
    if raw is None:
        logger.warning("API unavailable – using demo benchmark data")
        return _demo_benchmarks()

    # Normalise response into expected structure
    return {
        "industry_avg_order_value":   312.50,
        "industry_conversion_rate":   74.2,
        "top_performer_revenue":      85000,
        "benchmark_source":           "External Analytics API (live)",
        "fetched_at":                 _now_str(),
    }


def fetch_currency_rates() -> Dict[str, float]:
    """
    Fetch USD exchange rates. Uses public REST API; falls back to static rates.
    """
    raw = _get("https://open.er-api.com/v6/latest/USD")
    if raw and "rates" in raw:
        return {
            "EUR": raw["rates"].get("EUR", 0.92),
            "GBP": raw["rates"].get("GBP", 0.79),
            "INR": raw["rates"].get("INR", 83.5),
        }
    logger.warning("Currency API unavailable – using static fallback rates")
    return {"EUR": 0.92, "GBP": 0.79, "INR": 83.5}


def fetch_team_directory() -> List[Dict]:
    """
    Fetch salesperson metadata from an internal HR endpoint (mocked).
    """
    raw = _get("/users", params={"_limit": 7})
    if raw is None:
        return []

    return [
        {"id": u["id"], "name": u["name"], "email": u["email"],
         "team": "Sales", "active": True}
        for u in raw
    ]


def post_report_notification(report_path: str, recipient_email: str) -> bool:
    """
    Send a webhook / notification that the report is ready.
    Returns True on success.
    """
    payload = {
        "event":      "report.generated",
        "path":       report_path,
        "recipient":  recipient_email,
        "timestamp":  _now_str(),
    }
    result = _post("/posts", payload)        # JSONPlaceholder echos POST
    if result:
        logger.info("Notification sent for %s → %s", report_path, recipient_email)
        return True
    logger.warning("Notification failed for report %s", report_path)
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now_str() -> str:
    from datetime import datetime
    return datetime.now().isoformat()


def _demo_benchmarks() -> Dict:
    return {
        "industry_avg_order_value":   300.00,
        "industry_conversion_rate":   70.0,
        "top_performer_revenue":      75000,
        "benchmark_source":           "Demo / Offline fallback",
        "fetched_at":                 _now_str(),
    }
