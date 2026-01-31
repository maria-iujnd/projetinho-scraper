import json
import time

def write_heartbeat(path: str, data: dict):
    """
    Escreve JSON pequeno com timestamp, status, queue_size, last_error, etc.
    """
    data = dict(data)
    data["heartbeat_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        pass
