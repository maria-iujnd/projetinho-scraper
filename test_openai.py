#!/usr/bin/env python3
"""Script de teste para chamar a API de chat da OpenAI usando uma API key

Uso:
  - Defina a variável de ambiente `OPENAI_API_KEY` no PowerShell ou no sistema.
  - Execute: `python test_openai.py`

O script NÃO deve conter a chave em texto claro.
"""
import os
import sys
import requests


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Variável OPENAI_API_KEY não definida. Defina-a e tente novamente.")
        return 2

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Diga 'Olá' resumidamente."}],
        "max_tokens": 64,
    }

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=15)
    except Exception as e:
        print("Erro ao conectar na API:", e)
        return 3

    if resp.status_code != 200:
        print(f"Resposta de erro ({resp.status_code}):", resp.text)
        return 4

    j = resp.json()
    # Tenta extrair o texto de resposta de forma simples
    try:
        content = j["choices"][0]["message"]["content"]
    except Exception:
        print("Resposta inesperada:", j)
        return 5

    print("Resposta do modelo:")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
