
import argparse
from bot.runner import run

def build_parser():
    parser = argparse.ArgumentParser("Bot de passagens")
    subparsers = parser.add_subparsers(dest="subcommand")

    # Subcomandos operacionais
    subparsers.add_parser("help", help="Mostra esta ajuda")
    subparsers.add_parser("status", help="Mostra resumo do último ciclo e status da fila")
    subparsers.add_parser("health", help="Mostra status de healthcheck/heartbeat do serviço")
    subparsers.add_parser("prune", help="Limpa dados antigos do DB/fila")
    subparsers.add_parser("preflight", help="Valida ambiente, smoke e health antes do deploy")
    debug_parser = subparsers.add_parser("debug", help="Coleta bundle de debug")
    debug_parser.add_argument("--since-minutes", type=int, default=60)
    import tempfile
    debug_parser.add_argument("--out", type=str, default=tempfile.gettempdir())
    debug_parser.add_argument("--include-screenshots", action="store_true")

    # Argumentos principais (default)
    parser.add_argument("--mode", choices=["daily", "weekly_br", "weekly_intl"], default="daily")
    parser.add_argument("--trip", choices=["ow", "rt"], default="ow")
    parser.add_argument("--origin", default="REC")
    parser.add_argument("--dest", help="filtrar destino (ex: GRU)")
    parser.add_argument("--depart", help="data de ida (YYYY-MM-DD)")
    parser.add_argument("--return", dest="return_date", help="data de volta (YYYY-MM-DD)")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--scope", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("smoke", nargs='?', default=None, help="Roda o smoke test correto (origem, destino, data, teto)")
    parser.add_argument("smoke_args", nargs='*', help="[origem] [destino] [data] [teto]")
    parser.add_argument("--date", default="2026-02-15")
    parser.add_argument("--ceiling", type=int, default=500)
    return parser


def main():
    import os, json, sys
    parser = build_parser()
    args = parser.parse_args()

    # Subcommands
    if args.subcommand == "help":
        parser.print_help()
        sys.exit(0)
    elif args.subcommand == "debug":
        from bot.debug_collector import collect_debug_bundle
        try:
            zip_path = collect_debug_bundle(
                since_minutes=args.since_minutes,
                out_dir=args.out,
                include_screenshots=args.include_screenshots
            )
            print(f"[DEBUG] bundle created at: {zip_path}")
            sys.exit(0)
        except Exception as e:
            print(f"[DEBUG] erro ao criar bundle: {e}")
            sys.exit(2)
    elif args.subcommand == "preflight":
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
        if not os.path.exists(env_path):
            print(f"[PREFLIGHT] ERRO: .env não encontrado em {env_path}")
            sys.exit(1)
        try:
            from bot.smoke_test import run_smoke_test
            report = run_smoke_test()
            if not report.get('ok'):
                print(f"[PREFLIGHT] SMOKE FAIL: {report}")
                sys.exit(1)
        except Exception as e:
            print(f"[PREFLIGHT] ERRO no smoke_test: {e}")
            sys.exit(1)
        try:
            heartbeat_path = os.path.join(os.path.dirname(__file__), "heartbeat.json")
            if not os.path.exists(heartbeat_path):
                print("[PREFLIGHT] ERRO: heartbeat.json não encontrado")
                sys.exit(1)
            with open(heartbeat_path, "r", encoding="utf-8") as f:
                hb = json.load(f)
            if hb.get('status', '').lower() not in ("ok", "healthy", "running", "alive"):
                print(f"[PREFLIGHT] Healthcheck status ruim: {hb}")
                sys.exit(1)
        except Exception as e:
            print(f"[PREFLIGHT] ERRO no healthcheck: {e}")
            sys.exit(1)
        print("[PREFLIGHT] OK: ambiente, smoke e healthcheck válidos.")
        sys.exit(0)
    elif args.subcommand == "status":
        from bot.runtime_state import load_runtime_state
        state = load_runtime_state()
        if state:
            print("\nResumo do último ciclo:")
            print(f"  Duração: {state.get('duration', '?'):.1f}s" if 'duration' in state else "  Duração: ?")
            print("  Contadores por fase/motivo:")
            for k, v in state.get("counts", {}).items():
                print(f"    {k} = {v}")
            print("  Status da fila:")
            for k, v in state.get("queue", {}).items():
                print(f"    {k}: {v}")
        else:
            print("Nenhum resumo encontrado. Execute o bot pelo menos uma vez.")
        sys.exit(0)
    elif args.subcommand == "health":
        from bot.notify import notify_admin
        from bot.runtime_state import should_send_alert
        import time
        heartbeat_path = os.path.join(os.path.dirname(__file__), "heartbeat.json")
        max_age = 600  # 10 min
        alert_needed = False
        age_seconds = None
        last_error = None
        queue_size = None
        if os.path.exists(heartbeat_path):
            with open(heartbeat_path, "r", encoding="utf-8") as f:
                hb = json.load(f)
            ts = hb.get('timestamp', hb.get('heartbeat_ts'))
            status = hb.get('status', '').upper()
            last_error = hb.get('last_error')
            queue_size = hb.get('queue_size')
            try:
                t_struct = time.strptime(ts, "%Y-%m-%dT%H:%M:%S")
                age_seconds = int(time.time() - time.mktime(t_struct))
            except Exception:
                age_seconds = None
            if age_seconds is not None and age_seconds > max_age:
                alert_needed = True
            if status not in ("OK", "HEALTHY", "RUNNING", "ALIVE"):
                alert_needed = True
            if alert_needed and should_send_alert("healthcheck_fail", 1800):
                body = f"heartbeat_age={age_seconds}s (limit={max_age}s)\nlast_cycle_status={status}\nlast_error={last_error}\nqueue_size={queue_size}\nlog=/var/log/kiwi_bot.log"
                notify_admin("HEALTHCHECK_FAIL", body, alert_type="HEALTHCHECK_FAIL")
            print("\nHealthcheck/Heartbeat:")
            print(f"  Último heartbeat: {ts}")
            print(f"  Status: {status}")
            print(f"  Info: {hb.get('info', '')}")
            if alert_needed:
                sys.exit(1)
        else:
            if should_send_alert("healthcheck_fail", 1800):
                notify_admin("HEALTHCHECK_FAIL", "heartbeat.json não encontrado\nlog=/var/log/kiwi_bot.log", alert_type="HEALTHCHECK_FAIL")
            print("Nenhum heartbeat encontrado. O serviço pode não estar rodando.")
            sys.exit(1)
    elif args.subcommand == "prune":
        from state_store import prune_seen, prune_history
        from bot.queue_store import prune_queue_sent
        n_seen = prune_seen(older_than_seconds=30*86400)
        n_hist = prune_history(older_than_days=90)
        n_queue = prune_queue_sent(older_than_days=7)
        print(f"Prune concluído: seen={n_seen}, history={n_hist}, queue_sent={n_queue}")
        sys.exit(0)

    # Normalização de datas
    from bot.date_utils import to_iso_date
    if hasattr(args, "date") and args.date:
        try:
            args.date = to_iso_date(args.date)
        except Exception as e:
            print(f"[ERRO] Data inválida (--date): {e}"); exit(1)
    if hasattr(args, "depart") and args.depart:
        try:
            args.depart = to_iso_date(args.depart)
        except Exception as e:
            print(f"[ERRO] Data inválida (--depart): {e}"); exit(1)
    if hasattr(args, "return_date") and args.return_date:
        try:
            args.return_date = to_iso_date(args.return_date)
        except Exception as e:
            print(f"[ERRO] Data inválida (--return): {e}"); exit(1)

    # Smoke test
    if args.smoke is not None:
        origin = args.origin
        dest = args.dest
        date = args.date
        ceiling = args.ceiling
        if args.smoke_args and len(args.smoke_args) >= 1:
            origin = args.smoke_args[0]
        if args.smoke_args and len(args.smoke_args) >= 2:
            dest = args.smoke_args[1]
        if args.smoke_args and len(args.smoke_args) >= 3:
            date = args.smoke_args[2]
        if args.smoke_args and len(args.smoke_args) >= 4:
            try:
                ceiling = int(args.smoke_args[3])
            except Exception:
                pass
        from bot.smoke_test import run_smoke_test
        report = run_smoke_test(
            origin=origin,
            dest=dest,
            date=date,
            ceiling=ceiling
        )
        print("\n[SMOKE TEST RESULT]")
        print(f"ok:     {report['ok']}")
        print(f"stage:  {report['stage']}")
        print(f"reason: {report['reason']}")
        print("details:")
        for k, v in report['details'].items():
            print(f"  {k}: {v}")
        sys.exit(0 if report['ok'] else 1)

    # Caminho padrão: executa run(args)
    raise SystemExit(run(args))

if __name__ == "__main__":
    main()
