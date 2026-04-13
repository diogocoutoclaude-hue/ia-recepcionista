"""
Daily batch sender: sends 20 emails scheduled for 3PM today.
Designed to run as a cron job Mon-Sat at 14:50 Lisbon time.

Tracks progress in emails_progress.json so it picks up where it left off.
Skips Sundays automatically.

Usage:
    python outreach/send_daily_batch.py
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from outreach.send_campaign import CampaignSender

LISBON_TZ = ZoneInfo("Europe/Lisbon")
BATCH_SIZE = 20
STAGGER_MINUTES = 3

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EMAILS_PATH = os.path.join(SCRIPT_DIR, "emails_ready.json")
PROGRESS_PATH = os.path.join(SCRIPT_DIR, "emails_progress.json")
LOG_PATH = os.path.join(SCRIPT_DIR, "daily_send_log.txt")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)


def load_progress():
    """Load progress tracker — which emails have already been sent."""
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"sent_emails": [], "last_run": None}


def save_progress(progress):
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from utils.atomic_writer import atomic_write_json
    atomic_write_json(PROGRESS_PATH, progress)


def main():
    now = datetime.now(LISBON_TZ)

    # Skip Sunday
    if now.weekday() == 6:
        log.info("Sunday — skipping.")
        return

    log.info(f"{'='*60}")
    log.info(f"Daily batch send — {now.strftime('%A %d/%m/%Y %H:%M')}")
    log.info(f"{'='*60}")

    # Load all emails
    with open(EMAILS_PATH, 'r', encoding='utf-8') as f:
        all_emails = json.load(f)

    # Load progress
    progress = load_progress()
    sent_set = set(progress["sent_emails"])

    # Filter to unsent only
    unsent = [e for e in all_emails if e["email"] not in sent_set]
    log.info(f"Total: {len(all_emails)} | Already sent: {len(sent_set)} | Remaining: {len(unsent)}")

    if not unsent:
        log.info("All emails have been sent! Campaign complete.")
        return

    # Take today's batch
    batch = unsent[:BATCH_SIZE]
    log.info(f"Today's batch: {len(batch)} emails")

    # Schedule each email for 3PM today, staggered by 3 min
    sender = CampaignSender()
    base_time = now.replace(hour=15, minute=0, second=0, microsecond=0)

    # If it's already past 3PM, send immediately (no scheduled_at)
    past_3pm = now >= base_time

    sent_count = 0
    failed_count = 0

    for i, email_data in enumerate(batch):
        to_email = email_data['email']
        to_name = email_data['name']
        subject = email_data['generated_subject']
        body = email_data['generated_body']

        if past_3pm:
            send_time = None
            time_str = "NOW"
        else:
            send_time = base_time + timedelta(minutes=i * STAGGER_MINUTES)
            send_time_utc = send_time.astimezone(ZoneInfo("UTC"))
            time_str = send_time.strftime("%H:%M")
            send_time = send_time_utc

        log.info(f"[{i+1}/{len(batch)}] {to_name} ({to_email}) — {time_str}")

        success = sender.send_email(to_email, to_name, subject, body, scheduled_at=send_time)

        if success:
            log.info(f"  OK")
            sent_count += 1
            progress["sent_emails"].append(to_email)
        else:
            log.info(f"  FAILED")
            failed_count += 1

    progress["last_run"] = now.isoformat()
    save_progress(progress)

    log.info(f"")
    log.info(f"Batch done: {sent_count} sent, {failed_count} failed")
    log.info(f"Total progress: {len(progress['sent_emails'])}/{len(all_emails)}")
    log.info(f"{'='*60}")


if __name__ == "__main__":
    main()
