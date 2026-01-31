#!/usr/bin/env python3
"""
Watchdog/Monitor para o bot de passagens.
Monitora logs, alertas de falha, e status geral.

Uso: python monitor.py [--log-file LOG] [--alert-on-error]
"""
import os
import sys
import datetime
from pathlib import Path

def check_last_run(log_file: str, max_hours: int = 4) -> dict:
    """Verifica se bot rodou recentemente."""
    if not os.path.exists(log_file):
        return {"ok": False, "msg": f"Log não encontrado: {log_file}", "last_run": None}
    
    try:
        mtime = os.path.getmtime(log_file)
        last_run = datetime.datetime.fromtimestamp(mtime)
        hours_ago = (datetime.datetime.now() - last_run).total_seconds() / 3600
        
        if hours_ago > max_hours:
            return {
                "ok": False,
                "msg": f"Bot não rodou há {hours_ago:.1f} horas",
                "last_run": last_run,
                "hours_ago": hours_ago
            }
        return {
            "ok": True,
            "msg": f"Bot rodou há {hours_ago:.1f} horas",
            "last_run": last_run,
            "hours_ago": hours_ago
        }
    except Exception as e:
        return {"ok": False, "msg": f"Erro ao ler log: {e}", "last_run": None}

def check_errors(error_file: str) -> dict:
    """Verifica arquivo de erros."""
    if not os.path.exists(error_file):
        return {"ok": True, "count": 0, "msg": "Sem erros registrados"}
    
    try:
        with open(error_file, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        
        count = len(lines)
        recent = lines[-3:] if lines else []
        
        if count > 0:
            return {
                "ok": False,
                "count": count,
                "recent": recent,
                "msg": f"{count} erro(s) registrado(s)"
            }
        return {"ok": True, "count": 0, "msg": "Sem erros"}
    except Exception as e:
        return {"ok": False, "msg": f"Erro ao ler erros: {e}", "count": -1}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Monitor do bot de passagens")
    parser.add_argument("--log-file", default="/var/log/bot-passagens/bot-passagens.log")
    parser.add_argument("--error-file", default="/var/log/bot-passagens/last_error.txt")
    parser.add_argument("--alert-on-error", action="store_true")
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"Monitor Bot Passagens - {datetime.datetime.now().isoformat()}")
    print("=" * 60)
    
    # Verificar última execução
    run_check = check_last_run(args.log_file, max_hours=4)
    status_run = "✓" if run_check["ok"] else "✗"
    print(f"\n{status_run} Última execução: {run_check['msg']}")
    if run_check["last_run"]:
        print(f"   Timestamp: {run_check['last_run']}")
    
    # Verificar erros
    err_check = check_errors(args.error_file)
    status_err = "✓" if err_check["ok"] else "✗"
    print(f"\n{status_err} Erros: {err_check['msg']}")
    if err_check.get("recent"):
        print("   Últimos erros:")
        for line in err_check["recent"]:
            print(f"     - {line}")
    
    # Status geral
    print("\n" + "=" * 60)
    overall_ok = run_check["ok"] and err_check["ok"]
    if overall_ok:
        print("STATUS: ✅ HEALTHY")
        exit_code = 0
    else:
        print("STATUS: ⚠️ ALERT")
        exit_code = 1
    print("=" * 60)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
