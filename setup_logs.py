from date_utils import format_date_for_user  # Regra: toda data exibida ao usuário DEVE passar por esta função

# ATENÇÃO: NUNCA monte datas manualmente para o usuário!
# Sempre use format_date_for_user(dt) para exibir datas em mensagens, logs ou relatórios para o usuário final.
#!/usr/bin/env python3
"""
Setup estrutura de logs do bot com rotação automática.
Executa uma vez durante instalação.

Uso: python setup_logs.py
"""
import os
import sys
from pathlib import Path

def setup_logs(log_dir: str = "/var/log/bot-passagens"):
    """Cria estrutura de logs."""
    try:
        # Criar diretório
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Arquivos de log
        log_files = [
            "bot-passagens.log",      # Log principal
            "last_error.txt",          # Último(s) erro(s)
            "scraper.log",             # Específico do scraper
            "sender.log",              # Específico do sender
        ]
        
        for fname in log_files:
            fpath = Path(log_dir) / fname
            fpath.touch(exist_ok=True)
            print(f"✓ {fpath}")
        
        print(f"\n✅ Logs setup em: {log_dir}")
        return True
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Setup de logs")
    parser.add_argument("--log-dir", default="/var/log/bot-passagens")
    args = parser.parse_args()
    
    success = setup_logs(args.log_dir)
    sys.exit(0 if success else 1)
