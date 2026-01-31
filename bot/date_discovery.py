from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional


def smart_depart_dates(
    start: Optional[str] = None,
    days: int = 30,
    weekdays_only: bool = False,
) -> List[str]:
    """
    Gera uma lista de datas (YYYY-MM-DD) a partir de start (YYYY-MM-DD) ou hoje.
    - days: quantidade de dias à frente
    - weekdays_only: se True, remove sáb/dom
    """
    if start:
        d0 = datetime.strptime(start, "%Y-%m-%d").date()
    else:
        d0 = date.today()

    out: List[str] = []
    for i in range(days):
        d = d0 + timedelta(days=i)
        if weekdays_only and d.weekday() >= 5:
            continue
        out.append(d.isoformat())
    return out
