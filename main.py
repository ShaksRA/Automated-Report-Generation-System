#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import get_logger
logger = get_logger("main")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", action="store_true")
    parser.add_argument("--web", action="store_true")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--output", type=str, default=None)
    return parser.parse_args()


def main():
    args = parse_args()

    if args.output:
        import src.config as cfg
        cfg.REPORTS_DIR = Path(args.output)
        cfg.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.web:
        if args.schedule:
            import threading
            from src.scheduler import start_scheduler
            t = threading.Thread(target=start_scheduler, daemon=True)
            t.start()
            logger.info("Background scheduler started.")

        # Railway injects PORT automatically — always read from env
        port = args.port or int(os.environ.get("PORT", 8080))

        from src.dashboard import app
        logger.info("Starting web dashboard on 0.0.0.0:%s", port)
        app.run(host="0.0.0.0", port=port, debug=False)

    elif args.schedule:
        from src.scheduler import start_scheduler
        start_scheduler()

    else:
        from src.scheduler import run_pipeline
        report_path = run_pipeline()
        print(f"\n✅  Report generated: {report_path}\n")


if __name__ == "__main__":
    main()
