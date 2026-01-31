from __future__ import annotations

import time
from typing import Dict, Any, Tuple, List

from selenium.common.exceptions import NoSuchWindowException, WebDriverException
from bot.browser import open_browser, close_browser
from bot.decision_engine import evaluate_offer_batch
from bot.dedupe import make_offer_id, make_dedupe_key
from bot.logging_setup import setup_logger
from bot.planner import plan_attempts
from bot.pricing_utils import brl
from bot.queue_store import load_queue, save_queue, enqueue_message, sort_queue, is_in_queue
from bot.reasons import AttemptReport
from bot.reporting import print_summary
from bot import viajala_scraper

try:
    from .. import routes_config as cfg
    from .. import state_store
except ImportError:
    import routes_config as cfg
    import state_store


SCRAPERS = {
    "viajala": viajala_scraper.scrape_with_selenium,
}


def _is_dead_window_exc(e: Exception) -> bool:
    msg = str(e).lower()
    return ("no such window" in msg) or ("web view not found" in msg)


def _resolve_provider(args) -> Tuple[str, Any]:
    provider = (getattr(args, "provider", None) or "viajala").lower()
    scraper = SCRAPERS.get(provider)
    if not scraper:
        raise ValueError(f"Provider desconhecido: {provider}")
    return provider, scraper


def _resolve_url_builder(provider: str):
    builder = getattr(cfg, "build_viajala_url_ow", None)
    if not builder:
        raise ValueError("build_viajala_url_ow não configurado em routes_config")
    return builder


def _duration_text_from_minutes(minutes: int | None) -> str | None:
    if minutes is None:
        return None
    hours = minutes // 60
    mins = minutes % 60
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


def _price_int_from_offer(offer: Dict[str, Any]) -> int | None:
    price = offer.get("price")
    if isinstance(price, int):
        return price
    price_int = offer.get("price_int")
    if isinstance(price_int, int):
        return price_int
    if isinstance(price, str):
        digits = "".join(ch for ch in price if ch.isdigit())
        return int(digits) if digits else None
    return None


def run(args) -> int:
    logger = setup_logger()
    start_time = time.time()
    queue, _ = load_queue(scope=args.scope)
    if len(queue) >= 20:
        logger.warning("[EXIT] fila cheia (queue size >= 20)")
        return 0

    driver = None
    reports = []
    counts_phase_reason: Dict[Tuple[str, str], int] = {}

    try:
        state_store.setup_database()

        provider, scraper = _resolve_provider(args)
        url_builder = _resolve_url_builder(provider)

        logger.info(
            f"[START] provider={provider} headless={args.headless} scope={args.scope} origin={args.origin} dest={args.dest}"
        )

        driver, meta = open_browser(
            headless=args.headless,
            scope=args.scope,
            kind=provider,
        )
        logger.info("[BROWSER] Chrome iniciado")
        logger.info(f"[BROWSER] meta={meta}")

        origin = args.origin
        if args.dest is None:
            logger.info("[INFO] Rodando em modo batch: dest=None (usando DAILY_DEST_IATA)")
        dests = [args.dest] if args.dest else cfg.DAILY_DEST_IATA

        config = {
            "PRICE_CEILINGS_OW": cfg.PRICE_CEILINGS_OW,
            "DEFAULT_PRICE_CEILING_OW": cfg.DEFAULT_PRICE_CEILING_OW,
            "build_url_ow": url_builder,
            "use_slugs": False,
            "date_window_days": getattr(cfg, "DATE_WINDOW_DAYS", 7),
            "weekdays_only": getattr(cfg, "WEEKDAYS_ONLY", False),
            "depart": getattr(args, "depart", None),
        }

        attempts, skip_reports = plan_attempts(
            origin=origin,
            dests=dests,
            config=config,
            state_store=state_store,
        )
        logger.info(f"[PLAN] attempts={len(attempts)}")
        reports.extend(skip_reports)
        for report in skip_reports:
            logger.info(
                f"[SKIP] {report.origin}->{report.dest} {report.date} {report.reason} {report.details}"
            )
            key = (report.phase, report.reason)
            counts_phase_reason[key] = counts_phase_reason.get(key, 0) + 1

        if attempts:
            logger.info(f"[INFO] Primeira URL a ser processada: {attempts[0]['url']}")

        total_collected = 0
        total_after_dedupe = 0
        total_enqueued = 0

        for attempt in attempts:
            url = attempt.get("url")
            ceiling = attempt["ceiling"]
            date = attempt["date"]
            dest = attempt["dest"]
            origin = attempt["origin"]

            logger.info(f"[ATTEMPT] origin={origin} dest={dest} date={date} url={url}")
            if not state_store.should_check(origin, dest, "OW", date, None):
                reports.append(
                    AttemptReport(
                        origin=origin,
                        dest=dest,
                        date=date,
                        phase="SKIP",
                        reason="COOLDOWN_ACTIVE",
                        details={"provider": provider},
                    )
                )
                counts_phase_reason[("SKIP", "COOLDOWN_ACTIVE")] = counts_phase_reason.get(
                    ("SKIP", "COOLDOWN_ACTIVE"),
                    0,
                ) + 1
                logger.info(f"[SKIP] cooldown active {origin}->{dest} {date}")
                continue
            if not url:
                reports.append(
                    AttemptReport(
                        origin=origin,
                        dest=dest,
                        date=date,
                        phase="SCRAPE",
                        reason="URL_MISSING",
                        details={"provider": provider},
                    )
                )
                counts_phase_reason[("SCRAPE", "URL_MISSING")] = counts_phase_reason.get(
                    ("SCRAPE", "URL_MISSING"),
                    0,
                ) + 1
                continue

            offers: List[Dict[str, Any]] = []
            try:
                offers = scraper(driver, origin, dest, date, max_cards=30)
            except NoSuchWindowException as e:
                close_browser(driver)
                driver, meta = open_browser(headless=args.headless, scope=args.scope, kind=provider)
                offers = []
                logger.warning("[SCRAPE] selenium window error: %s", e)
            except WebDriverException as e:
                if _is_dead_window_exc(e):
                    close_browser(driver)
                    driver, meta = open_browser(headless=args.headless, scope=args.scope, kind=provider)
                offers = []
                logger.warning("[SCRAPE] selenium error: %s", e)
            except Exception as e:
                offers = []
                logger.warning("[SCRAPE] error: %s", e)

            total_collected += len(offers)

            if not offers:
                state_store.mark_no_data(origin, dest, "OW", date, None, cooldown_hours=1)
                reports.append(
                    AttemptReport(
                        origin=origin,
                        dest=dest,
                        date=date,
                        phase="SCRAPE",
                        reason="NO_DATA",
                        details={"provider": provider},
                    )
                )
                counts_phase_reason[("SCRAPE", "NO_DATA")] = counts_phase_reason.get(
                    ("SCRAPE", "NO_DATA"),
                    0,
                ) + 1
                logger.info(f"[SCRAPE] no offers {origin}->{dest} {date}")
                continue

            normalized: List[Dict[str, Any]] = []
            for offer in offers:
                offer["provider"] = offer.get("provider") or provider
                offer["origin"] = offer.get("origin") or origin
                offer["destination"] = offer.get("destination") or dest
                offer["depart_date"] = offer.get("depart_date") or date
                offer["origin_code"] = offer.get("origin_code") or origin
                offer["dest_code"] = offer.get("dest_code") or dest

                price_int = _price_int_from_offer(offer)
                if price_int is not None:
                    offer["price_int"] = price_int
                    offer["price"] = f"R$ {brl(price_int)}"

                if not offer.get("duration_text"):
                    offer["duration_text"] = _duration_text_from_minutes(offer.get("duration_min"))

                normalized.append(offer)

            prices = [o.get("price_int") for o in normalized if o.get("price_int") is not None]
            min_price = min(prices) if prices else None
            if min_price is None:
                state_store.mark_no_data(origin, dest, "OW", date, None, cooldown_hours=1)
                logger.info(f"[SCRAPE] offers without price {origin}->{dest} {date}")
                continue

            state_store.mark_good(origin, dest, "OW", date, None, min_price)

            deduped: List[Dict[str, Any]] = []
            for offer in normalized:
                offer_id = make_offer_id(offer)
                dedupe_key = make_dedupe_key(offer_id, channel="WHATSAPP", kind="ALERT")
                offer["offer_id"] = offer_id
                offer["dedupe_key"] = dedupe_key
                if is_in_queue(queue, dedupe_key):
                    logger.debug("[DEDUPE] queue duplicate key=%s", dedupe_key)
                    continue
                if state_store.was_seen_recently(dedupe_key, ttl_seconds=24 * 3600):
                    logger.debug("[DEDUPE] ttl duplicate key=%s", dedupe_key)
                    continue
                deduped.append(offer)

            total_after_dedupe += len(deduped)

            if not deduped:
                reports.append(
                    AttemptReport(
                        origin=origin,
                        dest=dest,
                        date=date,
                        phase="DECISION",
                        reason="DUPLICATE",
                        details={"provider": provider},
                    )
                )
                counts_phase_reason[("DECISION", "DUPLICATE")] = counts_phase_reason.get(
                    ("DECISION", "DUPLICATE"),
                    0,
                ) + 1
                continue

            result = evaluate_offer_batch(
                flights=deduped,
                min_price=min_price,
                ceiling=ceiling,
                origin=origin,
                dest=dest,
                depart_date=date,
                queue=queue,
                state_store=state_store,
            )

            reports.append(
                AttemptReport(
                    origin=origin,
                    dest=dest,
                    date=date,
                    phase="DECISION",
                    reason=getattr(result, "reason", "UNKNOWN"),
                    details={},
                )
            )
            logger.info(
                f"[DECISION] {origin}->{dest} {date} reason={getattr(result, 'reason', 'UNKNOWN')} "
                f"should_enqueue={getattr(result, 'should_enqueue', False)}"
            )
            key = ("DECISION", getattr(result, "reason", "UNKNOWN"))
            counts_phase_reason[key] = counts_phase_reason.get(key, 0) + 1

            if getattr(result, "should_enqueue", False):
                enqueue_message(
                    queue,
                    result.message_text,
                    result.dedupe_key,
                    result.priority,
                    meta={
                        "origin": origin,
                        "dest": dest,
                        "provider": provider,
                        "date": date,
                        "min_price": min_price,
                        "route": f"{origin}-{dest}",
                    },
                )
                logger.info(
                    f"[ENQUEUE] dedupe_key={result.dedupe_key} priority={result.priority} queue_size={len(queue)}"
                )
                total_enqueued += 1
                if hasattr(state_store, "mark_seen"):
                    state_store.mark_seen(result.dedupe_key)

        queue = sort_queue(queue)
        save_queue(queue, scope=args.scope)
        logger.info(f"[QUEUE] final size={len(queue)}")
        logger.info(
            "[SUMMARY] attempts=%s collected=%s deduped=%s enqueued=%s",
            len(attempts),
            total_collected,
            total_after_dedupe,
            total_enqueued,
        )
        try:
            from bot.queue_models import queue_stats

            stats = queue_stats(queue)
            logger.info(
                "[QUEUE] stats: total=%s approved=%s pending=%s sent=%s dropped=%s top5=%s",
                stats.get("total"),
                stats.get("approved"),
                stats.get("pending"),
                stats.get("sent"),
                stats.get("dropped"),
                stats.get("top5_priorities"),
            )
        except Exception:
            stats = {}

        logger.info("[SUMMARY] Contadores por fase/motivo:")
        for (phase, reason), count in sorted(counts_phase_reason.items()):
            logger.info(f"  {phase}:{reason} = {count}")
        print_summary(reports)
        duration = time.time() - start_time
        logger.info(f"[END] Duração total: {duration:.1f}s")
        try:
            from bot.runtime_state import save_runtime_state

            save_runtime_state(
                {
                    "counts": {
                        f"{phase}:{reason}": count
                        for (phase, reason), count in counts_phase_reason.items()
                    },
                    "queue": stats,
                    "duration": duration,
                }
            )
        except Exception:
            pass
        return 0

    except ValueError as e:
        logger.error(f"[CONFIG] {e}")
        return 2
    except Exception as e:
        logger.error(f"[CRASH] {type(e).__name__}: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return 1
    finally:
        close_browser(driver)
