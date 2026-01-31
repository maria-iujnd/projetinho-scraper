import os
import ast
import sys
import traceback
from pathlib import Path
from typing import List, Dict, Any

AUDIT_FILES = [
    'scrape_kiwi.py',
    'whatsapp_sender.py',
    'routes_config.py',
    'state_store.py',
    'db.py',
    'run_all.py',
]

REPORT_FILE = 'RELATORIO_AUDITORIA.md'

SEVERITY = {
    'CRITICAL': 1,
    'HIGH': 2,
    'MEDIUM': 3,
    'LOW': 4,
}

def find_files():
    """Return list of audit files that exist in the current directory."""
    return [f for f in AUDIT_FILES if Path(f).exists()]

def check_syntax(file: str) -> List[Dict[str, Any]]:
    """Check for syntax errors in a Python file."""
    problems = []
    try:
        with open(file, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source, filename=file)
    except SyntaxError as e:
        problems.append({
            'id': None,
            'severity': 'CRITICAL',
            'file': file,
            'function': '-',
            'desc': f'Syntax error: {e}',
            'how': f'Rodar: python {file}',
            'impact': 'Arquivo não executa, impede funcionamento do bot.',
            'fix': 'Corrigir o erro de sintaxe indicado.',
        })
    return problems

def check_imports(file: str) -> List[Dict[str, Any]]:
    """Check for broken imports in a Python file."""
    problems = []
    try:
        with open(file, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split('.')[0]
                    if not _module_exists(mod):
                        problems.append({
                            'id': None,
                            'severity': 'CRITICAL',
                            'file': file,
                            'function': '-',
                            'desc': f'Import quebrado: {mod}',
                            'how': f'Rodar: python {file}',
                            'impact': 'Quebra execução do bot.',
                            'fix': f'Corrigir ou instalar o módulo {mod}.',
                        })
            elif isinstance(node, ast.ImportFrom):
                mod = node.module
                if mod and not _module_exists(mod.split('.')[0]):
                    problems.append({
                        'id': None,
                        'severity': 'CRITICAL',
                        'file': file,
                        'function': '-',
                        'desc': f'Import quebrado: {mod}',
                        'how': f'Rodar: python {file}',
                        'impact': 'Quebra execução do bot.',
                        'fix': f'Corrigir ou instalar o módulo {mod}.',
                    })
    except Exception:
        pass
    return problems

def _module_exists(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except ImportError:
        return False

def check_undefined_functions_and_vars(file: str) -> List[Dict[str, Any]]:
    """Detecta funções chamadas mas não definidas/importadas e variáveis não definidas."""
    problems = []
    try:
        with open(file, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file)
        defined_funcs = set()
        imported_funcs = set()
        called_funcs = set()
        defined_vars = set()
        used_vars = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined_funcs.add(node.name)
            elif isinstance(node, ast.ImportFrom):
                for n in node.names:
                    imported_funcs.add(n.name)
            elif isinstance(node, ast.Import):
                for n in node.names:
                    imported_funcs.add(n.name)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_funcs.add(node.func.id)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        defined_vars.add(t.id)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
        # Funções chamadas mas não definidas/importadas
        for func in called_funcs:
            if func not in defined_funcs and func not in imported_funcs and not hasattr(__builtins__, func):
                problems.append({
                    'id': None,
                    'severity': 'HIGH',
                    'file': file,
                    'function': '-',
                    'desc': f'Função chamada mas não definida/importada: {func}',
                    'how': f'Rodar: python {file}',
                    'impact': 'Pode causar crash em tempo de execução.',
                    'fix': f'Definir ou importar a função {func}.',
                })
        # Variáveis usadas mas não definidas
        for var in used_vars:
            if var not in defined_vars and var not in imported_funcs and var not in defined_funcs and not hasattr(__builtins__, var):
                problems.append({
                    'id': None,
                    'severity': 'HIGH',
                    'file': file,
                    'function': '-',
                    'desc': f'Variável usada mas não definida/importada: {var}',
                    'how': f'Rodar: python {file}',
                    'impact': 'Pode causar NameError em tempo de execução.',
                    'fix': f'Definir ou importar a variável {var}.',
                })
    except Exception:
        pass
    return problems

def check_affiliate_link_risks(file: str) -> list:
    """Verifica se funções de enqueue/anúncio exigem link e se dedupe/cooldown consideram link."""
    problems = []
    try:
        with open(file, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Funções de enqueue/anúncio devem exigir 'link' como argumento
                if any(kw in node.name for kw in ['enqueue', 'announce', 'mark_announced']):
                    arg_names = [a.arg for a in node.args.args]
                    if 'link' not in arg_names:
                        problems.append({
                            'id': None,
                            'severity': 'HIGH',
                            'file': file,
                            'function': node.name,
                            'desc': f"Função '{node.name}' não exige argumento 'link' (risco de oferta sem rastreio)",
                            'how': f"Revisar assinatura da função {node.name}",
                            'impact': 'Pode permitir envio de oferta sem link afiliado, perdendo rastreio e dedupe correto.',
                            'fix': f"Adicionar argumento obrigatório 'link' em {node.name}.",
                        })
                # Funções de dedupe/cooldown devem usar 'link' no hash
                if any(kw in node.name for kw in ['dedup', 'cooldown', 'is_announced']):
                    src = ast.get_source_segment(source, node)
                    if src and 'link' not in src:
                        problems.append({
                            'id': None,
                            'severity': 'HIGH',
                            'file': file,
                            'function': node.name,
                            'desc': f"Função '{node.name}' não utiliza 'link' no hash/cooldown (risco de dedupe incorreto)",
                            'how': f"Revisar implementação de {node.name}",
                            'impact': 'Pode permitir repetição de oferta com link diferente ou dedupe incorreto.',
                            'fix': f"Garantir que {node.name} sempre inclua 'link' no hash/cooldown.",
                        })
    except Exception:
        pass
    return problems

def main():
    files = find_files()
    all_problems = []
    for file in files:
        all_problems.extend(check_syntax(file))
        all_problems.extend(check_imports(file))
        all_problems.extend(check_undefined_functions_and_vars(file))
        all_problems.extend(check_affiliate_link_risks(file))
    # TODO: Adicionar mais checagens: funções inexistentes, inconsistências, duplicações, riscos, etc.
    # TODO: Priorização e geração do relatório
    write_report(all_problems)
    print(f"Relatório gerado em {REPORT_FILE}")

def write_report(problems: List[Dict[str, Any]]):
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# RELATÓRIO DE AUDITORIA DO BOT\n\n")
        f.write("## Resumo Executivo\n\n")
        f.write(f"Foram encontrados {len(problems)} problemas até o momento.\n\n")
        f.write("## Lista Priorizada de Problemas\n\n")
        for idx, p in enumerate(sorted(problems, key=lambda x: SEVERITY.get(x['severity'], 99))):
            pid = f"P{idx+1:02d}"
            f.write(f"### {pid} - {p['severity']}\n")
            f.write(f"**Arquivo:** {p['file']}\n\n")
            f.write(f"**Função:** {p['function']}\n\n")
            f.write(f"**Descrição:** {p['desc']}\n\n")
            f.write(f"**Como reproduzir:** {p['how']}\n\n")
            f.write(f"**Consequência real:** {p['impact']}\n\n")
            f.write(f"**Correção recomendada:** {p['fix']}\n\n")
            f.write("---\n\n")

if __name__ == "__main__":
    main()
