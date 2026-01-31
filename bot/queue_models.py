import time
from typing import List, Dict
from dataclasses import dataclass, asdict

@dataclass
class QueueItem:
    id: str  # dedupe_key
    created_ts: int  # unix timestamp
    priority: int
    channel: str
    text: str
    status: str  # PENDING, APPROVED, SENT, DROPPED
    meta: dict = None
    group: str = None  # grupo WhatsApp alvo

def sort_queue(items):
    status_order = {"APPROVED": 0, "PENDING": 1, "SENT": 2, "DROPPED": 3}

    def get_status(x):
        return x.status if hasattr(x, "status") else x.get("status", "PENDING")

    def get_priority(x):
        return x.priority if hasattr(x, "priority") else x.get("priority", 0)

    def get_created(x):
        return x.created_ts if hasattr(x, "created_ts") else x.get("created_ts", 0)

    return sorted(items, key=lambda x: (status_order.get(get_status(x), 99), -get_priority(x), get_created(x)))

def dequeue_sendable(items: List[QueueItem], limit: int) -> List[QueueItem]:
    sendable = [x for x in sort_queue(items) if x.status == "APPROVED"]
    return sendable[:limit]

def mark_sent(items: List[QueueItem], id: str):
    for x in items:
        if x.id == id:
            x.status = "SENT"
            break

def mark_dropped(items: List[QueueItem], id: str, reason: str = ""): 
    for x in items:
        if x.id == id:
            x.status = "DROPPED"
            if x.meta is not None:
                x.meta["drop_reason"] = reason
            break

def mark_approved(items: List[QueueItem], id: str):
    for x in items:
        if x.id == id:
            x.status = "APPROVED"
            break

def queue_stats(items: List[QueueItem]) -> dict:
    total = len(items)
    approved = sum(1 for x in items if x.status == "APPROVED")
    pending = sum(1 for x in items if x.status == "PENDING")
    sent = sum(1 for x in items if x.status == "SENT")
    dropped = sum(1 for x in items if x.status == "DROPPED")
    top5 = sorted(items, key=lambda x: -x.priority)[:5]
    return {
        "total": total,
        "approved": approved,
        "pending": pending,
        "sent": sent,
        "dropped": dropped,
        "top5_priorities": [x.priority for x in top5],
    }
