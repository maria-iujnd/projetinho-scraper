import os
import time
import json
from typing import Optional

STATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'send_rate_state.json')

def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def can_send_group(group: str, min_interval: int) -> (bool, int):
    state = _load_state()
    now = int(time.time())
    last = state.get(f'group_{group}', 0)
    wait = min_interval - (now - last)
    if wait > 0:
        return False, wait
    state[f'group_{group}'] = now
    _save_state(state)
    return True, 0

def can_send_route(route_key: str, min_interval: int) -> (bool, int):
    state = _load_state()
    now = int(time.time())
    last = state.get(f'route_{route_key}', 0)
    wait = min_interval - (now - last)
    if wait > 0:
        return False, wait
    state[f'route_{route_key}'] = now
    _save_state(state)
    return True, 0
