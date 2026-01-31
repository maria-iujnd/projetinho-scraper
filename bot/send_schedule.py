import pytz
from datetime import datetime, time as dtime

def parse_windows(windows_str):
    """
    Ex: "08:00-09:00,11:00-12:00" → [(start, end), ...] (as dtime)
    """
    result = []
    for win in windows_str.split(","):
        start, end = win.strip().split("-")
        h1, m1 = map(int, start.split(":"))
        h2, m2 = map(int, end.split(":"))
        result.append((dtime(h1, m1), dtime(h2, m2)))
    return result

def is_within_any_window(now, windows, tz):
    """
    now: datetime (naive ou aware)
    windows: [(start, end)] (dtime)
    tz: str (ex: 'America/Recife')
    """
    if now.tzinfo is None:
        tzinfo = pytz.timezone(tz)
        now = tzinfo.localize(now)
    else:
        now = now.astimezone(pytz.timezone(tz))
    now_t = now.time()
    for start, end in windows:
        if start <= now_t < end:
            return True
    return False
