import re
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict


@dataclass(frozen=True)
class FlightCard:
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    airline: str
    duration_min: int
    price_brl: int


def _parse_duration_minutes(duration_text: str) -> Optional[int]:
    """
    Converte durações como "3h 20 min" para minutos (200).
    Aceita variações como "3h", "20 min", "3 h 20min".
    """
    if not duration_text:
        return None

    hours = 0
    minutes = 0

    h_match = re.search(r"(\d+)\s*h", duration_text)
    if h_match:
        hours = int(h_match.group(1))

    m_match = re.search(r"(\d+)\s*min", duration_text)
    if m_match:
        minutes = int(m_match.group(1))

    total = hours * 60 + minutes
    return total if total > 0 else None


def parse_flight_card_text(text: str) -> Optional[FlightCard]:
    """
    Faz parse de um bloco de texto de card de voo, por exemplo:

    02:50 – 06:10
    Azul
    3h 20 min
    REC–GRU

    R$ 594

    Retorna FlightCard ou None se não conseguir extrair campos essenciais.
    """
    if not text:
        return None

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 4:
        return None

    times = lines[0]
    airline = lines[1]
    duration = lines[2]
    route = lines[3]
    price_line = lines[4] if len(lines) > 4 else ""

    if "–" not in times or "–" not in route:
        return None

    dep, arr = [t.strip() for t in times.split("–", 1)]
    origin, dest = [t.strip() for t in route.split("–", 1)]

    price = extract_price_int_from_text(price_line)
    duration_min = _parse_duration_minutes(duration)

    if not all([dep, arr, origin, dest, airline]) or price is None or duration_min is None:
        return None

    return FlightCard(
        origin=origin,
        destination=dest,
        departure_time=dep,
        arrival_time=arr,
        airline=airline,
        duration_min=duration_min,
        price_brl=price,
    )


def extract_price_int_from_text(text: str) -> Optional[int]:
    """
    Extrai um preço inteiro de textos como:
    'R$ 1.234', '1.234', 'BRL 1,234'.
    Retorna None se não encontrar algo válido.
    ⚠️ Limitação: separadores decimais são ignorados (R$ 1.234,56 vira 123456).
    """
    if not text:
        return None

    cleaned = re.sub(r"[^0-9.,]", "", text)
    cleaned = cleaned.replace(".", "").replace(",", "")

    try:
        value = int(cleaned)
        return value if value > 0 else None
    except Exception:
        return None


PRICE_SELECTORS = (
    '[data-test-id="price"]',
    '.price',
    '.amount',
    '[class*="Price"]',
)


def _try_extract_from_container(container):
    for sel in PRICE_SELECTORS:
        try:
            el = container.find_element("css selector", sel)
            price = extract_price_int_from_text(el.text)
            if price is not None:
                return price, el.text
        except Exception:
            continue
    return None, None


def find_price_for_sector(sector_element) -> Optional[int]:
    """
    Tenta extrair o preço de um sector/card:
    1) no próprio sector
    2) no card pai
    3) em siblings próximos
    """
    price, _ = _try_extract_from_container(sector_element)
    if price is not None:
        return price

    try:
        parent = sector_element.find_element(
            "xpath", "./ancestor::*[contains(@class,'card')]"
        )
        price, _ = _try_extract_from_container(parent)
        if price is not None:
            return price
    except Exception:
        pass

    try:
        sibling = sector_element.find_element("xpath", "following-sibling::*")
        price, _ = _try_extract_from_container(sibling)
        if price is not None:
            return price
    except Exception:
        pass

    return None


def compute_min_price(flight_sectors: List) -> Tuple[Optional[int], Dict]:
    """
    Retorna (menor preço encontrado, debug_dict) para uma lista de setores.
    debug_dict inclui amostras de texto dos setores e contagem de falhas.
    """
    prices_found: List[int] = []
    debug_samples: List[str] = []
    missing_count = 0

    for sector in flight_sectors:
        price = find_price_for_sector(sector)
        if price is not None:
            prices_found.append(price)
            if len(debug_samples) < 3:
                try:
                    debug_samples.append(sector.text)
                except Exception:
                    debug_samples.append("NO_TEXT")
        else:
            missing_count += 1

    return (
        min(prices_found) if prices_found else None,
        {
            "prices_found": prices_found,
            "missing_count": missing_count,
            "debug_samples": debug_samples,
            "sectors_count": len(flight_sectors),
        },
    )
import re
from typing import Optional, List, Tuple, Dict

def extract_price_int_from_text(text: str) -> Optional[int]:
    """
    Extrai um inteiro de preço de textos como 'R$ 1.234', '1.234', 'BRL 1,234', etc.
    Retorna None se não encontrar.
    """
    if not text:
        return None
    # Remove currency symbols and letters
    cleaned = re.sub(r'[^0-9.,]', '', text)
    # Troca vírgula por ponto se for separador decimal
    if cleaned.count(',') == 1 and cleaned.count('.') == 0:
        cleaned = cleaned.replace(',', '.')
    # Remove milhares
    cleaned = cleaned.replace('.', '').replace(',', '')
    try:
        value = int(cleaned)
        return value if value > 0 else None
    except Exception:
        return None

def find_price_for_sector(sector_element) -> Optional[int]:
    """
    Tenta extrair o preço de um sector/card, subindo para containers pais e siblings se necessário.
    sector_element: Selenium WebElement
    """
    # 1. Tenta dentro do próprio sector
    price_selectors = [
        '[data-test-id="price"]',
        '.price',
        '.amount',
        '[class*="Price"]',
    ]
    for sel in price_selectors:
        try:
            el = sector_element.find_element('css selector', sel)
            price = extract_price_int_from_text(el.text)
            if price:
                return price
        except Exception:
            continue
    # 2. Sobe para o card pai
    try:
        parent = sector_element.find_element('xpath', './ancestor::*[contains(@class,"card")]')
        for sel in price_selectors:
            try:
                el = parent.find_element('css selector', sel)
                price = extract_price_int_from_text(el.text)
                if price:
                    return price
            except Exception:
                continue
    except Exception:
        pass
    # 3. Siblings/containers próximos
    try:
        sibling = sector_element.find_element('xpath', 'following-sibling::*')
        for sel in price_selectors:
            try:
                el = sibling.find_element('css selector', sel)
                price = extract_price_int_from_text(el.text)
                if price:
                    return price
            except Exception:
                continue
    except Exception:
        pass
    # 4. Falhou
    return None

def compute_min_price(flight_sectors: List) -> Tuple[Optional[int], Dict]:
    """
    Itera setores, chama find_price_for_sector, coleta preços e debug.
    Retorna (min_price, debug_dict)
    """
    prices_found = []
    debug_samples = []
    missing_count = 0
    for sector in flight_sectors:
        price = find_price_for_sector(sector)
        if price is not None:
            prices_found.append(price)
            if len(debug_samples) < 3:
                try:
                    debug_samples.append(sector.text)
                except Exception:
                    debug_samples.append('NO_TEXT')
        else:
            missing_count += 1
    min_price = min(prices_found) if prices_found else None
    debug = {
        'prices_found': prices_found,
        'missing_count': missing_count,
        'debug_samples': debug_samples,
        'sectors_count': len(flight_sectors),
    }
    return min_price, debug
