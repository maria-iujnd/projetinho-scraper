# countdown_control.py
"""
Funções para ativar/desativar (ON/STOP) o controle de cooldown global do bot.
Permite pausar ou liberar todos os cooldowns temporariamente, sem alterar o banco permanentemente.
"""

import threading

# Estado global do countdown (cooldown)
_countdown_enabled = True
_countdown_lock = threading.Lock()

def enable_countdown():
    """Ativa o controle de cooldown (ON)."""
    global _countdown_enabled
    with _countdown_lock:
        _countdown_enabled = True

def disable_countdown():
    """Desativa o controle de cooldown (STOP): ignora todos os cooldowns temporariamente."""
    global _countdown_enabled
    with _countdown_lock:
        _countdown_enabled = False

def is_countdown_enabled() -> bool:
    """Retorna True se o controle de cooldown está ativo (ON)."""
    with _countdown_lock:
        return _countdown_enabled
