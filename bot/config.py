# Configs de serviço/daemon
SERVICE_ENABLED = True
POLL_INTERVAL_SECONDS = 300  # 5 min
CYCLE_MAX_SECONDS = 240
MAX_CONSECUTIVE_FAILURES = 5
import tempfile
from pathlib import Path
SERVICE_HEARTBEAT_PATH = str(Path(tempfile.gettempdir()) / "kiwi_bot_heartbeat.json")
# Configurações de governança da fila
QUEUE_MAX_SIZE = 50
QUEUE_DROP_POLICY = "drop_lowest"  # ou "drop_new"
QUEUE_MIN_PRIORITY_TO_KEEP = 150
MODERATION_ENABLED = False
AUTO_APPROVE_MIN_PRIORITY = 600


# --- NOVOS LIMITES E RITMO DE ENVIO ---
# 5 janelas diárias, 4 por hora por grupo, spacing 180s
SEND_TZ = "America/Recife"
SEND_WINDOWS = "08:00-09:00,11:00-12:00,14:00-15:00,17:00-18:00,20:00-21:00"
MAX_PER_HOUR_PER_GROUP = 4
MIN_SECONDS_BETWEEN_MESSAGES_PER_GROUP = 180

def get_dest_list(mode, dest_filter=None):
    # TODO: migrar lógica de construção de lista de destinos
    return []
