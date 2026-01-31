from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import List, Dict, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bot.viajala_urls import build_viajala_url_ow_with_fallback

logger = logging.getLogger(__name__)

_COOKIES_ACCEPTED = False
_INTERSTITIAL_SEEN = 0
_INTERSTITIAL_DISMISSED = 0
_INTERSTITIAL_WAITED = 0



def _ensure_debug_dir() -> str:
    debug_dir = os.path.join(os.path.dirname(__file__), "..", "debug")
    debug_dir = os.path.abspath(debug_dir)
    os.makedirs(debug_dir, exist_ok=True)
    return debug_dir


def _adapt_path(debug_dir: str) -> str:
    return os.path.join(debug_dir, "viajala_adapt.json")


def _load_adapt_state(debug_dir: str) -> dict:
    path = _adapt_path(debug_dir)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_adapt_state(debug_dir: str, data: dict) -> None:
    path = _adapt_path(debug_dir)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _detect_page_state(driver) -> str:
    text = (driver.page_source or "").lower()
    if driver.find_elements(By.CSS_SELECTOR, "div.segments.result-item-ow"):
        return "RESULTS_OK"
    if "aceitar" in text and "cookies" in text:
        return "CONSENT"
    if "sites de viagem buscados" in text and "result" not in text:
        return "LOADING"
    if "os voos mais baratos encontrados recentemente" in text or "como e onde comprar passagens aéreas" in text:
        return "LANDING"
    if "/pesquisa-voos/" in (driver.current_url or ""):
        return "EMPTY"
    return "LANDING"


def _dismiss_overlays(driver, timeout: int = 6) -> None:
    wait = WebDriverWait(driver, timeout)
    try:
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)
    except Exception:
        pass

    possible_buttons = [
        (By.XPATH, "//button[contains(., 'Aceitar')]") ,
        (By.XPATH, "//button[contains(., 'Concordo')]") ,
        (By.XPATH, "//button[contains(., 'Entendi')]") ,
        (By.XPATH, "//button[contains(., 'Fechar')]") ,
        (By.XPATH, "//button[contains(., 'Continuar')]") ,
        (By.CSS_SELECTOR, "[aria-label*='close' i], [aria-label*='fechar' i]"),
    ]

    for by, sel in possible_buttons:
        try:
            btn = wait.until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            break
        except Exception:
            pass

    try:
        driver.execute_script(
            """
            document.documentElement.classList.remove('cdk-global-scrollblock');
            document.body.classList.remove('cdk-global-scrollblock');
            document.documentElement.style.overflow = 'auto';
            document.body.style.overflow = 'auto';
            const backdrops = document.querySelectorAll('.cdk-overlay-backdrop, .cdk-global-overlay-wrapper');
            backdrops.forEach(e => e.remove());
            """
        )
    except Exception:
        pass


def _try_accept_cookies(driver, timeout: int = 8) -> bool:
    end = time.time() + timeout
    link_xpath = (
        "//a[normalize-space()='Aceitar' or "
        "contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ACEITAR')]"
    )
    button_xpath = (
        "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ACEITAR')]"
    )
    try:
        while time.time() < end:
            try:
                links = driver.find_elements(By.XPATH, link_xpath)
            except Exception:
                links = []
            for el in links:
                try:
                    if not el.is_displayed():
                        continue
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                    el.click()
                    logger.debug("cookies_accepted=True")
                    return True
                except Exception:
                    continue

            try:
                buttons = driver.find_elements(By.XPATH, button_xpath)
            except Exception:
                buttons = []
            for el in buttons:
                try:
                    if not el.is_displayed():
                        continue
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                    el.click()
                    logger.debug("cookies_accepted=True")
                    return True
                except Exception:
                    continue
            time.sleep(0.2)
    except Exception:
        pass
    logger.debug("cookies_accepted=False")
    return False


def _normalize_airline(name: str | None) -> str | None:
    if not name:
        return None
    value = name.strip().upper()
    if not value:
        return None
    mapping = {
        "G3": "GOL",
        "GOL": "GOL",
        "AZUL": "AZUL",
        "AD": "AZUL",
        "LATAM": "LATAM",
        "LA": "LATAM",
        "JJ": "LATAM",
        "TAM": "LATAM",
    }
    return mapping.get(value, value)


def _is_time_hhmm(s: str | None) -> bool:
    if not s:
        return False
    s = s.strip()
    if not re.match(r"^\d{2}:\d{2}$", s):
        return False
    try:
        hh, mm = s.split(":", 1)
        h = int(hh)
        m = int(mm)
    except Exception:
        return False
    return 0 <= h <= 23 and 0 <= m <= 59


def _wait_results_stable(driver, cards_css: str, timeout: int = 35, stable_rounds: int = 3, poll: float = 0.6) -> bool:
    end = time.time() + timeout
    last_count = None
    stable = 0
    while time.time() < end:
        try:
            cards = driver.find_elements(By.CSS_SELECTOR, cards_css)
            count = len(cards)
        except Exception:
            count = 0
        if count > 0 and count == last_count:
            stable += 1
        else:
            stable = 0
        last_count = count
        if count > 0 and stable >= stable_rounds:
            return True
        time.sleep(poll)
    return False


def _wait_cards_loaded(driver, timeout: int = 20) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "span.price-value")) > 0
        )
        return True
    except Exception:
        return False


def _try_close_overlay(driver, timeout: int = 4) -> bool:
    end = time.time() + timeout
    selectors = [
        "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'FECHAR')]",
        "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ENTENDI')]",
        "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'OK')]",
        "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'CONTINUAR')]",
    ]
    aria_selectors = [
        "[aria-label*='close' i]",
        "[aria-label*='fechar' i]",
    ]
    try:
        while time.time() < end:
            for xpath in selectors:
                try:
                    buttons = driver.find_elements(By.XPATH, xpath)
                except Exception:
                    buttons = []
                for btn in buttons:
                    try:
                        if not btn.is_displayed():
                            continue
                        try:
                            btn.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", btn)
                        return True
                    except Exception:
                        continue
            for sel in aria_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, sel)
                    if not btn.is_displayed():
                        continue
                    try:
                        btn.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", btn)
                    return True
                except Exception:
                    continue
            time.sleep(0.2)
    except Exception:
        pass
    return False


def _compute_confidence(
    price_ok: bool,
    times_ok: bool,
    duration_ok: bool,
    airline_ok: bool,
    link_ok: bool,
) -> int:
    score = 0
    if price_ok:
        score += 30
    if times_ok:
        score += 20
    if duration_ok:
        score += 20
    if airline_ok:
        score += 20
    if link_ok:
        score += 10
    return score


def _dismiss_interstitials(driver, timeout: int = 8) -> bool:
    global _INTERSTITIAL_SEEN, _INTERSTITIAL_DISMISSED, _INTERSTITIAL_WAITED
    end = time.time() + timeout
    detected = False

    dialogs = driver.find_elements(By.CSS_SELECTOR, "[role='dialog']")
    if dialogs:
        detected = True

    page_text = (driver.page_source or "").lower()
    if "gol" in page_text and "overlay" in page_text:
        detected = True

    if detected:
        _INTERSTITIAL_SEEN += 1

    if detected and _INTERSTITIAL_SEEN > 2:
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: not d.find_elements(By.CSS_SELECTOR, "[role='dialog']")
            )
            _INTERSTITIAL_WAITED += 1
        except Exception:
            pass
        return True

    if detected:
        selectors = [
            "button[aria-label*='close' i]",
            "button[aria-label*='fechar' i]",
        ]
        for sel in selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                btn.click()
                _INTERSTITIAL_DISMISSED += 1
                return True
            except Exception:
                continue
        try:
            btn = driver.find_element(By.XPATH, "//button[contains(., '×') or contains(., 'X')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            btn.click()
            _INTERSTITIAL_DISMISSED += 1
            return True
        except Exception:
            pass

        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            _INTERSTITIAL_DISMISSED += 1
            return True
        except Exception:
            pass

        try:
            WebDriverWait(driver, timeout).until(
                lambda d: not d.find_elements(By.CSS_SELECTOR, "[role='dialog']")
            )
            _INTERSTITIAL_WAITED += 1
        except Exception:
            pass

    return detected


def _dismiss_partner_modal(driver, timeout: int = 10) -> bool:
    modal_sel = "div.frame-container.modal"
    close_sel = "app-svg-icon.smart-close"
    header_sel = "div.frame-container.modal div.header"
    start = time.time()

    def _modal_present() -> bool:
        try:
            modals = driver.find_elements(By.CSS_SELECTOR, modal_sel)
            return bool(modals) and modals[0].is_displayed()
        except Exception:
            return False

    if not _modal_present():
        return False

    logger.info("[VIAJALA] partner_modal=seen")
    try:
        driver.save_screenshot(os.path.join(_ensure_debug_dir(), "viajala_modal.png"))
    except Exception:
        pass

    while time.time() - start < timeout:
        try:
            el = driver.find_element(By.CSS_SELECTOR, close_sel)
            el.click()
            logger.info("[VIAJALA] partner_modal=dismissed method=close_icon")
            return True
        except Exception:
            pass
        try:
            el = driver.find_element(By.CSS_SELECTOR, close_sel)
            svg = el.find_element(By.CSS_SELECTOR, "svg")
            svg.click()
            logger.info("[VIAJALA] partner_modal=dismissed method=close_svg")
            return True
        except Exception:
            pass
        try:
            header = driver.find_element(By.CSS_SELECTOR, header_sel)
            header.click()
            logger.info("[VIAJALA] partner_modal=dismissed method=header")
            return True
        except Exception:
            pass
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            logger.info("[VIAJALA] partner_modal=dismissed method=esc")
            return True
        except Exception:
            pass
        try:
            WebDriverWait(driver, 1).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, modal_sel))
            )
            logger.info("[VIAJALA] partner_modal=dismissed method=wait")
            return True
        except Exception:
            pass
    return _modal_present()


def _wait_interstitial_to_clear(driver, timeout: int = 15) -> None:
    modal_css = "mat-dialog-container, .mat-mdc-dialog-surface"
    try:
        WebDriverWait(driver, timeout).until(lambda d: len(d.find_elements(By.CSS_SELECTOR, modal_css)) == 0)
    except Exception:
        pass


def _close_viajala_interstitial(driver, timeout: int = 2) -> bool:
    selectors = [
        "app-svg-icon.smart-close[name='close']",
        "app-svg-icon.smart-close",
        "app-svg-icon.smart-close .mat-icon",
    ]
    for css in selectors:
        try:
            el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            continue
    return False


def _partner_modal_visible(driver) -> bool:
    try:
        modals = driver.find_elements(By.CSS_SELECTOR, "div.frame-container.modal")
        return bool(modals) and modals[0].is_displayed()
    except Exception:
        return False


def _parse_price_value(text: str) -> int | None:
    if not text:
        return None
    cleaned = (
        text.replace("R$", "")
        .replace(".", "")
        .replace(" ", "")
        .replace("\xa0", "")
        .strip()
    )
    if "," in cleaned:
        cleaned = cleaned.split(",", 1)[0]
    return int(cleaned) if cleaned.isdigit() else None


def _parse_duration_min(text: str) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d{1,2})h(\d{2})", text)
    if match:
        return int(match.group(1)) * 60 + int(match.group(2))
    match = re.search(r"(\d{1,2})h(\d{1,2})", text)
    if match:
        return int(match.group(1)) * 60 + int(match.group(2))
    match = re.search(r"(\d{1,2})h", text)
    if match:
        return int(match.group(1)) * 60
    return None


def _parse_extra_offers_count(text: str) -> int | None:
    match = re.search(r"(\d+)\s+ofertas\s+mais", text.lower())
    if match:
        return int(match.group(1))
    return None


def _find_price_text(card) -> str | None:
    patterns = [r"R\$\s*[\d\.]+,\d{2}", r"R\$\s*[\d\.,]+"]
    candidates = []

    sources = [
        card.text or "",
        card.get_attribute("innerText") or "",
        card.get_attribute("textContent") or "",
        card.get_attribute("innerHTML") or "",
    ]
    for source in sources:
        for pattern in patterns:
            for match in re.findall(pattern, source):
                candidates.append(match)

    if not candidates:
        return None

    prices = [p for p in (_parse_price_value(c) for c in candidates) if p is not None]
    if not prices:
        return None
    return f"R$ {min(prices)}"


def _wait_any_price(driver, timeout: int = 12) -> bool:
    price_re = re.compile(r"R\$\s*\d")
    try:
        WebDriverWait(driver, timeout).until(lambda d: price_re.search(d.page_source or ""))
        return True
    except Exception:
        return False


def _find_airline(card) -> str | None:
    try:
        label = card.find_element(By.CSS_SELECTOR, "div.partner-label > div").text.strip()
    except Exception:
        label = ""
    if label:
        return label
    try:
        alt = card.find_element(By.CSS_SELECTOR, "div.airline-logo img").get_attribute("alt")
        return alt.strip() if alt else None
    except Exception:
        return None


    def _normalize_airline(name: str | None) -> str | None:
        if not name:
            return None
        code = name.strip().upper()
        mapping = {"G3": "GOL", "JJ": "LATAM", "AD": "Azul"}
        return mapping.get(code, name)


    def _is_time_hhmm(value: str | None) -> bool:
        if not value:
            return False
        return bool(re.match(r"^\d{2}:\d{2}$", value.strip()))


    def _compute_confidence(price_ok: bool, times_ok: bool, duration_ok: bool, airline_ok: bool, link_ok: bool) -> int:
        score = 0
        score += 30 if price_ok else 0
        score += 20 if times_ok else 0
        score += 20 if duration_ok else 0
        score += 20 if airline_ok else 0
        score += 10 if link_ok else 0
        return score


def _parse_stops(card) -> int | None:
    try:
        layovers = card.find_element(By.CSS_SELECTOR, "div.layovers").text.strip()
        return 0 if layovers == "" else None
    except Exception:
        return None


def _card_has_valid_route(card, origin: str, destination: str) -> bool:
    airports = []
    try:
        for el in card.find_elements(By.CSS_SELECTOR, "div.airport"):
            text = (el.text or "").strip().upper()
            if text:
                airports.append(text)
    except Exception:
        return False

    valid_dests = {destination}
    if destination in {"GRU", "CGH", "VCP"}:
        valid_dests.add("SAO")

    has_origin = origin in airports
    has_dest = any(d in airports for d in valid_dests)
    return has_origin and has_dest


def _is_next_day(dep_time: str | None, arr_time: str | None, card) -> bool:
    try:
        if card.find_elements(By.CSS_SELECTOR, "div.nextday"):
            return True
    except Exception:
        pass
    if _is_time_hhmm(dep_time) and _is_time_hhmm(arr_time):
        dep_h, dep_m = [int(x) for x in dep_time.split(":")]
        arr_h, arr_m = [int(x) for x in arr_time.split(":")]
        if (arr_h, arr_m) < (dep_h, dep_m):
            return True
    return False


def _save_debug_zero(debug_dir: str, driver, cards: list) -> None:
    html_path = os.path.join(debug_dir, "viajala_last.html")
    png_path = os.path.join(debug_dir, "viajala_last.png")
    url_path = os.path.join(debug_dir, "viajala_last_url.txt")
    cards_path = os.path.join(debug_dir, "viajala_last_cards.txt")
    try:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except Exception:
        pass
    try:
        driver.save_screenshot(png_path)
    except Exception:
        pass
    try:
        with open(url_path, "w", encoding="utf-8") as f:
            f.write(driver.current_url)
    except Exception:
        pass
    try:
        with open(cards_path, "w", encoding="utf-8") as f:
            f.write(f"cards_found={len(cards)}\n")
            for card in cards[:5]:
                text = (card.text or "").replace("\n", " ")
                f.write(text[:200] + "\n")
    except Exception:
        pass
    logger.info(
        "[VIAJALA][DEBUG] saved html=%s png=%s url=%s cards=%s",
        html_path,
        png_path,
        url_path,
        cards_path,
    )


def scrape_with_selenium(
    driver,
    origin: str,
    destination: str,
    depart_date: str,
    max_cards: int = 30,
) -> List[Dict[str, Any]]:
    debug_dir = _ensure_debug_dir()
    adapt = _load_adapt_state(debug_dir)
    prefer_dest = (adapt.get("viajala_preferred_dest") or {})

    urls = build_viajala_url_ow_with_fallback(origin, destination, depart_date)
    if destination in prefer_dest:
        preferred = prefer_dest[destination]
        urls = [u for u in urls if f"-{preferred}/" in u] + [u for u in urls if f"-{preferred}/" not in u]

    last_selector = None
    for url in urls:
        start_ts = time.time()
        first_price_ts = None
        logger.info("[VIAJALA] url=%s", url)
        driver.get(url)
        global _COOKIES_ACCEPTED
        if not _COOKIES_ACCEPTED:
            _try_accept_cookies(driver)
            _COOKIES_ACCEPTED = True
        _dismiss_interstitials(driver)
        _dismiss_overlays(driver)
        _try_close_overlay(driver)
        _close_viajala_interstitial(driver)
        _wait_interstitial_to_clear(driver)
        if _wait_cards_loaded(driver, timeout=20):
            first_price_ts = time.time()
        if _dismiss_partner_modal(driver):
            if _dismiss_partner_modal(driver):
                time.sleep(2)

        page_state = _detect_page_state(driver)
        logger.info("[VIAJALA] page_state=%s", page_state)

        if page_state in ("LANDING", "EMPTY"):
            adapt.setdefault("viajala_stats", {})
            adapt["viajala_stats"]["airport_url_failed"] = adapt["viajala_stats"].get("airport_url_failed", 0) + 1
            prefer_dest.setdefault(destination, "SAO" if destination in {"GRU", "CGH", "VCP"} else "RIO" if destination in {"GIG", "SDU"} else destination)
            adapt["viajala_preferred_dest"] = prefer_dest

        try:
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.segments.result-item-ow"))
            )
            selector = "div.segments.result-item-ow"
        except TimeoutException:
            selector = "div.segments.result-item"

        if _dismiss_partner_modal(driver):
            time.sleep(2)
        if _partner_modal_visible(driver):
            logger.info("[VIAJALA] partner_modal=visible, skipping collection")
            _save_debug_zero(debug_dir, driver, [])
            continue

        stable_ok = _wait_results_stable(driver, selector)
        if not stable_ok:
            adapt.setdefault("last_run", {})
            adapt["last_run"]["stable_wait"] = False
            _save_adapt_state(debug_dir, adapt)
        cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if not cards:
            selector = "div.segments"
            cards = [
                c for c in driver.find_elements(By.CSS_SELECTOR, selector)
                if c.find_elements(By.CSS_SELECTOR, "span.price-value") and c.find_elements(By.CSS_SELECTOR, "a.btn.book")
            ]

        last_selector = selector
        logger.info("[VIAJALA] selector=%s cards_found=%s", selector, len(cards))

        _wait_any_price(driver, timeout=12)
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.25);")
            time.sleep(0.8)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
        except Exception:
            pass

        if not cards and page_state == "LOADING":
            _dismiss_interstitials(driver)
            if _dismiss_partner_modal(driver):
                time.sleep(5)
                cards = driver.find_elements(By.CSS_SELECTOR, selector)

        offers: List[Dict[str, Any]] = []
        seen_links = set()
        for card in cards[:max_cards]:
            try:
                if card.find_elements(By.XPATH, "ancestor::div[contains(@class,'frame-container') and contains(@class,'modal')]"):
                    continue
            except Exception:
                pass
            text = card.text or ""
            low = text.lower()
            if "patrocinado" in low or "skyscanner" in low:
                continue
            if not _card_has_valid_route(card, origin, destination):
                continue

            try:
                price_text = card.find_element(By.CSS_SELECTOR, "span.price-value").text
            except Exception:
                price_text = ""
            if not price_text:
                price_text = _find_price_text(card) or ""
            price = _parse_price_value(price_text)
            if price is not None and first_price_ts is None:
                first_price_ts = time.time()

            try:
                dep_time = card.find_element(By.CSS_SELECTOR, "div.departure strong").text.strip()
            except Exception:
                dep_time = None
            try:
                arr_time = card.find_element(By.CSS_SELECTOR, "div.arrival strong").text.strip()
            except Exception:
                arr_time = None
            try:
                duration_text = card.find_element(By.CSS_SELECTOR, "span.duration").text.strip()
            except Exception:
                duration_text = None
            duration_min = _parse_duration_min(duration_text or "")
            if duration_min is not None and duration_min > 900:
                duration_min = None

            airline = _normalize_airline(_find_airline(card))
            stops = _parse_stops(card)

            link = None
            try:
                link_el = card.find_element(By.CSS_SELECTOR, "a.btn.book")
                href = link_el.get_attribute("href")
                if href and "viajala.com.br/redirect" in href:
                    link = href
            except Exception:
                link = None

            next_day = _is_next_day(dep_time, arr_time, card)

            price_ok = price is not None
            times_ok = _is_time_hhmm(dep_time) and _is_time_hhmm(arr_time)
            duration_ok = duration_min is not None
            airline_ok = bool(airline)
            link_ok = bool(link)
            confidence = _compute_confidence(price_ok, times_ok, duration_ok, airline_ok, link_ok)

            if confidence < 60:
                continue

            if link and link in seen_links:
                continue
            if link:
                seen_links.add(link)

            offer = {
                "provider": "viajala",
                "origin": origin,
                "destination": destination,
                "depart_date": depart_date,
                "price": price,
                "dep_time": dep_time,
                "arr_time": arr_time,
                "duration_min": duration_min,
                "airline": airline,
                "stops": stops,
                "link": link,
                "raw_text": text,
                "confidence": confidence,
                "extra_offers_count": _parse_extra_offers_count(text),
            }
            if next_day:
                offer["next_day"] = True
            offers.append(offer)

        offers.sort(
            key=lambda o: (
                o.get("price") is None,
                o.get("price") or 10**9,
                o.get("duration_min") or 10**9,
            )
        )

        adapt["last_working_selector"] = selector if offers else adapt.get("last_working_selector")
        adapt.setdefault("selector_success", {})
        adapt["selector_success"][selector] = adapt["selector_success"].get(selector, 0) + (1 if offers else 0)

        adapt["interstitial_seen_count"] = _INTERSTITIAL_SEEN
        adapt["interstitial_dismissed_count"] = _INTERSTITIAL_DISMISSED
        adapt["interstitial_waited_count"] = _INTERSTITIAL_WAITED

        adapt["run_metrics"] = {
            "had_gol_banner": _INTERSTITIAL_SEEN > 0,
            "time_to_first_price": (first_price_ts - start_ts) if first_price_ts else None,
            "total_cards": len(cards),
            "prices_found": sum(1 for o in offers if o.get("price") is not None),
            "min_price": min([o.get("price") for o in offers if o.get("price") is not None], default=None),
        }

        adapt["last_run"] = {
            "timestamp": int(time.time()),
            "url": url,
            "page_state": page_state,
            "cards_found": len(cards),
            "offers_valid": len(offers),
            "selector": selector,
            "reason": None if offers else "NO_OFFERS",
        }
        _save_adapt_state(debug_dir, adapt)

        logger.info("[VIAJALA] offers_valid=%s", len(offers))
        if offers:
            return offers

        if _INTERSTITIAL_SEEN > 0:
            try:
                driver.save_screenshot(os.path.join(debug_dir, "viajala_interstitial.png"))
            except Exception:
                pass
        _save_debug_zero(debug_dir, driver, cards)

    adapt["last_working_selector"] = last_selector or adapt.get("last_working_selector")
    _save_adapt_state(debug_dir, adapt)
    logger.info("[VIAJALA] all tries failed: %s", len(urls))
    return []
