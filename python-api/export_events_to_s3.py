#!/usr/bin/env python3
"""
export_events_to_s3.py

Pulls metadata change events from OpenMetadata/Collate via /v1/events
and uploads them to S3 as JSONL.

  s3://<S3_BUCKET>/<S3_KEY_PREFIX>change_events/events_<timestamp>.jsonl

State is tracked in STATE_DIR/state_change_events.txt so each run picks
up only new events since the last successful run.

Usage:
  python export_events_to_s3.py                        # incremental (default)
  python export_events_to_s3.py --all                  # from epoch 0
  python export_events_to_s3.py --start-date 2026-06-01
  python export_events_to_s3.py --skip-state           # don't advance state
  python export_events_to_s3.py --dry-run              # print, don't upload

Environment variables:
  TOKEN           OpenMetadata JWT (required)
  API_BASE        e.g. https://your-org.getcollate.io/api/v1 (required)
  S3_BUCKET       Destination S3 bucket (required unless --dry-run)
  S3_KEY_PREFIX   Optional folder prefix inside the bucket (default: "")
  STATE_DIR       Where to store the state file (default: current dir)
  DRY_RUN         Set to "true" to skip S3 upload
"""
import os
import sys
import json
import argparse
import urllib.parse
from datetime import datetime, timezone, timedelta

import boto3
from om_client import OpenMetadataClient

# ── Config ────────────────────────────────────────────────────────────────────
S3_BUCKET     = os.getenv("S3_BUCKET")
S3_KEY_PREFIX = os.getenv("S3_KEY_PREFIX", "").rstrip("/")
S3_KEY_PREFIX = S3_KEY_PREFIX + "/" if S3_KEY_PREFIX else ""
STATE_DIR     = os.getenv("STATE_DIR", ".")
DRY_RUN       = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")

STATE_FILE            = os.path.join(STATE_DIR, "state_change_events.txt")
DEFAULT_LOOKBACK_DAYS = 3

# ── State helpers ─────────────────────────────────────────────────────────────

def load_state(fallback: datetime) -> datetime:
    """Return the last-run datetime, or fallback if the state file is absent."""
    if os.path.exists(STATE_FILE):
        try:
            raw = open(STATE_FILE).read().strip()
            if raw:
                return datetime.fromisoformat(
                    raw.replace("Z", "+00:00")
                ).astimezone(timezone.utc)
        except Exception as e:
            print(f"⚠️  Could not read state file: {e}. Using fallback.")
    return fallback


def save_state(dt: datetime):
    if DRY_RUN:
        print(f"   [dry-run] Would save state → {STATE_FILE}: {dt.isoformat()}")
        return
    with open(STATE_FILE, "w") as f:
        f.write(dt.isoformat())
    print(f"   💾 State saved → {STATE_FILE}: {dt.isoformat()}")


# ── S3 upload ─────────────────────────────────────────────────────────────────

def upload_to_s3(events: list, run_time: datetime) -> bool:
    if not events:
        print("ℹ️  No events to upload.")
        return True

    filename = f"events_{run_time.strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    s3_key   = f"{S3_KEY_PREFIX}change_events/{filename}"
    body     = ("\n".join(json.dumps(e) for e in events) + "\n").encode("utf-8")

    if DRY_RUN:
        print(f"[dry-run] Would upload {len(events)} events "
              f"({len(body):,} bytes) → s3://{S3_BUCKET}/{s3_key}")
        print(f"Sample: {json.dumps(events[0], indent=2)[:400]}...")
        return True

    if not S3_BUCKET:
        print("❌ S3_BUCKET is not set.")
        return False

    try:
        boto3.client("s3").put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=body,
            ContentType="application/x-ndjson",
        )
        print(f"✅ Uploaded {len(events)} events → s3://{S3_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        print(f"❌ S3 upload failed: {e}")
        return False


# ── Event fetch ───────────────────────────────────────────────────────────────

def fetch_change_events(client: OpenMetadataClient, since_ms: int) -> list:
    """
    Pull all change events with timestamp > since_ms using the '*' wildcard
    so every entity type (including 'user') is covered.

    The API paginates by advancing the timestamp parameter to the last-seen
    value; there is no cursor token.
    """
    all_events = []
    ts = since_ms

    while True:
        params = {
            "entityCreated":  "*",
            "entityUpdated":  "*",
            "entityRestored": "*",
            "entityDeleted":  "*",
            "timestamp": ts,
        }
        resp = client._make_request(
            "GET", f"/events?{urllib.parse.urlencode(params)}"
        )
        if not resp or resp.status_code != 200:
            code = resp.status_code if resp else "no response"
            print(f"❌ /v1/events returned {code}: {resp.text if resp else ''}")
            break

        page = resp.json().get("data", [])
        if not page:
            break

        # Keep only events strictly newer than our window start
        new = [e for e in page if (e.get("timestamp") or 0) > since_ms]
        all_events.extend(new)

        # Advance timestamp for next page
        last_ts = page[-1].get("timestamp")
        if not last_ts or last_ts <= ts:
            break       # no forward progress
        if len(new) < len(page):
            break       # caught up to since_ms boundary
        ts = last_ts

    return all_events


# ── Entry point ───────────────────────────────────────────────────────────────

def resolve_start(args) -> datetime:
    if args.all:
        print("📁 Mode: ALL historical events (from 1970-01-01)")
        return datetime(1970, 1, 1, tzinfo=timezone.utc)

    if args.start_date:
        ds = args.start_date
        if len(ds) == 10:
            ds += "T00:00:00Z"
        try:
            dt = datetime.fromisoformat(ds.replace("Z", "+00:00")).astimezone(timezone.utc)
            print(f"📁 Mode: Custom start date → {dt.isoformat()}")
            return dt
        except ValueError as e:
            print(f"❌ Invalid --start-date '{args.start_date}': {e}")
            sys.exit(1)

    fallback = datetime.now(timezone.utc) - timedelta(days=DEFAULT_LOOKBACK_DAYS)
    dt = load_state(fallback)
    print(f"📁 Mode: Incremental from state → {dt.isoformat()}")
    return dt


def main():
    parser = argparse.ArgumentParser(
        description="Export OpenMetadata change events to S3."
    )
    parser.add_argument(
        "--start-date",
        help="ISO 8601 start (YYYY-MM-DD or full timestamp). Overrides state file.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Export all events from the beginning of time.",
    )
    parser.add_argument(
        "--skip-state", action="store_true",
        help="Do not update the state file after a successful run.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be uploaded without writing to S3.",
    )
    args = parser.parse_args()

    global DRY_RUN
    DRY_RUN = DRY_RUN or args.dry_run

    if not S3_BUCKET and not DRY_RUN:
        print("❌ S3_BUCKET is not set. Use --dry-run for local testing.")
        sys.exit(1)

    client   = OpenMetadataClient()
    now      = datetime.now(timezone.utc)
    start_dt = resolve_start(args)
    start_ms = int(start_dt.timestamp() * 1000)

    print(f"🔍 Fetching change events since {start_dt.isoformat()} "
          f"(epoch ms: {start_ms})")

    events = fetch_change_events(client, start_ms)
    print(f"📊 Retrieved: {len(events)} change events")

    ok = upload_to_s3(events, now)

    if ok and not args.skip_state:
        save_state(now)
    elif not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
