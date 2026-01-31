import time
import sys
import traceback
from bot.runner import run as run_one_cycle
from bot.logging_setup import setup_logger
from bot.healthcheck import write_heartbeat
from bot.config import POLL_INTERVAL_SECONDS, CYCLE_MAX_SECONDS, MAX_CONSECUTIVE_FAILURES, SERVICE_HEARTBEAT_PATH

def run_forever():
    logger = setup_logger()
    failures = 0
    need_browser_restart = False
    last_prune_day = None
    from bot.notify import notify_admin
    # Notifica início do serviço
    notify_admin("START", f"Bot iniciado em {time.strftime('%Y-%m-%d %H:%M:%S')}", alert_type="START")
    while True:
        cycle_start = time.time()
        status = "OK"
        last_error = None
        try:
            logger.info("[SERVICE] Iniciando ciclo do bot...")
            # Timeout watchdog
            result = None
            try:
                result = run_one_cycle()
            except Exception as e:
                status = "EXCEPTION"
                last_error = str(e)
                logger.error(f"[SERVICE] Exception: {e}")
                logger.error(traceback.format_exc())
                failures += 1
                # Notifica falha de ciclo
                notify_admin("CYCLE_FAIL", f"Falha no ciclo em {time.strftime('%Y-%m-%d %H:%M:%S')}\nErro: {last_error}", alert_type="CYCLE_FAIL")
            duration = time.time() - cycle_start
            if duration > CYCLE_MAX_SECONDS:
                logger.warning(f"[WATCHDOG] cycle_timeout: {duration:.1f}s > {CYCLE_MAX_SECONDS}s")
                status = "TIMEOUT"
                failures += 1
            else:
                if status == "OK":
                    failures = 0
                    # Notifica ciclo OK (opcional, pode comentar se não quiser)
                    #notify_admin("CYCLE_OK", f"Ciclo OK em {time.strftime('%Y-%m-%d %H:%M:%S')}", alert_type="CYCLE_OK")
            # Prune automático 1x/dia
            today = time.strftime("%Y-%m-%d")
            if last_prune_day != today:
                try:
                    from state_store import prune_seen, prune_history
                    from bot.queue_store import prune_queue_sent
                    n_seen = prune_seen(older_than_seconds=30*86400)
                    n_hist = prune_history(older_than_days=90)
                    n_queue = prune_queue_sent(older_than_days=7)
                    logger.info(f"[PRUNE] seen={n_seen} history={n_hist} queue_sent={n_queue}")
                except Exception as e:
                    logger.error(f"[PRUNE] erro: {e}")
                last_prune_day = today
            # Heartbeat
            write_heartbeat(SERVICE_HEARTBEAT_PATH, {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "last_cycle_status": status,
                "duration": duration,
                "failures": failures,
                "last_error": last_error,
            })
            if failures >= MAX_CONSECUTIVE_FAILURES:
                logger.error(f"[SERVICE] too_many_failures={failures} exiting for systemd restart")
                try:
                    from bot.runtime_state import should_send_alert
                    if should_send_alert("failures", 600):  # 10 min
                        body = f"failures={failures}\nlast_error={last_error}\naction=service exiting (systemd restart)\nlog=/var/log/kiwi_bot.log"
                        notify_admin("SERVICE_EXIT", body, alert_type="SERVICE_EXIT")
                except Exception as e:
                    logger.error(f"[NOTIFY] erro ao notificar admin: {e}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"[SERVICE] Outer exception: {e}")
            logger.error(traceback.format_exc())
            try:
                notify_admin("SERVICE_EXIT", f"Exceção fatal: {e}", alert_type="SERVICE_EXIT")
            except Exception:
                pass
            sys.exit(2)
        logger.info(f"[SERVICE] Ciclo finalizado. Dormindo {POLL_INTERVAL_SECONDS}s...")
        time.sleep(POLL_INTERVAL_SECONDS)
