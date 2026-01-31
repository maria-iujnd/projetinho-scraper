import db
from typing import Optional, List, Dict
import sqlite3

def load_policies_from_db() -> List[sqlite3.Row]:
    """
    Carrega todas as políticas de rota ativas do banco de dados.
    """
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM route_policy WHERE is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_ceiling(origin: str, dest: str, trip_type: str = 'one-way') -> Optional[int]:
    """
    Retorna o teto de preço (price_ceiling) para uma rota específica.
    Retorna None se a rota não tiver política definida.
    """
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT price_ceiling FROM route_policy WHERE origin = ? AND dest = ? AND trip_type = ?",
        (origin, dest, trip_type)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row['price_ceiling']
    return None

def seed_default_policies():
    """
    Insere políticas padrão no banco de dados:
    - 8 destinos DAILY (cooldown de 1 dia) com tetos específicos.
    - Destinos WEEKLY (cooldown de 7 dias) com tetos genéricos.
    """
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    # Assumindo REC como origem padrão baseado no contexto do projeto
    origin = 'REC'
    trip_type = 'one-way'

    # Destinos DAILY (IATA)
    daily_targets = [
        ('GRU', 450), ('GIG', 500), ('BSB', 500), ('SSA', 400),
        ('FOR', 420), ('CNF', 500), ('VCP', 450), ('NAT', 420)
    ]

    print("Inserindo políticas DAILY...")
    for dest, ceiling in daily_targets:
        cursor.execute("""
        INSERT OR REPLACE INTO route_policy 
        (origin, dest, trip_type, is_active, price_ceiling, cooldown_good_days, cooldown_bad_hours, cooldown_nodata_hours)
        VALUES (?, ?, ?, 1, ?, 1, 6, 12)
        """, (origin, dest, trip_type, ceiling))

    # Destinos WEEKLY (Exemplos genéricos)
    weekly_targets = [
        ('FLN', 800), ('CWB', 800), ('POA', 900), ('MAO', 1000)
    ]

    print("Inserindo políticas WEEKLY...")
    for dest, ceiling in weekly_targets:
        cursor.execute("""
        INSERT OR REPLACE INTO route_policy 
        (origin, dest, trip_type, is_active, price_ceiling, cooldown_good_days, cooldown_bad_hours, cooldown_nodata_hours)
        VALUES (?, ?, ?, 1, ?, 7, 24, 24)
        """, (origin, dest, trip_type, ceiling))

    conn.commit()
    conn.close()
    print("Políticas padrão inseridas com sucesso.")

if __name__ == "__main__":
    # Permite rodar este arquivo diretamente para popular o banco
    seed_default_policies()