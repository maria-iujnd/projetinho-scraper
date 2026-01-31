import time
import state_store
from typing import List, Tuple
from date_utils import format_date_for_user  # Regra: toda data exibida ao usuário DEVE passar por esta função

# ATENÇÃO: NUNCA monte datas manualmente para o usuário!
# Sempre use format_date_for_user(dt) para exibir datas em mensagens, logs ou relatórios para o usuário final.

def enqueue_message(queue: List[Tuple[str, str]], text: str, offer_hash: str):
    """
    Enfileira uma mensagem se o offer_hash não tiver sido anunciado recentemente.
    """
    if not state_store.was_announced_recently(offer_hash, hours=72):
        queue.append((text, offer_hash))

def send_with_spacing(queue: List[Tuple[str, str]], min_seconds: int = 120, max_per_hour: int = 10):
    """
    Envia as mensagens da fila respeitando um espaçamento (Stub).
    """
    if not queue:
        return

    print(f"\n--- Iniciando envio de {len(queue)} mensagens acumuladas ---")
    for text, offer_hash in queue:
        print(f"[ENVIANDO] {text}")
        # Aqui entraria a lógica real de envio (Telegram, WhatsApp, etc)
        state_store.mark_as_announced(offer_hash)
        # time.sleep(min_seconds) # Comentado pois é apenas um stub
    print("--- Envio concluído ---")