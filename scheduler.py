"""
Automated Video Scheduler
=========================
Runs the full video pipeline (generate script → AI images → voiceover → video → YouTube upload)
at 7:00 AM and 7:00 PM IST daily, fully automated with zero user input.

Usage:
    python scheduler.py            # Start the scheduler (runs forever)
    python scheduler.py --test     # Dry-run: verify schedule setup without waiting
    python scheduler.py --now      # Run the pipeline immediately once, then exit
"""

import sys
import os
import time
import asyncio
import logging
import argparse
from datetime import datetime

# Fix Windows encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add src to path so we can import the pipeline
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import schedule

# ---- Logging Setup ----
os.makedirs("outputs", exist_ok=True)
LOG_FILE = os.path.join("outputs", "scheduler.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("scheduler")


def run_pipeline_job():
    """
    Execute the full video pipeline: generate script → images → voiceover → video → YouTube upload.
    This function is called by the scheduler at the configured times.
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"{'='*60}")
    logger.info(f"PIPELINE RUN STARTED  |  Run ID: {run_id}")
    logger.info(f"{'='*60}")

    try:
        # Import here to pick up any .env changes at runtime
        from app import run_full_pipeline

        # Run the async pipeline
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_full_pipeline(script_text=None, auto_upload=True))
        finally:
            loop.close()

        logger.info(f"PIPELINE RUN COMPLETE  |  Run ID: {run_id}")
        logger.info(f"Video generated and uploaded to YouTube successfully!")

    except Exception as e:
        logger.error(f"PIPELINE RUN FAILED  |  Run ID: {run_id}")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Don't re-raise — let the scheduler continue for the next run
    
    logger.info(f"{'='*60}")
    logger.info(f"Next runs: {get_next_runs()}")
    logger.info(f"{'='*60}\n")


def get_next_runs():
    """Get a human-readable list of upcoming scheduled jobs."""
    jobs = schedule.get_jobs()
    if not jobs:
        return "No jobs scheduled"
    return ", ".join(str(j.next_run.strftime("%Y-%m-%d %H:%M IST")) for j in jobs if j.next_run)


def setup_schedule():
    """Configure the daily schedule: 7:00 AM and 7:00 PM IST."""
    schedule.every().day.at("07:00").do(run_pipeline_job)
    schedule.every().day.at("19:00").do(run_pipeline_job)
    logger.info("Schedule configured:")
    logger.info("  - Daily at 07:00 AM IST  (morning upload)")
    logger.info("  - Daily at 19:00 PM IST  (evening upload)")


def main():
    parser = argparse.ArgumentParser(description="Automated YouTube Video Scheduler")
    parser.add_argument("--test", action="store_true", help="Dry-run: verify setup without waiting")
    parser.add_argument("--now", action="store_true", help="Run pipeline immediately once, then exit")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("  WEBORAX VIDEO SCHEDULER")
    logger.info("  Automated YouTube Shorts Upload")
    logger.info("  Schedule: 7:00 AM & 7:00 PM IST Daily")
    logger.info("=" * 60)

    # Verify imports work
    try:
        from app import run_full_pipeline
        logger.info("[OK] Pipeline module imported successfully")
    except ImportError as e:
        logger.error(f"[FAIL] Cannot import pipeline: {e}")
        logger.error("Make sure you're running from the WeboraxModel directory")
        sys.exit(1)

    if args.now:
        logger.info("Running pipeline immediately (--now mode)...")
        run_pipeline_job()
        logger.info("Done! Exiting.")
        return

    setup_schedule()

    if args.test:
        logger.info(f"\n[TEST MODE] Schedule verified successfully!")
        logger.info(f"Next scheduled runs: {get_next_runs()}")
        logger.info("Exiting (test mode). Remove --test to run for real.")
        return

    logger.info(f"\nScheduler is LIVE! Waiting for next run...")
    logger.info(f"Next scheduled runs: {get_next_runs()}")
    logger.info(f"Log file: {os.path.abspath(LOG_FILE)}")
    logger.info("Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user (Ctrl+C).")


if __name__ == "__main__":
    main()
