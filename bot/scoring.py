def compute_priority(min_price: int, ceiling: int) -> int:
    """Calcula prioridade simples: quanto menor o preço em relação ao teto, maior a prioridade."""
    if min_price <= 0 or ceiling <= 0:
        return 0
    return int(round((ceiling - min_price) / ceiling * 100))
