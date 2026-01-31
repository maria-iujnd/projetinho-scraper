import time
from bot.send_schedule import is_within_any_window, parse_windows
from bot.config import SEND_TZ, SEND_WINDOWS, MAX_PER_HOUR_PER_GROUP, MIN_SECONDS_BETWEEN_MESSAGES_PER_GROUP
import state_store

_windows = parse_windows(SEND_WINDOWS)

def can_send_now(group_name):
    now = state_store.now_dt()
    if not is_within_any_window(now, _windows, SEND_TZ):
        return False, "OUTSIDE_WINDOW"
    sent_timestamps = state_store.get_group_send_timestamps(group_name, window_seconds=3600)
    if len(sent_timestamps) >= MAX_PER_HOUR_PER_GROUP:
        return False, f"GROUP_HOURLY_LIMIT"
    last_sent = state_store.get_group_last_sent_ts(group_name)
    if last_sent and (now.timestamp() - last_sent) < MIN_SECONDS_BETWEEN_MESSAGES_PER_GROUP:
        wait = int(MIN_SECONDS_BETWEEN_MESSAGES_PER_GROUP - (now.timestamp() - last_sent))
        return False, f"GROUP_SPACING wait={wait}s"
    return True, "OK"
