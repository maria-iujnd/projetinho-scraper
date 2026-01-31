
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

RESULT_SELECTORS = [
    (By.CSS_SELECTOR, "[data-test*='Result']"),
    (By.CSS_SELECTOR, "[data-testid*='Result']"),
    (By.CSS_SELECTOR, "article"),  # fallback
]

def wait_results(driver, timeout=20):
    w = WebDriverWait(driver, timeout)
    last_err = None
    for by, sel in RESULT_SELECTORS:
        try:
            w.until(EC.presence_of_element_located((by, sel)))
            return True
        except Exception as e:
            last_err = e
    raise TimeoutException(f"Resultados não apareceram: {last_err}")
import time
import re
import traceback
from pathlib import Path
import tempfile
from typing import List, Dict, Tuple
from bot.status_codes import ScrapeStatus, ScrapeReason, ScrapeResult
from bot.kiwi_cookies import try_accept_cookies, is_overlay_blocking
from bot.price_extractor import compute_min_price, find_price_for_sector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# === Debug helpers ===
DEBUG_DIR = Path(tempfile.gettempdir()) / "kiwi_debug"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

def dump_debug(driver, tag=""):
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_tag = tag.replace(" ", "_")[:60]
    base = DEBUG_DIR / f"{ts}_{safe_tag}"
    html = ""
    # URL/título
    try:
        (base.with_suffix(".meta.txt")).write_text(
            f"URL: {getattr(driver, 'current_url', '?')}\nTITLE: {getattr(driver, 'title', '?')}\n",
            encoding="utf-8", errors="ignore",
        )
    except Exception:
        pass
    # HTML completo
    try:
        html = getattr(driver, 'page_source', '') or ""
        (base.with_suffix(".html")).write_text(html, encoding="utf-8", errors="ignore")
    except Exception:
        pass
    # Screenshot
    try:
        driver.save_screenshot(str(base.with_suffix(".png")))
    except Exception:
        pass
    print(f"[DEBUG] dumped: {base}.html/.png/.meta.txt  (len_html={len(html)})")

def looks_like_block(driver) -> bool:
    html = (getattr(driver, 'page_source', '') or '').lower()
    keywords = [
        "cloudflare", "checking your browser", "just a moment",
        "access denied", "attention required", "captcha",
        "verify you are human", "bot detection"
    ]
    return any(k in html for k in keywords)

def print_browser_logs(driver):
    try:
        for entry in driver.get_log("browser")[-30:]:
            print("[BROWSER]", entry)
    except Exception as e:
        print("[BROWSER] log not available:", e)
from typing import List, Dict, Tuple


def scrape_with_selenium(driver, wait, url, price_ceiling, max_results=10):
    """
    Função principal de scraping Selenium para Kiwi.
    Retorna ScrapeResult.
    """
    # === Navegação e scraping principal ===
    flights = []
    min_price = None
    debug = {"url": url}
    try:
        print(f"[SCRAPE] {url}")
        driver.get(url)
        dump_debug(driver, "after_get")


        # Aceita cookies e espera overlay sumir
        try:
            from bot.kiwi_cookies import try_accept_cookies, is_overlay_blocking
            try_accept_cookies(driver, wait, timeout=4)
            t0 = time.time()
            while is_overlay_blocking(driver) and time.time() - t0 < 5:
                time.sleep(0.25)
        except Exception:
            pass

        # Espera resultados reais
        try:
            wait_results(driver, timeout=25)
        except TimeoutException:
            # Diagnóstico TIMEOUT_WAITING_RESULTS
            print("[DIAG] Timeout esperando resultados ou shell vazio.")
            reason = ScrapeReason.TIMEOUT_WAITING_RESULTS
            print("[DIAG] URL:", driver.current_url)
            print("[DIAG] Title:", driver.title)
            print("[DIAG] HTML snippet:", driver.page_source[:800])
            return ScrapeResult(
                status=ScrapeStatus.ERROR,
                reason=reason,
                flights=[],
                min_price=None,
                debug={"block": True}
            )
        # Diagnóstico detalhado de erro
        page_source = driver.page_source.lower()
        challenge_signals = ["cloudflare", "cf-", "captcha", "verify", "robot", "challenge"]
        noresults_signals = ["nenhum resultado", "no results"]
        # 1. Sinais de challenge → BLOCKED_CHALLENGE
        found_challenge = [s for s in challenge_signals if s in page_source]
        if found_challenge:
            print("[DIAG] Sinais de challenge:", found_challenge)
            reason = ScrapeReason.BLOCKED_CHALLENGE
        else:
            # 2. Timeout esperando container de resultados
            # (Simulação: se não há nenhum data-test= ou Result, assume timeout)
            has_result_container = ("data-test" in page_source or "result" in page_source)
            if not has_result_container:
                print("[DIAG] Timeout esperando resultados ou shell vazio.")
                reason = ScrapeReason.TIMEOUT_WAITING_RESULTS
            else:
                # 3. Container presente e lista vazia/texto “nenhum resultado”
                found_noresults = [s for s in noresults_signals if s in page_source]
                if found_noresults:
                    print("[DIAG] Sinais de nenhum resultado:", found_noresults)
                    reason = ScrapeReason.NO_RESULTS
                else:
                    # 4. Fallback legado
                    print("[DIAG] Fallback: PAGE_NOT_LOADED")
                    reason = ScrapeReason.PAGE_NOT_LOADED

        print("[DIAG] URL:", driver.current_url)
        print("[DIAG] Title:", driver.title)
        print("[DIAG] HTML snippet:", driver.page_source[:800])

        return ScrapeResult(
            status=ScrapeStatus.ERROR,
            reason=reason,
            flights=[],
            min_price=None,
            debug={"block": True}
        )

        # 1) aceita cookies IMEDIATAMENTE
        try:
            from bot.kiwi_cookies import try_accept_cookies
            try_accept_cookies(driver)
        except Exception:
            pass

        # 2) dá um respiro curto pro JS renderizar
        time.sleep(1.5)

        # 3) Espera robusta por resultados reais
        try:
            # Espera um sinal real de que resultados carregaram:
            # - algum preço BRL (R$)
            # - ou a lista de resultados
            try:
                # Selenium 4.8+: EC.any_of
                wait = WebDriverWait(driver, 35)
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'R$')]")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid*='Result']")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='searchResults']")),
                    )
                )
            except AttributeError:
                # Fallback para Selenium <4.8
                deadline = time.time() + 35
                ok = False
                while time.time() < deadline:
                    if driver.find_elements(By.XPATH, "//*[contains(text(), 'R$')]"):
                        ok = True
                        break
                    if driver.find_elements(By.CSS_SELECTOR, "[data-testid*='Result']"):
                        ok = True
                        break
                    if driver.find_elements(By.CSS_SELECTOR, "[data-testid='searchResults']"):
                        ok = True
                        break
                    time.sleep(0.5)
                if not ok:
                    raise TimeoutException("TIMEOUT_WAITING_RESULTS")
        except TimeoutException:
            # Salva screenshot e HTML para debug headless
            try:
                from datetime import datetime
                import os
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                fname = f"debug_timeout_{ts}.png"
                driver.save_screenshot(fname)
                debug["screenshot"] = os.path.abspath(fname)
                htmlname = f"debug_timeout_{ts}.html"
                with open(htmlname, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                debug["html"] = os.path.abspath(htmlname)
            except Exception as e:
                debug["debug_save_error"] = str(e)
            if is_overlay_blocking(driver):
                try_accept_cookies(driver, wait)
                if is_overlay_blocking(driver):
                    return ScrapeResult(
                        status=ScrapeStatus.BLOCKED,
                        reason=ScrapeReason.COOKIE_MODAL_BLOCKING,
                        flights=[],
                        min_price=-1,
                        debug=debug
                    )
            return ScrapeResult(
                status=ScrapeStatus.EMPTY,
                reason=ScrapeReason.TIMEOUT_WAITING_RESULTS,
                flights=[],
                min_price=-1,
                debug=debug
            )
        if is_overlay_blocking(driver):
            try_accept_cookies(driver, wait)
            if is_overlay_blocking(driver):
                return ScrapeResult(
                    status=ScrapeStatus.BLOCKED,
                    reason=ScrapeReason.COOKIE_MODAL_BLOCKING,
                    flights=[],
                    min_price=-1,
                    debug=debug
                )
        # Verifica mensagem de "no results"
        if driver.find_elements(By.XPATH, '//div[contains(text(),"Não conseguimos encontrar")]'):
            return ScrapeResult(
                status=ScrapeStatus.EMPTY,
                reason=ScrapeReason.NO_RESULTS,
                flights=[],
                min_price=-1,
                debug=debug
            )
        sectors = driver.find_elements(By.CSS_SELECTOR, '[data-test="ResultCardSectorWrapper"]')
        if not sectors:
            return ScrapeResult(
                status=ScrapeStatus.EMPTY,
                reason=ScrapeReason.NO_RESULTS,
                flights=[],
                min_price=None,
                debug=debug
            )
        # Preenche voos e preços robustamente
        min_price, price_debug = compute_min_price(sectors[:max_results])
        for sector in sectors[:max_results]:
            try:
                times = sector.find_elements(By.CSS_SELECTOR, '[data-test="TripTimestamp"] time')
                hhmm = [t.text.strip() for t in times if re.match(r"^\d{1,2}:\d{2}$", (t.text or "").strip())]
                dep_time = hhmm[0] if len(hhmm) > 0 else "?"
                arr_time = hhmm[1] if len(hhmm) > 1 else "?"
                try:
                    duration_text = sector.find_element(By.CSS_SELECTOR, '.orbit-badge-primitive time').text
                except Exception:
                    duration_text = "?"
                try:
                    airline = sector.find_element(By.CSS_SELECTOR, '[data-test="ResultCardCarrierLogo"] img').get_attribute("alt")
                except Exception:
                    airline = "?"
                try:
                    stations = sector.find_elements(By.CSS_SELECTOR, '[data-test="stationName"]')
                    origin_code = stations[0].text if len(stations) > 0 else "?"
                    dest_code = stations[1].text if len(stations) > 1 else "?"
                except Exception:
                    origin_code = dest_code = "?"
                try:
                    stops = sector.find_element(By.CSS_SELECTOR, 'p[data-test^="StopCountBadge"]').text
                except Exception:
                    stops = "?"
                # Preço robusto
                price_int = find_price_for_sector(sector)
                flights.append({
                    "price_int": price_int,
                    "dep_time": dep_time,
                    "arr_time": arr_time,
                    "duration_text": duration_text,
                    "origin_code": origin_code,
                    "dest_code": dest_code,
                    "stops": stops,
                    "airline": airline,
                })
            except Exception:
                continue
        debug["price_debug"] = price_debug
        if not flights:
            # Salva HTML, screenshot e printa page_source para debug de página sem resultados
            try:
                from datetime import datetime
                import os
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname_html = f"debug_no_results_{ts}.html"
                with open(fname_html, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                debug["html"] = os.path.abspath(fname_html)
                fname_png = f"debug_no_results_{ts}.png"
                driver.save_screenshot(fname_png)
                debug["screenshot"] = os.path.abspath(fname_png)
                print("\n========== PAGE SOURCE (NO RESULTS) ==========")
                print(driver.page_source[:5000])
                print("========== END PAGE SOURCE ==========")
            except Exception as e:
                debug["debug_save_error"] = str(e)
            return ScrapeResult(
                status=ScrapeStatus.EMPTY,
                reason=ScrapeReason.NO_RESULTS,
                flights=[],
                min_price=min_price,
                debug=debug
            )
        # Validação obrigatória: min_price não pode ser None
        if min_price is None:
            # Diagnóstico visual opcional: screenshot
            try:
                from datetime import datetime
                import os
                origin = debug.get("origin", "?")
                dest = debug.get("dest", "?")
                date = debug.get("date", datetime.now().strftime("%Y%m%d"))
                fname = f"debug_price_fail_{origin}_{dest}_{date}.png"
                driver.save_screenshot(fname)
                debug["screenshot"] = os.path.abspath(fname)
            except Exception as e:
                debug["screenshot_error"] = str(e)
            return ScrapeResult(
                status=ScrapeStatus.ERROR,
                reason=ScrapeReason.UNKNOWN,
                flights=flights,
                min_price=None,
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
            debug={"exception": str(e), "url": url}
        )


