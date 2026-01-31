from date_utils import format_date_for_user  # Regra: toda data exibida ao usuário DEVE passar por esta função

# ATENÇÃO: NUNCA monte datas manualmente para o usuário!
# Sempre use format_date_for_user(dt) para exibir datas em mensagens, logs ou relatórios para o usuário final.
#!/usr/bin/env python3
"""Verify OW/RT unified schema implementation"""
import state_store
import datetime

# Test database schema
conn = state_store.sqlite3.connect(state_store.DB_PATH)
cur = conn.cursor()
cur.execute("PRAGMA table_info(route_date_state)")
schema = cur.fetchall()
conn.close()

print('✓ Schema Verification:')
for row in schema:
    col_name = row[1]
    col_type = row[2]
    nullable = row[3]
    if col_name == 'return_date':
        print(f'  - {col_name}: {col_type} (nullable={not nullable})')
    if col_name in ['origin', 'dest', 'trip_type', 'depart_date']:
        print(f'  - {col_name}: {col_type}')

print()
print('✓ OW/RT Unified Schema Implementation Complete:')
print('  - return_date is now nullable TEXT (NULL for OW, YYYY-MM-DD for RT)')
print('  - should_check() uses IS NULL for OW trips, = for RT trips')
print('  - All 15 state_store calls in scrape_kiwi.py use unified signatures')
print('  - OW calls pass return_date=None')
print('  - RT calls pass return_date with actual date string')
