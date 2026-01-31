def compute_priority_score(*, price: int, ceiling: int, route_key: str, trip_type: str, state_store):
    """
    Retorna (score, meta) para priorização inteligente.
    meta inclui razões: desconto_vs_teto, below_avg, samples, avg, etc.
    """
    meta = {}
    if ceiling <= 0 or price <= 0:
        return 0, {"discount_vs_ceiling": 0.0, "invalid": True}
    # Score base: desconto relativo ao teto
    discount_vs_ceiling = max(0, (ceiling - price) / ceiling)
    base = int(discount_vs_ceiling * 600)
    meta["discount_vs_ceiling"] = discount_vs_ceiling
    meta["base"] = base
    # Componente histórico (ex: RT EUA)
    bonus = 0
    stats = None
    try:
        stats = state_store.get_stats(route_key, trip_type)
    except Exception:
        stats = None
    if stats and stats.get("n", 0) >= 10 and stats.get("avg"):
        avg = stats["avg"]
        n = stats["n"]
        below_avg = (avg - price) / avg if avg > 0 else 0
        meta["below_avg"] = below_avg
        meta["avg"] = avg
        meta["n"] = n
        if trip_type == "RT_USA" and below_avg >= 0.15:
            bonus = 300
            meta["alert_below_avg"] = True
        elif trip_type == "RT_USA":
            bonus = int(150 * max(0, below_avg) / 0.15)  # até 150 se quase 15%
            meta["alert_below_avg"] = False
    score = base + bonus
    meta["score"] = score
    return score, meta
