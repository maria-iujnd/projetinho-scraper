from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict

class SkipReason(Enum):
    COOLDOWN_ACTIVE = auto()
    NO_ELIGIBLE_DATES = auto()
    CONFIG_DISABLED = auto()
    RATE_LIMIT = auto()

class ScrapeReason(Enum):
    COOKIE_BLOCKING = auto()
    NO_RESULTS = auto()
    TIMEOUT = auto()
    SELENIUM_ERROR = auto()
    PAGE_LOAD_ERROR = auto()

class DecisionReason(Enum):
    ABOVE_CEILING = auto()
    DUPLICATE = auto()
    NO_BEST_BUCKETS = auto()
    NO_PRICE = auto()
    OK = auto()

@dataclass
class AttemptReport:
    origin: str
    dest: str
    date: Optional[str]
    phase: str  # SKIP/SCRAPE/DECISION
    reason: str
    details: Optional[Dict] = field(default_factory=dict)
