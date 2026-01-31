
# --- Função utilitária para datas de partida ---
import datetime
from typing import List

def smart_depart_dates(start: datetime.date, days: int) -> List[str]:
    """
    Gera uma lista de datas (YYYY-MM-DD) a partir de uma data inicial e um número de dias.
    Prioriza quintas, sextas e sábados, mas retorna todas por enquanto.
    """
    result = []
    for i in range(days):
        d = start + datetime.timedelta(days=i)
        result.append(d.strftime("%Y-%m-%d"))
    return result

import datetime
import re

def to_iso_date(date_str: str) -> str:
    """
    Aceita 'YYYY-MM-DD' ou 'DD/MM/YYYY'. Retorna 'YYYY-MM-DD' ou levanta ValueError.
    """
    date_str = date_str.strip()
    # ISO direto
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            return dt.strftime("%Y-%m-%d")
        except Exception:
            raise ValueError(f"Data inválida: {date_str}")
    # BR
    if re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
        try:
            dt = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
            return dt.strftime("%Y-%m-%d")
        except Exception:
            raise ValueError(f"Data inválida: {date_str}")
    raise ValueError(f"Formato de data não suportado: {date_str}")

def to_br_date(iso_date: str) -> str:
    """'YYYY-MM-DD' -> 'DD/MM/YYYY'"""
    try:
        dt = datetime.datetime.strptime(iso_date, "%Y-%m-%d").date()
        return dt.strftime("%d/%m/%Y")
    except Exception:
        raise ValueError(f"Data inválida: {iso_date}")

def normalize_date(date_str: str) -> tuple[str, str]:
    """Retorna (iso, br)"""
    iso = to_iso_date(date_str)
    br = to_br_date(iso)
    return iso, br

# Compatibilidade antiga
def format_date_br(iso_yyyy_mm_dd: str) -> str:
    return to_br_date(iso_yyyy_mm_dd)
