from urllib.parse import quote

def build_google_flights_url_ow(origin_iata: str, dest_iata: str, depart_iso: str, sort_by_price: bool = True) -> str:
    """
    Monta URL de pesquisa do Google Flights usando query natural.
    Exemplo de query: "Flights to GRU from REC on 2026-02-15 oneway".
    """
    query = f"Flights to {dest_iata} from {origin_iata} on {depart_iso} oneway"
    q = quote(query)
    return (
        "https://www.google.com/travel/flights"
        f"?hl=pt-BR&gl=BR&curr=BRL&q={q}"
    )
