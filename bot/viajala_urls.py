"""Utilities to build Viajala search URLs.

URL pattern:
    https://viajala.com.br/pesquisa-voos/{ORIG}-{DEST}/{DD-MM-YYYY}

Examples:
    build_viajala_url_ow("REC", "GRU", "2026-02-15")
    -> https://viajala.com.br/pesquisa-voos/REC-GRU/15-02-2026
"""

from __future__ import annotations


AIRPORT_TO_CITY = {
    "GRU": "SAO",
    "CGH": "SAO",
    "VCP": "SAO",
    "GIG": "RIO",
    "SDU": "RIO",
}


def normalize_city_or_airport(code: str) -> str:
    """Normalize a city or airport code for Viajala URLs.

    - Uppercases
    - Removes spaces
    - Leaves 3-letter airport codes or longer city codes as-is
    """
    if not code:
        return ""
    return code.replace(" ", "").upper()


def build_viajala_url_ow(origin: str, destination: str, depart_date: str) -> str:
    """Build a one-way Viajala search URL.

    Args:
        origin: City or airport code (e.g., "REC").
        destination: City or airport code (e.g., "GRU" or "SAO").
        depart_date: Date in YYYY-MM-DD format.

    Returns:
        Full Viajala search URL.
    """
    orig = normalize_city_or_airport(origin)
    dest = normalize_city_or_airport(destination)
    yyyy, mm, dd = depart_date.split("-", 2)
    date_br = f"{dd}-{mm}-{yyyy}"
    return f"https://viajala.com.br/pesquisa-voos/{orig}-{dest}/{date_br}"


def build_viajala_url_ow_with_fallback(origin: str, destination: str, depart_date: str) -> list[str]:
    """Build one-way Viajala URLs with metro-city fallback.

    Examples:
        build_viajala_url_ow_with_fallback("REC", "GRU", "2026-02-15")
        -> [
            "https://viajala.com.br/pesquisa-voos/REC-GRU/15-02-2026",
            "https://viajala.com.br/pesquisa-voos/REC-SAO/15-02-2026",
        ]
    """
    orig = normalize_city_or_airport(origin)
    dest = normalize_city_or_airport(destination)
    urls = [build_viajala_url_ow(orig, dest, depart_date)]
    fallback = AIRPORT_TO_CITY.get(dest)
    if fallback:
        fb_url = build_viajala_url_ow(orig, fallback, depart_date)
        if fb_url not in urls:
            urls.append(fb_url)
    return urls
