from typing import List, Dict, Tuple

from bot.pricing_utils import parse_brl_to_int

ALERT_BUCKET_RULES = {
    "imperdivel": {
        "max_price_ratio_ceiling": 0.80,
        "max_price_ratio_avg": 0.85,
        "max_duration_min": 600,
        "max_stops": 1,
        "allow_next_day": False,
    },
    "bom": {
        "max_price_ratio_ceiling": 0.90,
        "max_price_ratio_avg": 0.95,
        "max_duration_min": 720,
        "max_stops": 1,
        "allow_next_day": True,
    },
    "ok": {
        "max_price_ratio_ceiling": 1.00,
        "max_price_ratio_avg": 1.05,
        "max_duration_min": 840,
        "max_stops": 2,
        "allow_next_day": True,
    },
}


def _price_int_from_offer(offer: Dict) -> int | None:
    if offer.get("price_int") is not None:
        return offer.get("price_int")
    price = offer.get("price")
    if isinstance(price, int):
        return price
    if isinstance(price, str):
        p = parse_brl_to_int(price)
        return None if p == -1 else p
    return None


def classify_alert_bucket(offer: Dict, *, ceiling: int, avg_price: float | None = None) -> tuple[str, Dict]:
    """
    Classifica a oferta em buckets de alerta: imperdivel, bom, ok, ignorar.

    Regras objetivas baseadas em:
      - preço vs teto
      - preço vs média histórica (se disponível)
      - duração, escalas e next_day
    """
    price = _price_int_from_offer(offer)
    duration_min = offer.get("duration_min") or 9999
    stops = offer.get("stops") or 0
    next_day = bool(offer.get("next_day"))

    if price is None or ceiling <= 0:
        return "ignorar", {"reason": "no_price_or_ceiling"}
    if price > ceiling:
        return "ignorar", {"reason": "above_ceiling"}

    price_ratio_ceiling = price / ceiling
    price_ratio_avg = (price / avg_price) if avg_price else None

    for bucket in ("imperdivel", "bom", "ok"):
        rules = ALERT_BUCKET_RULES[bucket]
        if price_ratio_ceiling > rules["max_price_ratio_ceiling"]:
            continue
        if price_ratio_avg is not None and price_ratio_avg > rules["max_price_ratio_avg"]:
            continue
        if duration_min > rules["max_duration_min"]:
            continue
        if stops > rules["max_stops"]:
            continue
        if (not rules["allow_next_day"]) and next_day:
            continue
        return bucket, {
            "price_ratio_ceiling": round(price_ratio_ceiling, 3),
            "price_ratio_avg": round(price_ratio_avg, 3) if price_ratio_avg is not None else None,
            "duration_min": duration_min,
            "stops": stops,
            "next_day": next_day,
        }

    return "ignorar", {
        "price_ratio_ceiling": round(price_ratio_ceiling, 3),
        "price_ratio_avg": round(price_ratio_avg, 3) if price_ratio_avg is not None else None,
        "duration_min": duration_min,
        "stops": stops,
        "next_day": next_day,
    }

def day_bucket(dep_time: str) -> str:
    """
    Classifica horário de saída em 'manha', 'tarde', 'noite'.
    dep_time: string tipo '06:00', '15:30', etc.
    """
    if not dep_time or not isinstance(dep_time, str):
        return "qualquer"
    try:
        h, m = map(int, dep_time.split(":"))
        mins = h * 60 + m
    except Exception:
        return "qualquer"
    if mins < 12 * 60:
        return "manha"
    if mins < 18 * 60:
        return "tarde"
    return "noite"


def pick_best_3_buckets(flights: List[Dict], ceiling: int) -> List[Dict]:
    """
    Escolhe até 3 voos: 1 manhã, 1 tarde, 1 noite.
    Critério: menor preço dentro do bucket, respeitando teto.
    """
    buckets = {"manha": None, "tarde": None, "noite": None}
    filtered: List[Tuple[int, Dict]] = []
    for f in flights:
        p = parse_brl_to_int(f.get("price", ""))
        if p == -1:
            continue
        if p > ceiling:
            continue
        filtered.append((p, f))
    filtered.sort(key=lambda x: x[0])
    for p, f in filtered:
        b = day_bucket(f.get("dep_time", ""))
        if b in buckets and buckets[b] is None:
            buckets[b] = (p, f)
        if all(v is not None for v in buckets.values()):
            break
    result: List[Dict] = []
    for b in ["manha", "tarde", "noite"]:
        if buckets[b] is not None:
            result.append(buckets[b][1])
    if not result and filtered:
        result = [filtered[0][1]]
    return result
