"""
Configuration settings for the Automated Report Generation System.
"""
import os
from pathlib import Path

# ── Project Root ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Data Paths ───────────────────────────────────────────────────────────────
DATA_DIR        = BASE_DIR / "data"
RAW_DATA_DIR    = DATA_DIR / "raw"
PROCESSED_DIR   = DATA_DIR / "processed"
EXPORTS_DIR     = DATA_DIR / "exports"
REPORTS_DIR     = BASE_DIR / "reports" / "output"

# ── Report Settings ──────────────────────────────────────────────────────────
REPORT_TITLE       = "Weekly Business Intelligence Report"
COMPANY_NAME       = "Acme Corporation"
REPORT_AUTHOR      = "Automated Report System"
DATE_FORMAT        = "%Y-%m-%d"
DATETIME_FORMAT    = "%Y-%m-%d %H:%M:%S"

# ── Excel Styling ────────────────────────────────────────────────────────────
COLORS = {
    "primary":     "1A237E",   # Deep indigo header
    "secondary":   "283593",
    "accent":      "42A5F5",   # Blue accent
    "success":     "2E7D32",   # Green
    "warning":     "F57F17",   # Amber
    "danger":      "C62828",   # Red
    "light_bg":    "E8EAF6",   # Lavender tint
    "alt_row":     "F5F5F5",   # Light gray alternate row
    "white":       "FFFFFF",
    "text_dark":   "212121",
}

FONTS = {
    "header":  "Calibri",
    "body":    "Calibri",
    "size_h1": 16,
    "size_h2": 13,
    "size_h3": 11,
    "size_body": 10,
}

# ── API Settings (Mock / Real REST endpoint) ─────────────────────────────────
API_BASE_URL   = os.getenv("API_BASE_URL", "https://jsonplaceholder.typicode.com")
API_TIMEOUT    = int(os.getenv("API_TIMEOUT", "30"))
API_RETRY_MAX  = int(os.getenv("API_RETRY_MAX", "3"))

# ── Scheduling ────────────────────────────────────────────────────────────────
SCHEDULE_DAY  = os.getenv("SCHEDULE_DAY",  "monday")   # Day to run weekly report
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "08:00")    # HH:MM (24h)

# ── Email (optional SMTP, set via env vars) ───────────────────────────────────
EMAIL_ENABLED  = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER      = os.getenv("SMTP_USER", "")
SMTP_PASSWORD  = os.getenv("SMTP_PASSWORD", "")
EMAIL_TO       = os.getenv("EMAIL_TO", "").split(",")

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR   = BASE_DIR / "logs"
