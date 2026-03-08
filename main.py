# main.py
import argparse
import time
import sys
import os
import yaml
from dotenv import load_dotenv
from loguru import logger
from core.database import Database
from core.runner import run_once

load_dotenv()


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )
    logger.add(
        "logs/bytohled_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level="DEBUG",
        encoding="utf-8",
    )


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="BytoHled — RealitniBot Ostrava")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--once",
        action="store_true",
        help="Run one scraping cycle and exit (for GitHub Actions)",
    )
    group.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously on scheduler interval (local dev)",
    )
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--db", default="listings.db", help="Path to SQLite database")
    args = parser.parse_args()

    setup_logging()
    config = load_config(args.config)
    db = Database(args.db)

    if args.once:
        logger.info("BytoHled starting — single run mode")
        try:
            run_once(config, db)
        finally:
            db.close()
        logger.info("BytoHled finished")
    elif args.daemon:
        interval = config.get("scheduler", {}).get("interval_minutes", 20) * 60
        logger.info(f"BytoHled starting — daemon mode (interval: {interval}s)")
        try:
            while True:
                try:
                    run_once(config, db)
                except Exception as e:
                    logger.error(f"Cycle error: {e}")
                logger.info(f"Sleeping {interval}s until next cycle...")
                time.sleep(interval)
        finally:
            db.close()


if __name__ == "__main__":
    main()
