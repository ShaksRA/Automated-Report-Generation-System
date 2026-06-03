"""
Scheduler
Runs the full report pipeline on a recurring schedule.
Can also be triggered manually via CLI or via the main.py entry point.
"""
import logging
import signal
import sys
import time
from datetime import datetime

import schedule

from src.config import SCHEDULE_DAY, SCHEDULE_TIME
from src.core.data_processor import load_and_process_all
from src.core.report_builder import build_report
from src.api.api_client import fetch_external_kpis, post_report_notification
from src.utils.logger import get_logger
from src.utils.email_sender import send_report_email

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline() -> str:
    """
    Full end-to-end pipeline:
      1. Load & process raw data
      2. Fetch external KPIs via REST API
      3. Build Excel report
      4. (Optional) email report
      5. (Optional) webhook notification
    Returns path to generated report.
    """
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("PIPELINE START  %s", start.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    # Step 1 – ETL
    logger.info("[1/4] Loading and processing data…")
    data = load_and_process_all()

    # Step 2 – Enrich with API data
    logger.info("[2/4] Fetching external KPIs via REST API…")
    benchmarks = fetch_external_kpis()
    if benchmarks:
        data["benchmarks"] = benchmarks
        logger.info("      Benchmarks: %s", benchmarks.get("benchmark_source"))

    # Step 3 – Build report
    logger.info("[3/4] Building Excel report…")
    report_path = build_report(data)

    # Step 4 – Notifications
    logger.info("[4/4] Sending notifications…")
    send_report_email(str(report_path))
    post_report_notification(str(report_path), "manager@acme.com")

    elapsed = (datetime.now() - start).total_seconds()
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE in %.1f seconds", elapsed)
    logger.info("Report: %s", report_path)
    logger.info("=" * 60)

    return str(report_path)


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler entry point
# ─────────────────────────────────────────────────────────────────────────────

def start_scheduler():
    """Register the weekly job and start the blocking scheduler loop."""
    day_fn = getattr(schedule.every(), SCHEDULE_DAY, schedule.every().monday)
    day_fn.at(SCHEDULE_TIME).do(_safe_run)

    logger.info(
        "Scheduler started. Next run: every %s at %s",
        SCHEDULE_DAY, SCHEDULE_TIME,
    )

    # Graceful shutdown on SIGTERM / SIGINT
    def _shutdown(signum, frame):
        logger.info("Shutdown signal received — stopping scheduler.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    while True:
        schedule.run_pending()
        time.sleep(30)


def _safe_run():
    try:
        run_pipeline()
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
