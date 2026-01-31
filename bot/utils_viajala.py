from __future__ import annotations

import re


def normalize_airline(name: str | None) -> str | None:
    if not name:
        return None
    value = name.strip().upper()
    if not value:
        return None
    mapping = {
        "G3": "GOL",
        "GOL": "GOL",
        "AZUL": "AZUL",
        "AD": "AZUL",
        "LATAM": "LATAM",
        "LA": "LATAM",
        "JJ": "LATAM",
        "TAM": "LATAM",
    }
    return mapping.get(value, value)


def is_time_hhmm(s: str | None) -> bool:
    if not s:
        return False
    s = s.strip()
    if not re.match(r"^\d{2}:\d{2}$", s):
        return False
    try:
        hh, mm = s.split(":", 1)
        h = int(hh)
        m = int(mm)
    except Exception:
        return False
    return 0 <= h <= 23 and 0 <= m <= 59


def parse_duration_min(text: str) -> int | None:
    if not text:
        return None
    t = text.strip().lower()

    match = re.search(r"(\d{1,2})h(\d{2})", t)
    if match:
        return int(match.group(1)) * 60 + int(match.group(2))

    match = re.search(r"(\d{1,2})h\s*(\d{1,2})\s*min", t)
    if match:
        return int(match.group(1)) * 60 + int(match.group(2))

    match = re.search(r"(\d{1,2})h", t)
    hours = int(match.group(1)) if match else 0

    match = re.search(r"(\d{1,2})\s*min", t)
    minutes = int(match.group(1)) if match else 0

    total = hours * 60 + minutes
    return total if total > 0 else None


def parse_price_int(text: str) -> int | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d,\.]", "", text)
    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "")
            cleaned = cleaned.split(",", 1)[0]
        else:
            cleaned = cleaned.replace(",", "")
            cleaned = cleaned.split(".", 1)[0]
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts[-1]) == 2:
            cleaned = "".join(parts[:-1])
        else:
            cleaned = "".join(parts)
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts[-1]) == 2:
            cleaned = "".join(parts[:-1])
        else:
            cleaned = "".join(parts)

    return int(cleaned) if cleaned.isdigit() else None
