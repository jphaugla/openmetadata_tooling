#!/usr/bin/env python3
"""
export_audit_logs.py

Pulls audit log entries from OpenMetadata/Collate via /v1/audit/logs
and uploads them to S3 as JSONL.

  s3://<S3_BUCKET>/<S3_KEY_PREFIX>audit_logs/audit_logs_<timestamp>.jsonl

⚠️  The /v1/audit/logs endpoint requires a token with AuditLogs permission.
    The ingestion-bot does NOT have this by default. Use AUDIT_LOG_TOKEN
    set to a personal access token or an admin bot token that has been
    granted the AuditLogs permission in:
      Settings → Access Control → Roles

State is tracked in STATE_DIR/state_audit_logs.txt so each run picks
up only new entries since the last successful run.

Usage:
  python export_audit_logs.py                        # incremental (default)
  python export_audit_logs.py --all                  # from epoch 0
  python export_audit_logs.py --start-date 2026-06-01
  python export_audit_logs.py --skip-state           # don't advance state
  python export_audit_logs.py --dry-run              # print, don't upload

Environment variables:
  AUDIT_LOG_TOKEN   JWT with AuditLogs permission (required)
  API_BASE          e.g. https://your-org.getcollate.io/api/v1 (required)
  S3_BUCKET         Destination S3 bucket (required unless --dry-run)
  S3_KEY_PREFIX     Optional folder prefix inside the bucket (default: "")
  STATE_DIR         Where to store the state file (default: current dir)
  DRY_RUN           Set to "true" to skip S3 upload
"""
import os
import sys
import json
import argparse
import urllib.parse
import requests
from datetime import datetime, timezone, timedelta

import boto3

# ── Config ────────────────────────────────────────────────────────────────────
AUDIT_LOG_TOKEN = os.getenv("AUDIT_LOG_TOKEN")
API_BASE        = os.getenv("API_BASE", "").rstrip("/")
S3_BUCKET       = os.getenv("S3_BUCKET")
S3_KEY_PREFIX   = os.getenv("S3_KEY_PREFIX", "").rstrip("/")
S3_KEY_PREFIX   = S3_KEY_PREFIX + "/" if S3_KEY_PREFIX else ""
STATE_DIR       = os.getenv("STATE_DIR", ".")
DRY_RUN         = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")

STATE_FILE            = os.path.join(STATE_DIR, "state_audit_logs.txt")
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


# ── HTTP helper ───────────────────────────────────────────────────────────────

def make_request(endpoint: str) -> requests.Response:
    url     = f"{API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {AUDIT_LOG_TOKEN}",
        "Content-Type":  "application/json",
    }
    print(f"DEBUG: [GET] {url}")
    try:
        return requests.get(url, headers=headers, timeout=30)
    except Exception as e:
        print(f"❌ Request error [{url}]: {e}")
        return None


# ── S3 upload ─────────────────────────────────────────────────────────────────

def upload_to_s3(logs: list, run_time: datetime) -> bool:
    if not logs:
        print("ℹ️  No audit log entries to upload.")
        return True

    filename = f"audit_logs_{run_time.strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    s3_key   = f"{S3_KEY_PREFIX}audit_logs/{filename}"
    body     = ("\n".join(json.dumps(e) for e in logs) + "\n").encode("utf-8")

    if DRY_RUN:
        print(f"[dry-run] Would upload {len(logs)} audit log entries "
              f"({len(body):,} bytes) → s3://{S3_BUCKET}/{s3_key}")
        print(f"Sample: {json.dumps(logs[0], indent=2)[:400]}...")
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
        print(f"✅ Uploaded {len(logs)} audit log entries → s3://{S3_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        print(f"❌ S3 upload failed: {e}")
        return False


# ── Audit log fetch ───────────────────────────────────────────────────────────

def fetch_audit_logs(since_ms: int, now_ms: int) -> list:
    """
    Pull all audit log entries between since_ms and now_ms.
    Uses cursor-based pagination (after/before) with batches of 100.
    """
    all_logs = []
    after    = None
    limit    = 100

    while True:
        params = {
            "startTs": since_ms,
            "endTs":   now_ms,
            "limit":   limit,
        }
        if after:
            params["after"] = after

        resp = make_request(f"/audit/logs?{urllib.parse.urlencode(params)}")

        if resp is None:
            print("❌ No response from /v1/audit/logs (connection error).")
            break

        if resp.status_code == 403:
            print(
                "⛔ 403 Forbidden — AUDIT_LOG_TOKEN does not have AuditLogs permission.\n"
                "   Go to Settings → Access Control → Roles and grant AuditLogs\n"
                "   to the bot or user whose token is set in AUDIT_LOG_TOKEN."
            )
            break

        if resp.status_code != 200:
            print(f"❌ /v1/audit/logs returned {resp.status_code}: {resp.text}")
            break

        body  = resp.json()
        page  = body.get("data", [])
        all_logs.extend(page)

        paging = body.get("paging", {})
        after  = paging.get("after")
        if not after or not page:
            break

    return all_logs


# ── Entry point ───────────────────────────────────────────────────────────────

def resolve_start(args) -> datetime:
    if args.all:
        print("📁 Mode: ALL historical audit logs (from 1970-01-01)")
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
        description="Export OpenMetadata audit logs to S3."
    )
    parser.add_argument(
        "--start-date",
        help="ISO 8601 start (YYYY-MM-DD or full timestamp). Overrides state file.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Export all audit logs from the beginning of time.",
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

    # Validate required config
    if not AUDIT_LOG_TOKEN:
        print("❌ AUDIT_LOG_TOKEN is not set. See script docstring for details.")
        sys.exit(1)
    if not API_BASE:
        print("❌ API_BASE is not set.")
        sys.exit(1)
    if not S3_BUCKET and not DRY_RUN:
        print("❌ S3_BUCKET is not set. Use --dry-run for local testing.")
        sys.exit(1)

    now      = datetime.now(timezone.utc)
    now_ms   = int(now.timestamp() * 1000)
    start_dt = resolve_start(args)
    start_ms = int(start_dt.timestamp() * 1000)

    print(f"🔍 Fetching audit logs from {start_dt.isoformat()} "
          f"to {now.isoformat()}")

    logs = fetch_audit_logs(start_ms, now_ms)
    print(f"📊 Retrieved: {len(logs)} audit log entries")

    ok = upload_to_s3(logs, now)

    if ok and not args.skip_state:
        save_state(now)
    elif not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
