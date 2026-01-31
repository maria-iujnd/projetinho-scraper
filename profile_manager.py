#!/usr/bin/env python3
"""
Profile Manager: Gerencia locks e recuperação de profiles do Chrome.
Garante acesso exclusivo e recuperação em falhas.
"""
import os
import sys
import time
import shutil
import datetime
from date_utils import format_date_for_user  # Regra: toda data exibida ao usuário DEVE passar por esta função

# ATENÇÃO: NUNCA monte datas manualmente para o usuário!
# Sempre use format_date_for_user(dt) para exibir datas em mensagens, logs ou relatórios para o usuário final.
from pathlib import Path
from typing import Optional, Tuple

def get_profile_path(scope: str, service: str) -> Path:
    """
    Retorna caminho do profile baseado em scope e serviço.
    
    scope: "default", "prod", "test", "GRU", "GIG", etc
    service: "kiwi" ou "whatsapp"
    
    Exemplo: chrome_profile_kiwi_prod, chrome_profile_whatsapp_GRU
    """
    base_dir = Path(__file__).parent
    
    if scope == "default":
        profile_name = f"chrome_profile_{service}"
    else:
        profile_name = f"chrome_profile_{service}_{scope}"
    
    return base_dir / profile_name

def get_lock_file(profile_path: Path) -> Path:
    """Retorna caminho do arquivo de lock do profile."""
    return profile_path.parent / f"{profile_path.name}.lock"

def acquire_profile_lock(scope: str, service: str, timeout_secs: int = 10) -> Tuple[bool, Optional[Path]]:
    """
    Tenta adquirir lock exclusivo para um profile.
    
    Retorna: (sucesso: bool, profile_path: Path)
    
    Se falhar após timeout, registra erro e retorna False.
    """
    profile_path = get_profile_path(scope, service)
    lock_file = get_lock_file(profile_path)
    
    # Tentar adquirir lock
    elapsed = 0
    while elapsed < timeout_secs:
        try:
            # Criar arquivo de lock atomicamente (fails se já existe)
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(fd, f"{os.getpid()}\n{datetime.datetime.now().isoformat()}\n".encode())
            os.close(fd)
            
            return True, profile_path
        except FileExistsError:
            # Lock já existe, aguardar
            elapsed += 0.5
            time.sleep(0.5)
    
    # Timeout: registrar e abortar
    try:
        with open(lock_file, 'r') as f:
            lock_content = f.read().strip()
    except:
        lock_content = "(ilegível)"
    
    print(f"[ERRO] Profile '{profile_path.name}' está em uso (lock timeout):")
    print(f"       {lock_content}")
    print(f"       Se travar, remova: {lock_file}")
    
    return False, None

def release_profile_lock(profile_path: Path) -> None:
    """Libera lock do profile."""
    lock_file = get_lock_file(profile_path)
    try:
        if lock_file.exists():
            lock_file.unlink()
    except Exception as e:
        print(f"[WARN] Erro ao liberar lock: {e}")

def backup_corrupted_profile(profile_path: Path) -> Path:
    """
    Se profile está corrompido, faz backup com timestamp.
    Retorna caminho do backup.
    
    Exemplo: chrome_profile_whatsapp → chrome_profile_whatsapp_bak_20260129_143000
    """
    if not profile_path.exists():
        return profile_path
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = profile_path.parent / f"{profile_path.name}_bak_{timestamp}"
    
    try:
        shutil.move(str(profile_path), str(backup_path))
        print(f"[INFO] Profile corrompido movido para: {backup_path.name}")
        return backup_path
    except Exception as e:
        print(f"[ERRO] Erro ao fazer backup: {e}")
        return profile_path

def ensure_profile_exists(profile_path: Path) -> bool:
    """Cria profile vazio se não existir."""
    if profile_path.exists():
        return True
    
    try:
        profile_path.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Profile criado: {profile_path.name}")
        return True
    except Exception as e:
        print(f"[ERRO] Erro ao criar profile: {e}")
        return False

def get_chrome_args(profile_path: Path, scope: str = "default") -> list:
    """
    Retorna argumentos estáveis para Chrome (sem detecção/bloqueio).
    
    Args incluem:
    - Caminho do profile
    - Desabilita shared memory (Linux)
    - Idioma pt-BR
    - Delay entre requests
    """
    args = [
        "disable-dev-shm-usage",          # Linux: usa /tmp em vez de /dev/shm
        "disable-gpu",                     # Desabilita GPU (mais estável)
        "no-first-run",                    # Não mostra wizard
        "no-default-browser-check",        # Não checa default browser
        "disable-sync",                    # Desabilita Google Sync
        "disable-background-networking",   # Menos tráfego em background
        "disable-breakpad",                # Não envia crash reports
        "disable-client-side-phishing-detection",
        "disable-plugins-power-saver",
        "disable-extensions",              # Sem extensões (mais rápido)
        "no-service-autorun",
        "metrics-recording-only",
        "mute-audio",                      # Mudo (mais estável)
        "lang=pt-BR",                      # Português Brasil
    ]
    
    # Se scope é produção, adicionar argumentos de não-detecção
    if scope in ("prod", "production"):
        args.extend([
            "disable-automation",           # Remove webdriver flag
            "disable-blink-features=AutomationControlled",  # Esconde Selenium
        ])
    
    return args

# ========== EXEMPLO DE USO ==========

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Profile Manager - teste")
    parser.add_argument("--scope", default="default")
    parser.add_argument("--service", choices=["kiwi", "whatsapp"], required=True)
    parser.add_argument("--test-lock", action="store_true", help="Testar lock/unlock")
    args = parser.parse_args()
    
    # Testar
    success, profile_path = acquire_profile_lock(args.scope, args.service, timeout_secs=5)
    
    if success:
        print(f"✓ Lock adquirido para {profile_path.name}")
        print(f"  Chrome args: {get_chrome_args(profile_path, args.scope)[:3]}...")
        
        if args.test_lock:
            print(f"  (mantendo lock por 3s para teste)")
            time.sleep(3)
        
        release_profile_lock(profile_path)
        print(f"✓ Lock liberado")
    else:
        print(f"✗ Falha ao adquirir lock")
        sys.exit(1)
