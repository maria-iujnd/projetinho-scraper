from bot.browser import open_browser, close_browser, warm_start
from bot.google_flights_scraper import scrape_with_selenium
from bot.google_flights_urls import build_google_flights_url_ow
from bot.decision_engine import evaluate_offer_batch
from bot.message_builder import build_grouped_message
import routes_config as cfg

def run_smoke_test(*, origin: str, dest: str, date: str, ceiling: int) -> dict:
    """
    Retorna um relatório com:
      - ok: bool
      - stage: str (BROWSER / SCRAPE_BASE / DECISION / MESSAGE)
      - reason: str
      - details: dict
    """
    details = {}
    # 1. Browser
    try:
        # Caminho do profile real (ajustado para seu ambiente)
        driver, wait = open_browser(headless=False, kind="google")
        warm_start(driver)
    except Exception as e:
        return dict(ok=False, stage="BROWSER", reason=f"BROWSER_ERROR: {e}", details={})
    try:
        # 2. URL
        origin_slug = origin
        dest_slug = dest
        url = build_google_flights_url_ow(origin_slug, dest_slug, date, sort_by_price=True)
        details["url"] = url
        # 3. Scraping base
        result = scrape_with_selenium(driver, wait, url, ceiling)
        details["scrape_status"] = getattr(result, "status", None)
        details["scrape_reason"] = getattr(result, "reason", None)
        details["min_price"] = getattr(result, "min_price", None)
        flights = getattr(result, "flights", [])
        details["flights_count"] = len(flights)
        if not flights or result.min_price is None:
            close_browser(driver)
            return dict(ok=False, stage="SCRAPE_BASE", reason=f"NO_FLIGHTS_OR_PRICE", details=details)
        # 4. Decision
        queue = []
        import state_store
        state_store.setup_database()
        decision = evaluate_offer_batch(
            flights=flights,
            min_price=result.min_price,
            ceiling=ceiling,
            origin=origin_slug,
            dest=dest_slug,
            depart_date=date,
            queue=queue,
            state_store=state_store
        )
        details["decision_reason"] = getattr(decision, "reason", None)
        details["should_enqueue"] = getattr(decision, "should_enqueue", False)
        # 5. Message (apenas se for enviar)
        if getattr(decision, "should_enqueue", False):
            msg = build_grouped_message([flights[0]])
            details["message_text"] = msg
            if not msg.strip():
                close_browser(driver)
                return dict(ok=False, stage="MESSAGE", reason="EMPTY_MESSAGE", details=details)
        close_browser(driver)
        return dict(ok=True, stage="OK", reason="PASS", details=details)
    except Exception as e:
        close_browser(driver)
        return dict(ok=False, stage="EXCEPTION", reason=str(e), details=details)
