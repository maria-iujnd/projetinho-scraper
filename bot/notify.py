import os
import time
import logging

_ALERT_TTLS = {
    "START": 0,
    "CYCLE_FAIL": 600,
    "HEALTHCHECK_FAIL": 1800,
    "BROWSER_RESTART": 600,
    "SERVICE_EXIT": 0,
}

def notify_admin(title: str, body: str, level: str = "INFO", alert_type: str = None) -> None:
    """
    Envia alerta para o admin (WhatsApp). Usa rate limit por tipo.
    """
    try:
        from bot.notify_whatsapp import notify_admin as notify_admin_whatsapp
        from bot.runtime_state import should_send_alert
        alert_type = (alert_type or title or "GENERIC").upper().replace(" ", "_")
        ttl = _ALERT_TTLS.get(alert_type, 600)
        if ttl > 0 and not should_send_alert(alert_type.lower(), ttl):
            logging.getLogger("kiwi_bot").info(f"[NOTIFY] rate limit: {alert_type}")
            return
        admin_phone = os.environ.get("ADMIN_PHONE")
        admin_name = os.environ.get("ADMIN_CONTACT_NAME", "ADMIN")
        if not admin_phone and not admin_name:
            raise Exception("ADMIN_PHONE ou ADMIN_CONTACT_NAME não configurado")
        notify_admin_whatsapp(title, body, level=level, admin_phone=admin_phone, admin_name=admin_name)
    except Exception as e:
        logging.getLogger("kiwi_bot").error(f"[NOTIFY] Falha ao notificar admin: {e}")
