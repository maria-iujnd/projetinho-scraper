"""
Decision Engine: centraliza regras de negócio, dedupe, prioridade, seleção de buckets/top N.
"""

# Wrapper para compatibilidade
class DecisionEngine:
    @staticmethod
    def evaluate_offer_batch(*, flights, min_price, ceiling, origin, dest, depart_date, queue, state_store):
        return evaluate_offer_batch(
            flights=flights,
            min_price=min_price,
            ceiling=ceiling,
            origin=origin,
            dest=dest,
            depart_date=depart_date,
            queue=queue,
            state_store=state_store
        )
from bot.selector import pick_best_3_buckets
from bot.prioritizer import compute_priority_score
from bot.message_builder import build_grouped_message
from bot.queue_store import is_in_queue
from bot.dedupe import make_offer_id, make_dedupe_key
from bot.pricing_utils import parse_brl_to_int
import logging
from dataclasses import dataclass
from typing import Optional
from copy import deepcopy
import re

@dataclass
class DecisionResult:
    should_enqueue: bool
    reason: str
    dedupe_key: Optional[str]
    priority: int
    message_text: Optional[str]


def _price_int_from_offer(offer: dict) -> Optional[int]:
    if offer.get("price_int") is not None:
        return offer.get("price_int")
    price = offer.get("price")
    if isinstance(price, int):
        return price
    if isinstance(price, str):
        return parse_brl_to_int(price)
    return None


def _normalize_duration_bucket(duration_min: Optional[int]) -> Optional[int]:
    if duration_min is None:
        return None
    try:
        return int(round(duration_min / 5) * 5)
    except Exception:
        return duration_min


def fingerprint_offer(o: dict) -> str:
    provider = o.get("provider") or ""
    origin = o.get("origin") or ""
    dest = o.get("destination") or o.get("dest") or ""
    depart_date = o.get("depart_date") or ""
    dep = o.get("dep_time") or ""
    arr = o.get("arr_time") or ""
    next_day = "1" if o.get("next_day") else "0"
    stops = str(o.get("stops") if o.get("stops") is not None else "")
    airline = (o.get("airline") or "").strip().upper()
    dur = _normalize_duration_bucket(o.get("duration_min"))
    dur = str(dur if dur is not None else "")
    return "|".join([provider, origin, dest, depart_date, dep, arr, next_day, dur, stops, airline])


def merge_offer(a: dict, b: dict) -> dict:
    out = deepcopy(a)
    pa, pb = _price_int_from_offer(a), _price_int_from_offer(b)
    if pa is None:
        out["price"] = b.get("price")
        out["price_int"] = pb
    elif pb is not None:
        out["price"] = min(pa, pb)
        out["price_int"] = min(pa, pb)

    if not out.get("link") and b.get("link"):
        out["link"] = b.get("link")

    if (not out.get("partner")) and b.get("partner"):
        out["partner"] = b.get("partner")
    if out.get("partner") and b.get("partner"):
        if "oficial" not in out["partner"].lower() and "oficial" in b["partner"].lower():
            out["partner"] = b.get("partner")

    ea = a.get("extra_offers") or a.get("extra_offers_count") or 0
    eb = b.get("extra_offers") or b.get("extra_offers_count") or 0
    out["extra_offers"] = max(ea, eb)

    ta = a.get("raw_text") or ""
    tb = b.get("raw_text") or ""
    if len(tb) > len(ta):
        out["raw_text"] = tb
    return out


def compute_confidence(o: dict) -> int:
    c = 0
    if _price_int_from_offer(o) is not None:
        c += 40
    if o.get("dep_time") and o.get("arr_time"):
        c += 15
    if isinstance(o.get("duration_min"), int) and o.get("duration_min") > 0:
        c += 15
    if o.get("airline"):
        c += 10
    if o.get("link"):
        c += 10
    extra = int(o.get("extra_offers") or o.get("extra_offers_count") or 0)
    c += min(extra, 10)
    return max(0, min(100, c))


def compute_rank_score(o: dict) -> float:
    price = _price_int_from_offer(o)
    dur = o.get("duration_min") or 9999
    stops = o.get("stops") or 0
    extra = int(o.get("extra_offers") or o.get("extra_offers_count") or 0)
    conf = o.get("confidence", compute_confidence(o))
    if price is not None:
        return float(price) + 0.5 * float(dur) + 180.0 * float(stops) - 2.0 * min(extra, 10)
    return 1_000_000.0 - conf * 100.0 - float(dur)


def dedupe_and_rank(offers: list[dict]) -> list[dict]:
    bucket: dict[str, dict] = {}
    for o in offers:
        o = dict(o)
        o["confidence"] = compute_confidence(o)
        key = fingerprint_offer(o)
        if key not in bucket:
            bucket[key] = o
        else:
            bucket[key] = merge_offer(bucket[key], o)
            bucket[key]["confidence"] = compute_confidence(bucket[key])
    deduped = list(bucket.values())
    deduped.sort(key=compute_rank_score)
    return deduped

def evaluate_offer_batch(*, flights, min_price, ceiling, origin, dest, depart_date, queue, state_store):
    logger = logging.getLogger("kiwi_bot")
    if not flights:
        return DecisionResult(False, "NO_FLIGHTS", None, 0, None)
    ranked = dedupe_and_rank(flights)
    if not ranked:
        return DecisionResult(False, "NO_FLIGHTS", None, 0, None)
    min_price_local = _price_int_from_offer(ranked[0])
    if min_price_local is None or min_price_local <= 0:
        return DecisionResult(False, "NO_PRICE", None, 0, None)
    if min_price_local > ceiling:
        return DecisionResult(False, "ABOVE_CEILING", None, 0, None)
    best = pick_best_3_buckets(ranked, ceiling)
    if not best:
        return DecisionResult(False, "NO_BEST_BUCKETS", None, 0, None)
    # ID forte
    offer = dict(best[0])
    offer["depart_date"] = depart_date
    route_key = f"{origin}-{dest}"
    trip_type = "RT_USA" if "EUA" in dest or "USA" in dest or "NYC" in dest else "OW"
    score, meta = compute_priority_score(
        price=min_price_local,
        ceiling=ceiling,
        route_key=route_key,
        trip_type=trip_type,
        state_store=state_store
    )
    priority = score
    offer_id = make_offer_id(offer)
    dedupe_key = make_dedupe_key(offer_id, channel="WHATSAPP", kind="ALERT")
    # Dedupe fila
    if is_in_queue(queue, dedupe_key):
        logger.debug(f"[DEDUPE] skip reason=DUPLICATE_QUEUE key={dedupe_key}")
        return DecisionResult(False, "DUPLICATE_QUEUE", dedupe_key, priority, None)
    # Dedupe TTL
    DEDUP_TTL_HOURS = 24
    ttl_seconds = DEDUP_TTL_HOURS * 3600
    if hasattr(state_store, "was_seen_recently") and state_store.was_seen_recently(dedupe_key, ttl_seconds):
        logger.debug(f"[DEDUPE] skip reason=DUPLICATE_TTL key={dedupe_key}")
        return DecisionResult(False, "DUPLICATE_TTL", dedupe_key, priority, None)
    logger.info(f"[PRIORITY] score={score} meta={meta}")
    # Grava sample para histórico
    if hasattr(state_store, "record_sample"):
        try:
            state_store.record_sample(route_key, trip_type, min_price_local)
        except Exception:
            pass
    message_text = build_grouped_message(
        origin,
        dest,
        depart_date,
        best,
        min_price_local,
        ceiling
    )
    return DecisionResult(True, "OK", dedupe_key, priority, message_text)
