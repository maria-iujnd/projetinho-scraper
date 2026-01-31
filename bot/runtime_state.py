import time
def should_send_alert(kind: str, ttl_seconds: int) -> bool:
    """
    Retorna True se pode enviar alerta desse tipo (rate limit por TTL).
    Salva timestamp do último alerta enviado por tipo em runtime_state.json.
    """
    state = load_runtime_state()
    now = int(time.time())
    key = f"last_alert_{kind}_ts"
    last = state.get(key, 0)
    if now - last >= ttl_seconds:
        state[key] = now
        save_runtime_state(state)
        return True
    return False
import json
import time
import os

RUNTIME_STATE_PATH = os.path.join(os.path.dirname(__file__), 'runtime_state.json')

def save_runtime_state(data: dict):
    data = dict(data)
    data['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    with open(RUNTIME_STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_runtime_state():
    try:
        with open(RUNTIME_STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}
