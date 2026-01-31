import sqlite3
from datetime import datetime

DB_PATH = 'kiwi_state.db'

print('Datas em cooldown (BAD ou NO_DATA):')

try:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT origin, dest, trip_type, depart_date, status, cooldown_until
        FROM route_date_state
        WHERE status IN ('BAD','NO_DATA')
        ORDER BY cooldown_until DESC
        LIMIT 50;
    """)
    rows = cur.fetchall()
    for row in rows:
        origin, dest, trip_type, depart_date, status, cooldown_until = row
        print(f"{origin}->{dest} {trip_type} {depart_date} | {status} | cooldown até: {cooldown_until}")
    if not rows:
        print('Nenhuma data em cooldown.')
except Exception as e:
    print(f'Erro ao consultar o banco: {e}')
finally:
    try:
        conn.close()
    except:
        pass
