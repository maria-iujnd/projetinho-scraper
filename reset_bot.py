#!/usr/bin/env python3
import os
import json
import state_store

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILE = os.path.join(BASE_DIR, "queue_messages.json")

def main():
    state_store.setup_database()
    state_store.reset_all_state()
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    print("[RESET] Banco e fila zerados. Pronto para recomeçar do zero.")

if __name__ == "__main__":
    main()
