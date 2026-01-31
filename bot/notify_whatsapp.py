import os
import logging

def notify_admin(title: str, body: str, *, level: str = "WARN", admin_phone: str = None, admin_name: str = None) -> None:
    """
    Envia alerta para o admin via WhatsApp.
    """
    try:
        from bot.whatsapp_sender import send_whatsapp
        msg = f"[BOT ALERT] {title}\n\n{body}"
        if admin_phone:
            send_whatsapp(admin_phone, msg, urgent=True)
        elif admin_name:
            send_whatsapp(admin_name, msg, urgent=True)
        else:
            raise Exception("ADMIN_PHONE ou ADMIN_CONTACT_NAME não configurado")
    except Exception as e:
        logging.getLogger("kiwi_bot").error(f"[NOTIFY][WA] Falha ao notificar admin: {e}")
