#!/usr/bin/env python3
"""
Orquestrador do bot: executa scraper → sender com lock e política de falha.

Uso:
  python run_all.py [--scope SCOPE]
  
Ou com agendamento via cron:
  0 */3 * * * cd /path/to/script && python run_all.py

Lock: cria run_all.lock para evitar execuções simultâneas.
Política de falha:
  - Se scraper falha (exit != 0), não roda sender
  - Se sender falha, fila fica para próxima tentativa
"""
import os
import sys
import subprocess
import datetime
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = os.path.join(BASE_DIR, "run_all.lock")

def log(level: str, msg: str) -> None:
    """Log com timestamp."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")

def acquire_lock() -> bool:
    """
    Tenta adquirir lock atomicamente.
    Retorna True se sucesso, False se lock já existe.
    """
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        # Escreve PID e timestamp no lock
        os.write(fd, f"{os.getpid()}\n{datetime.datetime.now().isoformat()}\n".encode())
        os.close(fd)
        return True
    except FileExistsError:
        # Lock já existe
        try:
            with open(LOCK_FILE, 'r') as f:
                lock_content = f.read().strip()
            log("WARN", f"Lock já existe (PID da execução anterior):\n{lock_content}")
        except Exception:
            log("WARN", "Lock já existe (conteúdo ilegível)")
        return False

def release_lock() -> None:
    """Remove lock file."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            log("INFO", "Lock liberado")
    except Exception as e:
        log("ERROR", f"Erro ao liberar lock: {e}")

def handle_signal(sig, frame):
    """Handler para sinais (SIGINT, SIGTERM)."""
    log("WARN", f"Recebido sinal {sig}, limpando...")
    release_lock()
    sys.exit(130)

def run_script(script_name: str, args: list) -> int:
    """
    Executa script via subprocess.
    Retorna exit code.
    """
    cmd = [sys.executable, os.path.join(BASE_DIR, script_name)] + args
    log("INFO", f"Executando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=BASE_DIR)
        exit_code = result.returncode
        log("INFO", f"{script_name} terminou com exit code: {exit_code}")
        return exit_code
    except Exception as e:
        log("ERROR", f"Erro ao executar {script_name}: {e}")
        return 1

def main() -> int:
    # Parse args
    scope = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith("--scope="):
            scope = arg.split("=", 1)[1]
        elif arg == "--scope" and i < len(sys.argv) - 1:
            scope = sys.argv[i + 1]

    # Setup signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    log("INFO", "=== Bot Orquestrador Iniciado ===")
    if scope:
        log("INFO", f"Escopo: {scope}")

    # Tenta adquirir lock
    if not acquire_lock():
        log("ERROR", "Não foi possível adquirir lock. Outra instância pode estar rodando.")
        return 1

    log("INFO", "Lock adquirido")

    try:
        # 1. Roda scraper
        log("INFO", "--- Fase 1: Scraper ---")
        scraper_args = []
        if scope:
            scraper_args.extend(["--scope", scope])
        
        scraper_exit = run_script("scrape_kiwi.py", scraper_args)
        
        if scraper_exit != 0:
            log("ERROR", f"Scraper falhou (exit {scraper_exit}). Sender não será executado.")
            return 1

        log("INFO", "Scraper completado com sucesso")

        # 2. Roda sender
        log("INFO", "--- Fase 2: Sender ---")
        sender_args = []
        if scope:
            sender_args.extend(["--scope", scope])
        
        sender_exit = run_script("whatsapp_sender.py", sender_args)
        
        if sender_exit != 0:
            log("WARN", f"Sender falhou (exit {sender_exit}). Fila mantida para próxima tentativa.")
            # Não retorna erro; sender é idempotente
            return 0

        log("INFO", "Sender completado com sucesso")
        log("INFO", "=== Bot Orquestrador Finalizado (sucesso) ===")
        return 0

    except Exception as e:
        log("ERROR", f"Exceção não capturada: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        release_lock()

if __name__ == "__main__":
    sys.exit(main())