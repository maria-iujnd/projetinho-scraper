"""Format flight offers into grouped alert messages.

Groups by provider + origin + destination + depart_date and outputs a compact,
readable message per group.
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Any

from bot.date_utils import format_date_br
from bot.pricing_utils import brl


def _format_duration(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    hours = minutes // 60
    mins = minutes % 60
    if hours and mins:
        return f"{hours}h{mins:02d}"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


def _price_int(offer: Dict[str, Any]) -> int | None:
    price = offer.get("price")
    if isinstance(price, int):
        return price
    if isinstance(price, str):
        digits = "".join(ch for ch in price if ch.isdigit())
        return int(digits) if digits else None
    price_int = offer.get("price_int")
    return price_int if isinstance(price_int, int) else None


def _group_key(offer: Dict[str, Any]) -> Tuple[str, str, str, str]:
    provider = (offer.get("provider") or "").lower()
    origin = (offer.get("origin") or offer.get("origin_code") or "").upper()
    destination = (offer.get("destination") or offer.get("dest_code") or "").upper()
    depart_date = offer.get("depart_date") or ""
    return provider, origin, destination, depart_date


def format_flight_alert(offers: List[Dict[str, Any]]) -> List[str]:
    groups: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = {}
    for offer in offers:
        key = _group_key(offer)
        groups.setdefault(key, []).append(offer)

    messages: List[str] = []

    for (provider, origin, destination, depart_date), items in groups.items():
        items_sorted = sorted(
            items,
            key=lambda o: (_price_int(o) is None, _price_int(o) or 0),
        )[:5]

        date_br = format_date_br(depart_date) if depart_date else "-"
        header = f"🔔 Passagens {origin} → {destination} | {date_br}"

        lines: List[str] = [header]
        for offer in items_sorted:
            dep = offer.get("dep_time")
            arr = offer.get("arr_time")
            duration_min = offer.get("duration_min")
            duration_text = _format_duration(duration_min) if duration_min else None
            airline = offer.get("airline")
            price = _price_int(offer)

            if dep or arr:
                time_part = f"{dep or '-'}–{arr or '-'}"
                if duration_text:
                    lines.append(f"🕒 {time_part} | ⏱ {duration_text}")
                else:
                    lines.append(f"🕒 {time_part}")

            if airline:
                lines.append(f"🏷 {airline}")

            if price is not None:
                lines.append(f"💰 R$ {brl(price)}")

        link = None
        for offer in items_sorted:
            link = offer.get("link")
            if link:
                break
        if link:
            lines.append(f"🔗 Abrir busca: {link}")

        messages.append("\n".join(lines))

    return messages
