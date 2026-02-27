"""Cron-ready runner for data sync + AI alerts.

Example crontab entry (every 6 hours):
0 */6 * * * /path/to/python /path/to/backend/run_scheduler.py
"""

from __future__ import annotations

import json

from ai_alert_engine import generate_ai_alerts
from data_pipeline import sync_all_if_due
from db import init_db


def main() -> None:
    init_db()
    result = {
        "sync": sync_all_if_due(),
        "alerts": generate_ai_alerts(force=False),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
