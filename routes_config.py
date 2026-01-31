__all__ = [
    'ORIGIN_IATA', 'DAILY_DEST_IATA', 'WEEKLY_BR_DEST_IATA', 'WEEKLY_INTL_DEST_IATA',
    'RT_USA_DEST_IATA', 'DESTINATION_GROUPS', 'PRICE_CEILINGS_OW', 'DEFAULT_PRICE_CEILING_OW',
    'PRICE_CEILINGS_RT', 'DEFAULT_PRICE_CEILING_RT', 'RT_NIGHTS_OPTIONS', 'get_price_ceiling_rt',
    'IATA_TO_SLUG', 'build_kiwi_url_ow', 'build_kiwi_url_rt',
    'build_viajala_url_ow', 'build_results_url_oneway', 'today_plus_days'
]
from bot.kiwi_urls import build_kiwi_url_ow, build_kiwi_url_rt
from bot.viajala_urls import build_viajala_url_ow
# routes_config.py

# Origem fixa
ORIGIN_IATA = "REC"

# ===============================
# DESTINOS
# ===============================

# 8 destinos diários
DAILY_DEST_IATA = [
    "SP", "RIO", "BSB", "SSA", "FOR", "CNF", "NAT"
]

# Capitais restantes (2x por semana)
WEEKLY_BR_DEST_IATA = [
    "AJU", "BEL", "BVB", "CGB", "CGR", "CWB", "FLN", "GYN",
    "JPA", "MCZ", "MAO", "MCP", "PMW", "POA", "PVH", "RBR",
    "SLZ", "THE", "VIX"
]

# Internacionais (1x por semana)
WEEKLY_INTL_DEST_IATA = [
    # EUA
    "MIA", "MCO", "JFK",
]

# --- RT EUA (ida e volta) ---
RT_USA_DEST_IATA = ["MIA", "MCO", "JFK"]

# Grupos de destinos
DESTINATION_GROUPS = {
    "SP": ["GRU", "CGH", "VCP"],
    "RIO": ["GIG", "SDU"],
}

# ===============================
# TETOS DE PREÇO (IDA)
# ===============================

PRICE_CEILINGS_OW = {
    # Daily
    "GRU": 650,
    "GIG": 650,
    "BSB": 700,
    "SSA": 500,
    "FOR": 550,
    "CNF": 700,
    "NAT": 450,
    "VCP": 650,
    "CGH": 650,
    "SDU": 650,

    # Weekly BR
    "AJU": 450,
    "BEL": 900,
    "BVB": 1200,
    "CGB": 950,
    "CGR": 1050,
    "CWB": 900,
    "FLN": 900,
    "GYN": 800,
    "JPA": 350,
    "MCZ": 380,
    "MAO": 1200,
    "MCP": 1300,
    "PMW": 1200,
    "POA": 1000,
    "PVH": 1300,
    "RBR": 1300,
    "SLZ": 850,
    "THE": 700,
    "VIX": 850,

    # Internacional
    "LIS": 2800,
    "MAD": 2900,
    "OPO": 2800,
    "SCL": 2500,
    "MIA": 2500,
    "MCO": 2400,
    "JFK": 2800,
}

DEFAULT_PRICE_CEILING_OW = 800

# ===== RT (IDA E VOLTA) =====
# Tetos RT (BRL) - MVP (ajuste com o tempo)
PRICE_CEILINGS_RT = {
    "GRU": 1300,
    "VCP": 1300,
    "CGH": 1300,
    "GIG": 1300,
    "SDU": 1300,
    "BSB": 1100,
    "SSA": 900,
    "FOR": 950,
    "CNF": 1200,
    "NAT": 900,

    # América do Sul
    "EZE": 1400,
    "SCL": 1500,
    "MVD": 1400,
    "LIM": 1600,
    "BOG": 1700,

    # Europa
    "LIS": 3000,
    "OPO": 2800,
    "MAD": 3200,
    "CDG": 3500,
    "FCO": 3500,

    # Estados Unidos
    "MIA": 3500,
    "MCO": 3400,
    "JFK": 3800,
}
DEFAULT_PRICE_CEILING_RT = 1500

# padrões de duração (noites) que mais convertem
RT_NIGHTS_OPTIONS = [2, 3, 4, 6, 7, 9, 10]

def get_price_ceiling_rt(dest_iata: str) -> int:
    return PRICE_CEILINGS_RT.get(dest_iata, DEFAULT_PRICE_CEILING_RT)

# ===============================
# IATA → SLUG KIWI
# ===============================

IATA_TO_SLUG = {
    "REC": "recife-pernambuco-brasil",

    # Daily
    "GRU": "aeroporto-internacional-de-sao-paulo-guarulhos-sao-paulo-sao-paulo-brasil",
    "GIG": "rio-de-janeiro-rio-de-janeiro-brasil",
    "BSB": "brasilia-distrito-federal-brasil",
    "SSA": "salvador-bahia-brasil",
    "FOR": "fortaleza-ceara-brasil",
    "CNF": "belo-horizonte-minas-gerais-brasil",
    "NAT": "natal-rio-grande-do-norte-brasil",
    "VCP": "campinas-sao-paulo-brasil",
    "CGH": "sao-paulo-sao-paulo-brasil",  # fallback (Kiwi nem sempre trata CGH direto)
    "SDU": "rio-de-janeiro-rio-de-janeiro-brasil",  # fallback (muitas vezes SDU não aparece)

    # Weekly BR
    "AJU": "aracaju-sergipe-brasil",
    "BEL": "belem-para-brasil",
    "BVB": "boa-vista-roraima-brasil",
    "CGB": "cuiaba-mato-grosso-brasil",
    "CGR": "campo-grande-mato-grosso-do-sul-brasil",
    "CWB": "curitiba-parana-brasil",
    "FLN": "florianopolis-santa-catarina-brasil",
    "GYN": "goiania-goias-brasil",
    "JPA": "joao-pessoa-paraiba-brasil",
    "MCZ": "maceio-alagoas-brasil",
    "MAO": "manaus-amazonas-brasil",
    "MCP": "macapa-amapa-brasil",
    "PMW": "palmas-tocantins-brasil",
    "POA": "porto-alegre-rio-grande-do-sul-brasil",
    "PVH": "porto-velho-rondonia-brasil",
    "RBR": "rio-branco-acre-brasil",
    "SLZ": "sao-luis-maranhao-brasil",
    "THE": "teresina-piaui-brasil",
    "VIX": "vitoria-espirito-santo-brasil",

    # Internacional
    "LIS": "lisboa-portugal",
    "MAD": "madrid-espanha",
    "OPO": "porto-portugal",
    "SCL": "santiago-chile",
    "EZE": "buenos-aires-argentina",
    "MVD": "montevideo-uruguai",
    "LIM": "lima-peru",
    "BOG": "bogota-colombia",
    "CDG": "paris-franca",
    "FCO": "roma-italia",
    "MIA": "miami-florida-united-states",
    "MCO": "orlando-florida-united-states",
    "JFK": "new-york-city-new-york-united-states",
}

def build_results_url_oneway(origin_iata: str, dest_iata: str, depart_date: str) -> str:
    """
    Monta a URL de busca do Kiwi.com para voo one-way.
    Exemplo: https://www.kiwi.com/pt/search/results/REC/GRU/2026-02-01
    """
    return f"https://www.kiwi.com/pt/search/results/{origin_iata}/{dest_iata}/{depart_date}"

import datetime

def today_plus_days(days: int) -> datetime.date:
    """
    Retorna a data de hoje + N dias (objeto date).
    """
    return datetime.date.today() + datetime.timedelta(days=days)
