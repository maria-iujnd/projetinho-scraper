#!/usr/bin/env python3
import os
import json
import shutil
import sqlite3
import datetime
from date_utils import format_date_for_user  # Regra: toda data exibida ao usuário DEVE passar por esta função

# ATENÇÃO: NUNCA monte datas manualmente para o usuário!
# Sempre use format_date_for_user(dt) para exibir datas em mensagens, logs ou relatórios para o usuário final.
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "kiwi_state.db"
QUEUE_PATH = BASE_DIR / "queue_messages.json"

# ======= AJUSTES INTELIGENTES (MVP) =======
HOT_LOOKBACK_DAYS = 30          # janela para detectar "rotas quentes"
HOT_KEEP_PAST_DAYS = 120        # quanto manter de passado para rotas quentes
COLD_KEEP_PAST_DAYS = 45        # quanto manter de passado para rotas frias

# Sempre manter viagens futuras por pelo menos X dias à frente (mesmo se rota fria)
KEEP_FUTURE_DAYS = 180

# Backup/rotacao
KEEP_BACKUPS = 4               # manter só os últimos N backups

# Fila WhatsApp: limite para não crescer infinito
QUEUE_MAX_ITEMS = 400
QUEUE_KEEP_LAST = 200


def now_utc_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()


def parse_date_yyyy_mm_dd(s: str):
    # depart_date vem como TEXT; tentamos YYYY-MM-DD
    try:
        return datetime.date.fromisoformat(s[:10])
    except Exception:
        return None


def backup_db():
    if not DB_PATH.exists():
        print("[CLEANUP] DB não existe. Pulando backup.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BASE_DIR / f"kiwi_state_backup_{ts}.db"
    shutil.copy2(DB_PATH, backup)
    print(f"[CLEANUP] Backup criado: {backup.name}")

    # Rotaciona backups (mantém só os últimos KEEP_BACKUPS)
    backups = sorted(BASE_DIR.glob("kiwi_state_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[KEEP_BACKUPS:]:
        try:
            old.unlink()
            print(f"[CLEANUP] Backup antigo removido: {old.name}")
        except Exception:
            pass


def cleanup_queue():
    if not QUEUE_PATH.exists():
        print("[CLEANUP] queue_messages.json não existe. OK.")
        return

    try:
        data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            data = []
    except Exception:
        print("[CLEANUP] queue_messages.json corrompido. Zerando.")
        data = []

    original = len(data)

    # Se fila ficou grande, mantém só o final
    if len(data) > QUEUE_MAX_ITEMS:
        data = data[-QUEUE_KEEP_LAST:]

    QUEUE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[CLEANUP] Fila: {original} -> {len(data)} itens")


def cleanup_db():
    if not DB_PATH.exists():
        print("[CLEANUP] DB não existe. OK.")
        return

    today = datetime.date.today()
    hot_cutoff = today - datetime.timedelta(days=HOT_KEEP_PAST_DAYS)
    cold_cutoff = today - datetime.timedelta(days=COLD_KEEP_PAST_DAYS)
    future_keep_until = today + datetime.timedelta(days=KEEP_FUTURE_DAYS)

    hot_since_dt = (datetime.datetime.now() - datetime.timedelta(days=HOT_LOOKBACK_DAYS)).replace(microsecond=0).isoformat()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ====== 1) Descobre rotas "quentes" ======
    # critério: teve announcement nos últimos 30d OU status=GOOD checado nos últimos 30d
    hot_routes = set()

    # announcements: não tem origin/dest, só offer_hash. Então aqui a gente usa como indicador geral
    # e usa status=GOOD + last_checked_at para rotas realmente quentes por rota.
    try:
        cur.execute("""
            SELECT DISTINCT origin, dest
            FROM route_date_state
            WHERE status = 'GOOD' AND last_checked_at >= ?
        """, (hot_since_dt,))
        for o, d in cur.fetchall():
            hot_routes.add((o, d))
    except Exception as e:
        print(f"[CLEANUP] Falha ao detectar rotas quentes: {e}")

    print(f"[CLEANUP] Rotas quentes detectadas: {len(hot_routes)}")

    # ====== 2) Limpar announcements antigos ======
    # announcements serve pra evitar repetição; manter um bom tempo.
    # Aqui vamos manter 180 dias.
    ann_cutoff = (datetime.datetime.now() - datetime.timedelta(days=180)).replace(microsecond=0).isoformat()
    try:
        cur.execute("DELETE FROM announcements WHERE created_at < ?", (ann_cutoff,))
        print(f"[CLEANUP] announcements deletados: {cur.rowcount}")
    except Exception as e:
        print(f"[CLEANUP] Falha limpando announcements: {e}")

    # ====== 3) Limpeza inteligente do route_date_state ======
    # Regras:
    # - NUNCA apagar depart_date no futuro (até KEEP_FUTURE_DAYS à frente)
    # - manter passado maior para rotas quentes, menor para frias
    # - nunca apagar linhas com cooldown_until no futuro (para não quebrar throttling)
    # - manter pelo menos 1 linha mais recente por rota (origin,dest)

    # 3.1) pega "último check" por rota
    last_check_by_route = {}
    cur.execute("""
        SELECT origin, dest, MAX(last_checked_at) AS mx
        FROM route_date_state
        GROUP BY origin, dest
    """)
    for o, d, mx in cur.fetchall():
        last_check_by_route[(o, d)] = mx

    # 3.2) varre todas as linhas e decide deletar via batch
    cur.execute("""
        SELECT origin, dest, depart_date, last_checked_at, cooldown_until
        FROM route_date_state
    """)
    rows = cur.fetchall()

    to_delete = []
    kept = 0

    for o, d, depart_date_s, last_checked_s, cooldown_until_s in rows:
        route = (o, d)

        # mantém 1 linha mais recente por rota
        if last_checked_s and last_check_by_route.get(route) == last_checked_s:
            kept += 1
            continue

        depart_date = parse_date_yyyy_mm_dd(depart_date_s or "")
        if depart_date is None:
            # sem data parseável? mantém para não apagar algo errado
            kept += 1
            continue

        # 1) mantém futuro (até KEEP_FUTURE_DAYS)
        if depart_date >= today and depart_date <= future_keep_until:
            kept += 1
            continue

        # 2) se cooldown_until ainda válido, mantém
        if cooldown_until_s:
            try:
                cooldown_dt = datetime.datetime.fromisoformat(cooldown_until_s)
                if cooldown_dt > datetime.datetime.now():
                    kept += 1
                    continue
            except Exception:
                pass

        # 3) aplica cutoff por “hot vs cold” (só para passado)
        if depart_date < today:
            cutoff = hot_cutoff if route in hot_routes else cold_cutoff
            if depart_date < cutoff:
                to_delete.append((o, d, depart_date_s))
            else:
                kept += 1
        else:
            # futuro muito longe (acima KEEP_FUTURE_DAYS): pode limpar para evitar DB enorme
            # mas só se for rota fria
            if route not in hot_routes:
                to_delete.append((o, d, depart_date_s))
            else:
                kept += 1

    # 3.3) executa delete em batch
    deleted = 0
    if to_delete:
        cur.executemany("""
            DELETE FROM route_date_state
            WHERE origin = ? AND dest = ? AND depart_date = ?
        """, to_delete)
        deleted = cur.rowcount if cur.rowcount is not None else len(to_delete)

    print(f"[CLEANUP] route_date_state: manter ~{kept}, deletar ~{len(to_delete)} (executado={deleted})")

    conn.commit()

    # compacta
    try:
        cur.execute("VACUUM;")
        conn.commit()
        print("[CLEANUP] VACUUM OK.")
    except Exception as e:
        print(f"[CLEANUP] VACUUM falhou: {e}")

    conn.close()


def main():
    print(f"[CLEANUP] Início: {now_utc_iso()}")
    backup_db()
    cleanup_db()
    cleanup_queue()
    print(f"[CLEANUP] Fim: {now_utc_iso()}")


if __name__ == "__main__":
    main()
