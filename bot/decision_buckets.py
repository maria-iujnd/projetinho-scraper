from typing import List, Dict, Tuple

from bot.pricing_utils import parse_brl_to_int

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
