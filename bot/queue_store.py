import json
import os
def load_queue(scope=None):
    path = os.path.join(os.path.dirname(__file__), '..', 'queue_messages.json')
    path = os.path.abspath(path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            queue = json.load(f)
        # Monta set de dedupe_keys para O(1) lookup
        queue_keys_set = set(item.get("dedupe_key") for item in queue if item.get("dedupe_key"))
        return queue, queue_keys_set
    except Exception:
        return [], set()

def save_queue(queue, scope=None):
    path = os.path.join(os.path.dirname(__file__), '..', 'queue_messages.json')
    path = os.path.abspath(path)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[QUEUE][ERRO] Falha ao salvar fila: {e}")


def sort_queue(queue):
    # Ordenação forte: status, prioridade, created_ts
    status_order = {"APPROVED": 0, "PENDING": 1, "SENT": 2, "DROPPED": 3}
    def get_status(x):
        return x.status if hasattr(x, "status") else x.get("status", "PENDING")
    def get_priority(x):
        return x.priority if hasattr(x, "priority") else x.get("priority", 0)
    def get_created(x):
        return x.created_ts if hasattr(x, "created_ts") else x.get("created_ts", 0)
    return sorted(
        queue,
        key=lambda x: (
            status_order.get(get_status(x), 99),
            -get_priority(x),
            get_created(x)
        )
    )


import datetime
import logging
from bot.config import QUEUE_MAX_SIZE, QUEUE_DROP_POLICY, QUEUE_MIN_PRIORITY_TO_KEEP, MODERATION_ENABLED, AUTO_APPROVE_MIN_PRIORITY
from bot.queue_models import QueueItem, sort_queue

def enqueue_message(queue, msg, dedupe_key, priority=0.0, group=None, channel="WHATSAPP", meta=None):
    logger = logging.getLogger("kiwi_bot")
    # Dedupe na fila
    if any(x.get("dedupe_key") == dedupe_key for x in queue):
        logger.info(f"[QUEUE] dedupe: já existe dedupe_key={dedupe_key}")
        return "DUPLICATE"
    # Status/moderação
    status = "APPROVED"
    if MODERATION_ENABLED:
        status = "APPROVED" if priority >= AUTO_APPROVE_MIN_PRIORITY else "PENDING"
    # Roteamento de grupo
    target_group = group
    dest = None
    if meta and isinstance(meta, dict):
        dest = meta.get("dest") or meta.get("dest_iata")
    if not target_group and dest:
        try:
            from bot.group_router import resolve_group_for_dest
            target_group = resolve_group_for_dest(dest)
            logger.info(f"[ROUTING] origin={meta.get('origin','?')} dest={dest} group={target_group}")
        except Exception as e:
            logger.warning(f"[ROUTING] erro ao resolver grupo para dest={dest}: {e}")
            target_group = "GERAL"
    # Monta item
    now = int(datetime.datetime.now().timestamp())
    item = QueueItem(
        id=dedupe_key,
        created_ts=now,
        priority=int(priority),
        channel=channel,
        text=str(msg),
        status=status,
        meta=meta or {}
    )
    # Adiciona target_group ao item
    if target_group:
        if not hasattr(item, 'group'):
            setattr(item, 'group', target_group)
        else:
            item.group = target_group
    # Limite e política
    if len(queue) < QUEUE_MAX_SIZE:
        queue.append(item)
        logger.info(f"[QUEUE] enfileirado dedupe_key={dedupe_key} status={status} priority={priority} group={target_group}")
        return "ENQUEUED"
    # Fila cheia
    if QUEUE_DROP_POLICY == "drop_lowest":
        # Encontra o item de menor prioridade
        sorted_q = sort_queue(queue)
        lowest = sorted_q[-1]
        if item.priority > lowest.priority:
            queue.remove(lowest)
            queue.append(item)
            logger.warning(f"[QUEUE] full policy=drop_lowest dropped={lowest.id} new={item.id}")
            return "DROPPED_LOWEST"
        else:
            logger.warning(f"[QUEUE] full policy=drop_lowest drop_new new={item.id} (priority={item.priority})")
            return "DROP_NEW"
    elif QUEUE_DROP_POLICY == "drop_new":
        logger.warning(f"[QUEUE] full policy=drop_new drop_new new={item.id}")
        return "DROP_NEW"
    else:
        logger.warning(f"[QUEUE] full policy=unknown, drop_new new={item.id}")
        return "DROP_NEW"

def is_in_queue(queue, dedupe_key):
    def prune_queue_sent(queue_path=None, older_than_days=7):
        """Remove itens da fila com status SENT mais antigos que X dias."""
        import time
        path = queue_path or os.path.join(os.path.dirname(__file__), '..', 'queue_messages.json')
        path = os.path.abspath(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                queue = json.load(f)
        except Exception:
            return 0
        now = int(time.time())
        cutoff = now - older_than_days * 86400
        new_queue = [item for item in queue if not (item.get('status') == 'SENT' and item.get('created_ts', 0) < cutoff)]
        removed = len(queue) - len(new_queue)
        if removed > 0:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_queue, f, ensure_ascii=False, indent=2)
        return removed
    # Verifica se a dedupe_key já está na fila
    return any(item.get("dedupe_key") == dedupe_key for item in queue)
