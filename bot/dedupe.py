import hashlib
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def make_offer_fingerprint(offer: Dict) -> str:
    """
    Build a stable fingerprint for dedupe, including provider.

    Key order:
      provider|origin|destination|depart_date|dep_time|arr_time|airline|duration_min|price|link
    """
    provider = (offer.get("provider") or "").upper()
    origin = (offer.get("origin") or offer.get("origin_code") or "").upper()
    destination = (offer.get("destination") or offer.get("dest_code") or "").upper()
    depart_date = offer.get("depart_date") or ""
    dep_time = offer.get("dep_time") or ""
    arr_time = offer.get("arr_time") or ""
    airline = (offer.get("airline") or "").upper()
    duration_min = offer.get("duration_min") or ""
    price = offer.get("price")
    if price is None:
        price = offer.get("price_int")
    price = price if price is not None else ""
    link = offer.get("share_link") or offer.get("link") or ""

    parts = [
        provider,
        origin,
        destination,
        str(depart_date or ""),
        str(dep_time or ""),
        str(arr_time or ""),
        airline,
        str(duration_min or ""),
        str(price or ""),
        str(link or ""),
    ]
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()

def make_offer_id(offer: Dict) -> str:
    """
    Gera um ID forte e estável para o voo/oferta.
    Usa fingerprint estável (inclui provider e campos principais).
    """
    h = make_offer_fingerprint(offer)
    return f"F_{h}"

def make_dedupe_key(offer_id: str, *, channel: str, kind: str) -> str:
    """
    Monta dedupe_key: KIND|CHANNEL|<offer_id>
    """
    return f"{kind}|{channel}|{offer_id}"
