from bot.reasons import SkipReason, AttemptReport
from typing import List, Tuple
import datetime

def plan_attempts(*, origin, dests, config, state_store) -> Tuple[list, list]:
    """
    Retorna:
      - attempts: lista de dicts (origin, dest, date, ceiling, url, ...)
      - reports: lista de AttemptReport (SKIP)
    """
    attempts = []
    reports = []
    from routes_config import IATA_TO_SLUG
    for dest in dests:
        # Se config['depart'] estiver presente, usa só essa data
        depart = config.get('depart')
        if depart:
            try:
                date_obj = datetime.datetime.strptime(depart, "%Y-%m-%d").date()
                eligible_dates = [date_obj]
            except Exception:
                eligible_dates = []
        else:
            today = datetime.date.today()
            eligible_dates = [today + datetime.timedelta(days=i) for i in range(config.get('date_window_days', 7))]
            if config.get('weekdays_only'):
                eligible_dates = [d for d in eligible_dates if d.weekday() < 5]
        if not eligible_dates:
            reports.append(AttemptReport(
                origin=origin,
                dest=dest,
                date=None,
                phase="SKIP",
                reason=SkipReason.NO_ELIGIBLE_DATES.name,
                details={"date_window_days": config.get('date_window_days', 7), "weekdays_only": config.get('weekdays_only', False)}
            ))
            continue
        for date in eligible_dates:
            date_str = date.isoformat()
            cooldown_key = f"{origin}|{dest}|{date_str}"
            if hasattr(state_store, "is_in_cooldown") and state_store.is_in_cooldown(cooldown_key):
                reports.append(AttemptReport(
                    origin=origin,
                    dest=dest,
                    date=date_str,
                    phase="SKIP",
                    reason=SkipReason.COOLDOWN_ACTIVE.name,
                    details={"cooldown_key": cooldown_key}
                ))
                continue
            # Monta attempt usando slugs apenas quando necessário
            use_slugs = config.get('use_slugs', False)
            origin_slug = IATA_TO_SLUG.get(origin, origin) if use_slugs else origin
            dest_slug = IATA_TO_SLUG.get(dest, dest) if use_slugs else dest
            url_builder = config.get('build_url_ow') or config.get('build_kiwi_url_ow')
            attempt = {
                "origin": origin,
                "dest": dest,
                "date": date_str,
                "ceiling": config.get('PRICE_CEILINGS_OW', {}).get(dest, config.get('DEFAULT_PRICE_CEILING_OW', 9999)),
                "url": url_builder(origin_slug, dest_slug, date_str, sort_by_price=True) if url_builder else None
            }
            attempts.append(attempt)
    return attempts, reports
