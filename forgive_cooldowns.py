# forgive_cooldowns.py
"""
Script utilitário para perdoar (resetar) todos os cooldowns do bot, liberando todas as datas imediatamente.
Uso: python forgive_cooldowns.py
"""
import state_store
import settings
import sqlite3
from datetime import datetime

def forgive_all_cooldowns(db_path=None):
    db_path = db_path or settings.db_file(None)
    now_iso = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE route_date_state SET cooldown_until = ?", (now_iso,))
        conn.commit()
    print("Todos os cooldowns foram perdoados!")

if __name__ == "__main__":
    forgive_all_cooldowns()
