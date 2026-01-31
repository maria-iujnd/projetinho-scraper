#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import json
import os
import random
import re
import time
from datetime import datetime as dt

import pytz
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import settings
import state_store

from bot.browser import open_browser, close_browser
from bot.config import (
    SEND_TZ, SEND_WINDOWS,
    MIN_SECONDS_BETWEEN_MESSAGES_PER_GROUP,
)
from bot.send_rate_control import can_send_group, can_send_route


BASE_DIR = settings.BASE_DIR
QUEUE_FILE = settings.queue_file(None)
GROUP_NAME = settings.DEFAULT_GROUP_NAME

SEND_DELAY_MIN_SEC = settings.SEND_DELAY_MIN_SEC
SEND_DELAY_MAX_SEC = settings.SEND_DELAY_MAX_SEC
MAX_TO_SEND = settings.MAX_TO_SEND

# Profile persistente do WhatsApp (para não pedir QR sempre)
WHATSAPP_PROFILE_DIR = settings.whatsapp_profile_dir(None)


def log(level: str, msg: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def sanitize_for_chromedriver(text: str) -> str:
    # remove caracteres fora do BMP (evita problemas em algumas combinações)
    return re.sub(r"[\U00010000-\U0010FFFF]", "", text)


def load_queue(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        log("WARN", "queue file missing/corrupt, returning empty queue")
        return []

    if not isinstance(raw, list):
        log("WARN", "queue JSON root is not a list, ignoring")
        return []

    normalized: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        # compat
        if "text" not in item and "message" in item:
            item["text"] = item.get("message")

        mid = item.get("id") or item.get("offer_hash") or ""
        text = item.get("text") or ""
        if not str(mid).strip() or not str(text).strip():
            continue

        normalized_item = {
            "id": str(mid),
            "text": str(text),
            "priority": float(item.get("priority", 0.0) or 0.0),
            "created_at": item.get("created_at") or datetime.datetime.now().isoformat(timespec="seconds"),
            "group": item.get("group") or GROUP_NAME,
        }

        # route opcional (rate-limit por rota)
        if item.get("route"):
            normalized_item["route"] = item.get("route")
        else:
            o = item.get("origin")
            d = item.get("dest")
            if o and d:
                normalized_item["route"] = f"{o}-{d}"

        normalized.append(normalized_item)

    return normalized


def save_queue(queue: list[dict], path: str) -> None:
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def open_whatsapp(driver) -> None:
    driver.get("https://web.whatsapp.com/")
    log("INFO", "Abra o WhatsApp Web. Se pedir QR, escaneie com o celular.")
    wait = WebDriverWait(driver, 300)
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='pane-side']")))
    time.sleep(1.5)
    log("INFO", "WhatsApp Web pronto.")


def open_chat_by_name(driver, chat_name: str) -> bool:
    try:
        wait = WebDriverWait(driver, 30)

        search = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//div[@data-testid='pane-side']//input[@aria-label or @placeholder]"
        )))
        search.click()
        time.sleep(0.2)
        search.send_keys(Keys.CONTROL + "a")
        search.send_keys(Keys.DELETE)
        time.sleep(0.1)
        search.send_keys(chat_name)
        time.sleep(1.2)

        chat = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            f"//div[@data-testid='chat-list-item-container']//span[contains(text(), '{chat_name}')]"
        )))
        chat.click()
        time.sleep(0.6)
        return True
    except Exception as e:
        log("WARN", f"Não foi possível abrir o chat '{chat_name}': {e}")
        return False


def send_message(driver, msg: str) -> bool:
    try:
        wait = WebDriverWait(driver, 30)
        box = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//footer//div[@contenteditable='true'][@data-tab='1']"
        )))
        box.click()
        time.sleep(0.15)

        safe_msg = sanitize_for_chromedriver(msg)
        actions = ActionChains(driver)
        lines = safe_msg.splitlines()

        for i, line in enumerate(lines):
            if line:
                actions.send_keys(line)
            if i < len(lines) - 1:
                actions.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
                time.sleep(0.03)

        actions.perform()
        time.sleep(0.15)

        send_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//footer//button[@aria-label='Enviar' or @aria-label='Send']"
        )))
        send_btn.click()
        time.sleep(0.35)
        return True
    except Exception as e:
        log("ERROR", f"Falha ao enviar mensagem: {e}")
        return False


def is_within_send_window() -> bool:
    tz = pytz.timezone(SEND_TZ)
    now = dt.now(tz)

    # SEND_WINDOWS: "08:00-09:00,11:00-12:00"
    for window in str(SEND_WINDOWS).split(","):
        window = window.strip()
        if not window:
            continue
        start_str, end_str = window.split("-")
        start = dt.strptime(start_str.strip(), "%H:%M").replace(
            year=now.year, month=now.month, day=now.day, tzinfo=tz
        )
        end = dt.strptime(end_str.strip(), "%H:%M").replace(
            year=now.year, month=now.month, day=now.day, tzinfo=tz
        )
        if end <= start:
            end += datetime.timedelta(days=1)
        if start <= now <= end:
            return True
    return False


def can_send_now(group: str, route_key: str | None):
    if not is_within_send_window():
        return False, "OUTSIDE_WINDOW"

    ok, reason = can_send_group(group)
    if not ok:
        return False, reason

    if route_key:
        ok, reason = can_send_route(route_key)
        if not ok:
            return False, reason

    return True, "OK"


def group_items(queue: list[dict]) -> dict[str, list[dict]]:
    by_group: dict[str, list[dict]] = {}
    for it in queue:
        g = it.get("group") or GROUP_NAME
        by_group.setdefault(g, []).append(it)

    # prioridade maior primeiro
    for g in by_group:
        by_group[g].sort(key=lambda x: (-float(x.get("priority", 0.0) or 0.0), x.get("created_at", "")))
    return by_group


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Não envia nada, só imprime")
    parser.add_argument("--group", default=None, help="Sobrescreve o nome do grupo padrão")
    args = parser.parse_args()

    queue_file = QUEUE_FILE
    queue = load_queue(queue_file)
    if not queue:
        log("INFO", "Fila vazia. Nada para enviar.")
        return

    # override opcional de grupo
    if args.group:
        for item in queue:
            item["group"] = args.group

    messages_by_group = group_items(queue)

    driver = None
    wait = None

    if args.dry_run:
        log("INFO", "DRY-RUN ativo: nada será enviado.")
    else:
        # WhatsApp precisa de GUI -> headless=False
        driver, wait = open_browser(
            headless=False,
            kind="whatsapp",
            scope=None,
            wait_timeout=30,
            user_data_dir=WHATSAPP_PROFILE_DIR,
        )
        open_whatsapp(driver)

    total_sent = 0

    try:
        for group, items in messages_by_group.items():
            if total_sent >= MAX_TO_SEND:
                log("INFO", f"Limite global {MAX_TO_SEND} atingido. Encerrando.")
                break

            log("INFO", f"Grupo '{group}' com {len(items)} itens")

            if driver and not args.dry_run:
                if not open_chat_by_name(driver, group):
                    log("WARN", f"Grupo '{group}' não encontrado. Pulando.")
                    continue

            i = 0
            sent_in_group = 0
            while i < len(items):
                if total_sent >= MAX_TO_SEND:
                    break

                item = items[i]
                msg = item.get("text") or ""
                route_key = item.get("route") if isinstance(item.get("route"), str) else None

                allowed, reason = can_send_now(group, route_key)
                if not allowed:
                    log("SEND", f"blocked reason={reason} group={group}")
                    break

                if args.dry_run:
                    print(f"\n[DRY-RUN] Grupo '{group}':\n{msg}\n" + "-" * 40)
                    sent_in_group += 1
                    total_sent += 1
                    i += 1
                    continue

                ok = send_message(driver, msg)
                if not ok:
                    i += 1
                    continue

                offer_hash = item.get("id") or item.get("offer_hash")
                if offer_hash:
                    try:
                        state_store.mark_announced(offer_hash)
                    except Exception as e:
                        log("WARN", f"mark_announced falhou: {e}")

                try:
                    state_store.record_group_send(group)
                except Exception as e:
                    log("WARN", f"record_group_send falhou: {e}")

                # remove da fila
                sent_in_group += 1
                total_sent += 1
                items.pop(i)
                if item in queue:
                    queue.remove(item)
                save_queue(queue, queue_file)

                delay = random.randint(SEND_DELAY_MIN_SEC, SEND_DELAY_MAX_SEC)
                log("INFO", f"Enviado {sent_in_group} no grupo '{group}'. Próxima em {delay}s.")
                time.sleep(delay)

                if MIN_SECONDS_BETWEEN_MESSAGES_PER_GROUP and MIN_SECONDS_BETWEEN_MESSAGES_PER_GROUP > 0:
                    # delay já cobre; mantido por clareza
                    pass

            log("INFO", f"Grupo '{group}' finalizado: {sent_in_group} enviada(s)")

    finally:
        if not args.dry_run:
            save_queue(queue, queue_file)
        if driver:
            close_browser(driver)

    log("INFO", f"Finalizado. Total enviadas: {total_sent}")


if __name__ == "__main__":
    main()