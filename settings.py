#!/usr/bin/env python3
"""Central configuration and path helpers.
Do not import project modules here to avoid circular imports.
"""
import os
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Scoped path helpers ---
def _scoped_name(base: str, scope: Optional[str], ext: str) -> str:
    if scope:
        return f"{base}_{scope}{ext}"
    return f"{base}{ext}"

def queue_file(scope: Optional[str] = None) -> str:
    return os.path.join(BASE_DIR, _scoped_name("queue_messages", scope, ".json"))

def db_file(scope: Optional[str] = None) -> str:
    return os.path.join(BASE_DIR, _scoped_name("kiwi_state", scope, ".db"))

def kiwi_profile_dir(scope: Optional[str] = None) -> str:
    name = f"chrome_profile_kiwi{('_' + scope) if scope else ''}"
    return os.path.join(BASE_DIR, name)

def whatsapp_profile_dir(scope: Optional[str] = None) -> str:
    name = f"chrome_profile_whatsapp{('_' + scope) if scope else ''}"
    return os.path.join(BASE_DIR, name)

# Perfis Chrome em pasta temporária cross-platform
import tempfile
def chrome_profile_dir(scope: Optional[str] = None) -> str:
    name = f"chrome_profile{('_' + scope) if scope else ''}"
    return os.path.join(tempfile.gettempdir(), name)

# --- Runtime constants ---
# Limits and delays
MAX_MESSAGES_PER_RUN = 20
MAX_TO_SEND = 25
SEND_DELAY_MIN_SEC = 90
SEND_DELAY_MAX_SEC = 180

# Cooldowns
COOLDOWN_GOOD_DAYS = 5
COOLDOWN_BAD_HOURS = 36
COOLDOWN_NODATA_HOURS = 72

# Anti-spam policy
DAILY_ROUTE_LIMIT = 2
ROUTE_MIN_INTERVAL_SEC = 3600
ALERT_COOLDOWN_HOURS = 24
RECORD_BREAK_PCT = 0.10

# WhatsApp defaults
DEFAULT_GROUP_NAME = "sinais RECIFE"

# Other sensible defaults
MAX_RESULTS_TO_SCRAPE = 10

# Expose a small mapping for backward compatibility if needed
DEFAULTS = {
    "MAX_MESSAGES_PER_RUN": MAX_MESSAGES_PER_RUN,
    "MAX_TO_SEND": MAX_TO_SEND,
    "SEND_DELAY_MIN_SEC": SEND_DELAY_MIN_SEC,
    "SEND_DELAY_MAX_SEC": SEND_DELAY_MAX_SEC,
}
