import os
import glob
import shutil

# Pastas e arquivos a remover
REMOVE_DIRS = [
    'venv',
    '.venv',
    'bot/__pycache__',
    'chrome_profile',
    'chrome_profile_whatsapp',
]
REMOVE_FILES = [
    'kiwi_state.db',
    'queue_messages.json',
]
REMOVE_PATTERNS = [
    'debug_timeout_*.html',
    'debug_timeout_*.png',
    'boot_relatorio_*.txt',
    'RESUMO_*.txt',
    'FINAL_SUMMARY_*.txt',
]

def remove_path(path):
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
        print(f"Removido diretório: {path}")
    elif os.path.isfile(path):
        os.remove(path)
        print(f"Removido arquivo: {path}")

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    # Remove dirs
    for d in REMOVE_DIRS:
        abs_path = os.path.join(base, d)
        if os.path.exists(abs_path):
            remove_path(abs_path)
    # Remove arquivos
    for f in REMOVE_FILES:
        abs_path = os.path.join(base, f)
        if os.path.exists(abs_path):
            remove_path(abs_path)
    # Remove por padrão glob
    for pat in REMOVE_PATTERNS:
        for match in glob.glob(os.path.join(base, pat)):
            remove_path(match)
    print("Limpeza concluída!")

if __name__ == "__main__":
    main()
