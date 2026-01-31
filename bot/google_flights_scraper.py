import re
import time
import traceback
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bot.status_codes import ScrapeStatus, ScrapeReason, ScrapeResult
from bot.price_extractor import extract_price_int_from_text, _parse_duration_minutes, parse_flight_card_text
from bot.pricing_utils import brl

RESULT_SELECTORS = [
    (By.CSS_SELECTOR, "div[role='listitem']"),
    (By.CSS_SELECTOR, "li[role='listitem']"),
    (By.CSS_SELECTOR, "div[aria-label*='R$']"),
]

CARD_SELECTORS = [
    (By.CSS_SELECTOR, "div[role='listitem']"),
    (By.CSS_SELECTOR, "li[role='listitem']"),
    (By.CSS_SELECTOR, "div.yR1fYc"),
]


def wait_results(driver, timeout=25):
    w = WebDriverWait(driver, timeout)
    last_err = None
    for by, sel in RESULT_SELECTORS:
        try:
            w.until(EC.presence_of_element_located((by, sel)))
            return True
        except Exception as e:
            last_err = e
    raise TimeoutException(f"Resultados não apareceram: {last_err}")


def _pick_first_line(lines, predicate):
    for line in lines:
        if predicate(line):
            return line
    return None


def _extract_text(el) -> str:
    try:
        return el.text or ""
    except Exception:
        return ""


def _get_attr(el, name: str) -> str:
    try:
        return el.get_attribute(name) or ""
    except Exception:
        return ""


def _find_first_text(card, selectors) -> str:
    for by, sel in selectors:
        try:
            el = card.find_element(by, sel)
            txt = _extract_text(el)
            if txt:
                return txt
        except Exception:
            continue
    return ""


def _find_all_texts(card, selectors) -> List[str]:
    for by, sel in selectors:
        try:
            els = card.find_elements(by, sel)
            texts = [t for t in (_extract_text(e) for e in els) if t]
            if texts:
                return texts
        except Exception:
            continue
    return []


def _parse_airline_from_card(card) -> str:
    airline = _find_first_text(
        card,
        [
            (By.CSS_SELECTOR, "div.sSHqwe span"),
            (By.CSS_SELECTOR, "span.h1fkLb span"),
        ],
    )
    if not airline:
        aria = _get_attr(card, "aria-label")
        m = re.search(r"Voo da\s+([^\.]+)\.", aria or "")
        if m:
            airline = m.group(1).strip()
    return airline or "?"


def _parse_times_from_card(card) -> tuple:
    # Prefer aria-label spans
    dep = ""
    arr = ""
    try:
        dep_el = card.find_element(By.CSS_SELECTOR, "span[aria-label^='Horário de partida']")
        dep = _extract_text(dep_el)
    except Exception:
        pass
    try:
        arr_el = card.find_element(By.CSS_SELECTOR, "span[aria-label^='Horário de chegada']")
        arr = _extract_text(arr_el)
    except Exception:
        pass

    if dep and arr:
        return dep, arr

    # Fallback to visible time blocks
    times = _find_all_texts(
        card,
        [
            (By.CSS_SELECTOR, "div[aria-label^='Horário de partida']"),
            (By.CSS_SELECTOR, "div[aria-label^='Horário de chegada']"),
            (By.CSS_SELECTOR, "span[role='text']"),
        ],
    )
    hhmm = [t for t in times if re.match(r"^\d{1,2}:\d{2}$", t)]
    if len(hhmm) >= 2:
        return (hhmm[0], hhmm[1])

    aria = _get_attr(card, "aria-label")
    if aria:
        t = re.findall(r"\b(\d{1,2}:\d{2})\b", aria)
        if len(t) >= 2:
            return t[0], t[1]
    return ("?", "?")


def _parse_route_from_card(card) -> tuple:
    # Prefer IATA spans inside the route block
    codes = _find_all_texts(
        card,
        [
            (By.CSS_SELECTOR, "div.PTuQse span[aria-label='']"),
            (By.CSS_SELECTOR, "div.G2WY5c div"),
            (By.CSS_SELECTOR, "div.c8rWCd div"),
        ],
    )
    iata = [c for c in codes if re.match(r"^[A-Z]{3}$", c)]
    if len(iata) >= 2:
        return iata[0], iata[1]
    aria = _get_attr(card, "aria-label")
    if aria:
        i = re.findall(r"\b([A-Z]{3})\b", aria)
        if len(i) >= 2:
            return i[0], i[1]
    return "?", "?"


def _parse_duration_from_card(card) -> str:
    duration = _find_first_text(
        card,
        [
            (By.CSS_SELECTOR, "div[aria-label^='Duração total']"),
            (By.CSS_SELECTOR, "span.rGRiKd ~ span"),
        ],
    )
    if not duration:
        aria = _get_attr(card, "aria-label")
        m = re.search(r"Duração total:\s*([^\.]+)\.", aria or "")
        if m:
            duration = m.group(1).strip()
    return duration or "?"


def _parse_stops_from_card(card) -> str:
    stops = _find_first_text(
        card,
        [
            (By.CSS_SELECTOR, "span[aria-label*='Voo']"),
            (By.CSS_SELECTOR, "span.rGRiKd"),
            (By.CSS_SELECTOR, "div.BbR8Ec span"),
        ],
    )
    if not stops:
        aria = _get_attr(card, "aria-label")
        if aria:
            m = re.search(r"Voo da [^\.]+ com ([^\.]+)\.", aria)
            if m:
                stops = m.group(1).strip()
            else:
                m = re.search(r"Voo direto\.", aria)
                if m:
                    stops = "Sem escalas"
    return stops or "?"


def _parse_stops_detail_from_card(card) -> List[str]:
    aria = _get_attr(card, "aria-label")
    if not aria:
        return []
    details = []
    for m in re.finditer(r"Parada\s*\(\d+\s*de\s*\d+\)\s*de\s*([^\.]+)\.", aria):
        details.append(m.group(1).strip())
    return details


def _parse_price_from_card(card) -> tuple:
    price_text = _find_first_text(
        card,
        [
            (By.CSS_SELECTOR, "span[aria-label*='Reais brasileiros']"),
            (By.CSS_SELECTOR, "div.BVAVmf span"),
        ],
    )
    if not price_text:
        aria = _get_attr(card, "aria-label")
        m = re.search(r"A partir de\s*([0-9.]+)\s*Reais brasileiros", aria or "")
        if m:
            price_text = f"R$ {m.group(1)}"
    price_int = extract_price_int_from_text(price_text)
    return price_text or "?", price_int


def _parse_card_text(text: str) -> dict:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return {}

    parsed = parse_flight_card_text(text)
    if parsed:
        price_line = _pick_first_line(lines, lambda l: "R$" in l or "BRL" in l) or f"R$ {brl(parsed.price_brl)}"
        duration_line = _pick_first_line(lines, lambda l: "min" in l or "h" in l) or f"{parsed.duration_min} min"
        stops_line = _pick_first_line(lines, lambda l: "parada" in l.lower() or "stop" in l.lower() or "direto" in l.lower()) or "?"
        return {
            "dep_time": parsed.departure_time,
            "arr_time": parsed.arrival_time,
            "duration_text": duration_line,
            "origin_code": parsed.origin,
            "dest_code": parsed.destination,
            "airline": parsed.airline,
            "stops": stops_line,
            "price_text": price_line,
            "price": price_line,
            "price_int": parsed.price_brl,
        }

    # Fallback por regex
    times_match = re.search(r"(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})", text or "")
    dep_time = times_match.group(1) if times_match else "?"
    arr_time = times_match.group(2) if times_match else "?"

    route_match = re.search(r"\b([A-Z]{3})\s*[–-]\s*([A-Z]{3})\b", text or "")
    origin = route_match.group(1) if route_match else "?"
    dest = route_match.group(2) if route_match else "?"

    duration_line = _pick_first_line(lines, lambda l: "min" in l or "h" in l) or "?"
    duration_min = _parse_duration_minutes(duration_line)

    price_line = _pick_first_line(lines, lambda l: "R$" in l or "BRL" in l)
    price_int = extract_price_int_from_text(price_line or "")
    if price_line is None and price_int is not None:
        price_line = f"R$ {brl(price_int)}"

    stops_line = _pick_first_line(lines, lambda l: "parada" in l.lower() or "stop" in l.lower() or "direto" in l.lower()) or "?"

    # Heurística para airline
    def is_meta_line(l: str) -> bool:
        return (
            (times_match and l in (times_match.group(0),))
            or (route_match and l in (route_match.group(0),))
            or (l == duration_line)
            or (price_line and l == price_line)
            or (l == stops_line)
        )

    airline = _pick_first_line(lines, lambda l: not is_meta_line(l)) or "?"

    return {
        "dep_time": dep_time,
        "arr_time": arr_time,
        "duration_text": duration_line,
        "origin_code": origin,
        "dest_code": dest,
        "airline": airline,
        "stops": stops_line,
        "price_text": price_line or "?",
        "price": price_line or "?",
        "price_int": price_int,
        "duration_min": duration_min,
    }


def scrape_with_selenium(driver, wait, url, price_ceiling, max_results=10):
    flights = []
    min_price = None
    debug = {"url": url, "source": "google_flights"}
    try:
        print(f"[SCRAPE] {url}")
        driver.get(url)
        time.sleep(1.0)

        try:
            wait_results(driver, timeout=30)
        except TimeoutException:
            return ScrapeResult(
                status=ScrapeStatus.EMPTY,
                reason=ScrapeReason.TIMEOUT_WAITING_RESULTS,
                flights=[],
                min_price=None,
                debug=debug
            )

        cards = []
        for by, sel in CARD_SELECTORS:
            cards = driver.find_elements(by, sel)
            if cards:
                break

        if not cards:
            return ScrapeResult(
                status=ScrapeStatus.EMPTY,
                reason=ScrapeReason.NO_RESULTS,
                flights=[],
                min_price=None,
                debug=debug
            )

        for card in cards[:max_results]:
            try:
                dep_time, arr_time = _parse_times_from_card(card)
                origin, dest = _parse_route_from_card(card)
                duration_text = _parse_duration_from_card(card)
                airline = _parse_airline_from_card(card)
                stops = _parse_stops_from_card(card)
                stops_detail = _parse_stops_detail_from_card(card)
                price_text, price_int = _parse_price_from_card(card)
            except Exception:
                dep_time = arr_time = origin = dest = duration_text = airline = stops = "?"
                stops_detail = []
                price_text, price_int = "?", None

            if price_int is None:
                text = _extract_text(card)
                data = _parse_card_text(text)
            else:
                data = {
                    "dep_time": dep_time,
                    "arr_time": arr_time,
                    "duration_text": duration_text,
                    "origin_code": origin,
                    "dest_code": dest,
                    "airline": airline,
                    "stops": stops,
                    "stops_detail": stops_detail,
                    "price_text": price_text,
                    "price": price_text,
                    "price_int": price_int,
                }

            if not data or data.get("price_int") is None:
                continue
            flights.append(data)

        prices = [f.get("price_int") for f in flights if f.get("price_int") is not None]
        min_price = min(prices) if prices else None

        if not flights:
            return ScrapeResult(
                status=ScrapeStatus.EMPTY,
                reason=ScrapeReason.NO_RESULTS,
                flights=[],
                min_price=min_price,
                debug=debug
            )

        return ScrapeResult(
            status=ScrapeStatus.OK,
            reason=ScrapeReason.UNKNOWN,
            flights=flights,
            min_price=min_price,
            debug=debug
        )

    except Exception as e:
        print("[SCRAPE][CRASH]", e)
        traceback.print_exc()
        return ScrapeResult(
            status=ScrapeStatus.ERROR,
            reason=ScrapeReason.SELENIUM_EXCEPTION,
            flights=[],
            min_price=None,
            debug={"exception": str(e), "url": url, "source": "google_flights"}
        )
