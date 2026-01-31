from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Dict

class ScrapeStatus(Enum):
    OK = auto()
    EMPTY = auto()
    BLOCKED = auto()
    ERROR = auto()

class ScrapeReason(Enum):
    BLOCKED_CHALLENGE = auto()           # Sinais de challenge/captcha/cloudflare
    TIMEOUT_WAITING_RESULTS = auto()     # Timeout esperando container de resultados
    NO_RESULTS = auto()                  # Container presente, lista vazia/texto "nenhum resultado"
    PAGE_NOT_LOADED = auto()             # Legado/fallback
    COOKIE_MODAL_BLOCKING = auto()
    SELENIUM_EXCEPTION = auto()
    UNKNOWN = auto()

@dataclass
class ScrapeResult:
    status: ScrapeStatus
    reason: ScrapeReason
    flights: List[dict] = field(default_factory=list)
    min_price: int = -1
    debug: Optional[Dict] = field(default_factory=dict)
