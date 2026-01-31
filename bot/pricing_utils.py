def brl(n: int) -> str:
    """Formata número inteiro como moeda brasileira sem símbolo."""
    return f"{n:,}".replace(",", ".")

def parse_brl_to_int(price_text: str) -> int:
    """Converte texto de preço (ex: 'R$ 1.234') para inteiro (ex: 1234)."""
    import re
    if not price_text:
        return -1
    cleaned = price_text.replace(".", "").replace("\xa0", " ")
    nums = re.findall(r"\d+", cleaned)
    if not nums:
        return -1
    return int("".join(nums))
