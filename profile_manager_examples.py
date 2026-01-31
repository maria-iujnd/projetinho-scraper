#!/usr/bin/env python3
"""
Guia Rápido - Profile Manager Integration
Exemplos de uso para scrape_kiwi.py e whatsapp_sender.py
"""

# ============================================================
# EXEMPLO 1: Em scrape_kiwi.py (main function)
# ============================================================

def main_with_profile_manager():
    """Padrão de uso em scrape_kiwi.py"""
    import profile_manager
    import sys
    
    # Parse args
    scope = args.scope or "default"
    
    # 1. ADQUIRIR LOCK
    lock_acquired, profile_path = profile_manager.acquire_profile_lock(
        scope=scope, 
        service="kiwi", 
        timeout_secs=10
    )
    if not lock_acquired:
        log("ERROR", f"Falha ao adquirir lock Kiwi (escopo={scope})")
        sys.exit(1)
    
    # 2. GARANTIR PROFILE EXISTS
    profile_manager.ensure_profile_exists(profile_path)
    
    # 3. CRIAR CHROME OPTIONS
    options = webdriver.ChromeOptions()
    for arg in profile_manager.get_chrome_args(profile_path, scope):
        options.add_argument(arg)
    
    # Argumentos específicos
    options.add_argument("--start-maximized")
    if args.headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-notifications")
    
    # 4. INICIAR DRIVER COM TRATAMENTO DE ERRO
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=options
        )
        log("INFO", f"Chrome iniciado (profile={profile_path.name})")
    except Exception as e:
        log("ERROR", f"Falha ao iniciar Chrome: {e}")
        # Profile pode estar corrompido, fazer backup
        profile_manager.backup_corrupted_profile(profile_path)
        profile_manager.release_profile_lock(profile_path)
        sys.exit(1)
    
    # Armazenar para cleanup
    kiwi_profile_path = profile_path
    
    try:
        # ... main logic aqui ...
        pass
    finally:
        driver.quit()
        # LIBERAR LOCK
        profile_manager.release_profile_lock(kiwi_profile_path)
        log("INFO", f"Lock liberado ({profile_path.name})")


# ============================================================
# EXEMPLO 2: Em whatsapp_sender.py (open_whatsapp function)
# ============================================================

def open_whatsapp_with_lock(headless: bool = False, scope: str = "default"):
    """Padrão de uso em whatsapp_sender.py"""
    import profile_manager
    
    # 1. ADQUIRIR LOCK
    lock_acquired, profile_path = profile_manager.acquire_profile_lock(
        scope=scope, 
        service="whatsapp", 
        timeout_secs=15
    )
    if not lock_acquired:
        log("ERROR", f"Falha ao adquirir lock WhatsApp (escopo={scope})")
        return None
    
    # 2. GARANTIR PROFILE EXISTS
    profile_manager.ensure_profile_exists(profile_path)
    
    # 3. CRIAR CHROME OPTIONS
    options = webdriver.ChromeOptions()
    for arg in profile_manager.get_chrome_args(profile_path, scope):
        options.add_argument(arg)
    
    # Argumentos específicos
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-notifications")
    
    # 4. INICIAR DRIVER
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=options
        )
        # Armazenar profile path para cleanup depois
        driver._whatsapp_profile_path = profile_path
        log("INFO", f"WhatsApp Chrome iniciado (profile={profile_path.name})")
        return driver
    except Exception as e:
        log("ERROR", f"Falha ao iniciar WhatsApp Chrome: {e}")
        profile_manager.backup_corrupted_profile(profile_path)
        profile_manager.release_profile_lock(profile_path)
        return None


def main_whatsapp_with_lock():
    """Padrão de uso em whatsapp_sender.py main()"""
    import profile_manager
    
    scope = args.scope or "default"
    
    # Abrir com lock
    driver = open_whatsapp_with_lock(headless=args.headless, scope=scope)
    if driver is None:
        log("ERROR", f"Falha ao abrir WhatsApp (escopo={scope})")
        sys.exit(1)
    
    try:
        # ... main logic aqui ...
        pass
    finally:
        driver.quit()
        # LIBERAR LOCK
        if hasattr(driver, '_whatsapp_profile_path'):
            profile_manager.release_profile_lock(driver._whatsapp_profile_path)
            log("INFO", f"Lock liberado ({driver._whatsapp_profile_path.name})")


# ============================================================
# EXEMPLO 3: Testando Locks (concorrência)
# ============================================================

def test_concurrent_locks():
    """Testar behavior com múltiplas tentativas de lock"""
    import profile_manager
    import threading
    import time
    
    def try_lock(thread_id):
        success, path = profile_manager.acquire_profile_lock(
            scope="test", 
            service="kiwi", 
            timeout_secs=5
        )
        if success:
            print(f"Thread {thread_id}: ✓ Lock adquirido")
            time.sleep(2)  # Simular trabalho
            profile_manager.release_profile_lock(path)
            print(f"Thread {thread_id}: ✓ Lock liberado")
        else:
            print(f"Thread {thread_id}: ✗ Lock falhou (timeout esperado)")
    
    # Iniciar 3 threads simultâneas
    threads = [
        threading.Thread(target=try_lock, args=(i,))
        for i in range(3)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Resultado esperado:
    # Thread 0: ✓ Lock adquirido
    # Thread 1: ✗ Lock falhou (timeout esperado)
    # Thread 2: ✗ Lock falhou (timeout esperado)
    # Thread 0: ✓ Lock liberado


# ============================================================
# EXEMPLO 4: Debugging - Ver Profile Status
# ============================================================

def show_profile_status():
    """Mostrar status de todos os profiles"""
    from pathlib import Path
    
    script_dir = Path(__file__).parent
    
    print("\n=== Profile Status ===\n")
    
    # Listar profiles
    for profile_dir in sorted(script_dir.glob("chrome_profile_*")):
        if profile_dir.is_dir():
            lock_file = Path(str(profile_dir) + ".lock")
            
            status = "🔒 LOCKED" if lock_file.exists() else "✓ FREE"
            
            if lock_file.exists():
                try:
                    with open(lock_file) as f:
                        content = f.read().strip()
                    pid, ts = content.split('\n')
                    print(f"{profile_dir.name:<40} {status}  (PID={pid}, time={ts})")
                except:
                    print(f"{profile_dir.name:<40} {status}  (lock ilegível)")
            else:
                print(f"{profile_dir.name:<40} {status}")
    
    # Listar backups
    backups = list(script_dir.glob("chrome_profile_*_bak_*"))
    if backups:
        print(f"\n=== Backups ({len(backups)}) ===\n")
        for backup in sorted(backups):
            print(f"  {backup.name}")


# ============================================================
# EXEMPLO 5: Limpeza Segura
# ============================================================

def cleanup_old_backups(days=7):
    """Remover backups antigos (> N dias)"""
    from pathlib import Path
    import os
    import time
    
    script_dir = Path(__file__).parent
    now = time.time()
    max_age = days * 86400
    
    for backup in script_dir.glob("chrome_profile_*_bak_*"):
        age = now - os.path.getmtime(backup)
        if age > max_age:
            try:
                import shutil
                shutil.rmtree(backup)
                print(f"✓ Removido: {backup.name}")
            except Exception as e:
                print(f"✗ Erro ao remover {backup.name}: {e}")


# ============================================================
# Executar Exemplos
# ============================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "test-concurrent":
            print("Testando locks concorrentes...")
            test_concurrent_locks()
        
        elif cmd == "status":
            show_profile_status()
        
        elif cmd == "cleanup-backups":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            print(f"Limpando backups com > {days} dias...")
            cleanup_old_backups(days)
        
        else:
            print("Uso:")
            print("  python profile_manager_examples.py test-concurrent")
            print("  python profile_manager_examples.py status")
            print("  python profile_manager_examples.py cleanup-backups [days]")
    else:
        print("Ver exemplos de código acima")
