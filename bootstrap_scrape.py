#!/usr/bin/env python3
import os
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import routes_config as cfg
import state_store
from scrape_kiwi import (
    build_results_url_oneway,
    build_results_url_roundtrip,
    scrape_with_selenium,
    parse_brl_to_int,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KIWI_PROFILE_DIR = os.path.join(BASE_DIR, "chrome_profile_kiwi")

# ====== AJUSTES DO "BRUTO" ======
OW_MAX_RESULTS = 6
RT_MAX_RESULTS = 6
OW_DAYS_TO_SCRAPE = 10
RT_HORIZON_DAYS = 21
RT_NIGHTS = [2, 3, 4, 6, 7]

def next_monday(d: datetime.date) -> datetime.date:
    return d + datetime.timedelta(days=(7 - d.weekday()) % 7)

def date_range(start: datetime.date, days: int):
    for i in range(days):
        yield start + datetime.timedelta(days=i)

def setup_driver(headless: bool = False) -> tuple[webdriver.Chrome, WebDriverWait]:
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
        # Linha user-data-dir removida para scraping sem profile
    options.add_argument("--lang=pt-BR")
    options.add_argument("--disable-notifications")
    if headless:
        options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    return driver, wait

def bootstrap_week_ow(driver, wait, origin: str, dests: list[str], start: datetime.date, days: int = OW_DAYS_TO_SCRAPE):
    print(f"[BOOT-OW] Populando OW de {start.isoformat()} por {days} dias | {len(dests)} destinos")
    checked = 0
    for dest in dests:
        if dest == origin:
            continue
        if dest not in cfg.IATA_TO_SLUG:
            print(f"[BOOT-OW][WARN] Sem slug para {dest}. Pulando.")
            continue
        ceiling = cfg.PRICE_CEILINGS_OW.get(dest, cfg.DEFAULT_PRICE_CEILING_OW)
        for depart_date in date_range(start, days):
            url = build_results_url_oneway(origin, dest, depart_date)
            report_filename = os.path.join(BASE_DIR, f"boot_relatorio_OW_{origin}_{dest}_{depart_date.isoformat()}.txt")
            flights, min_price, status = scrape_with_selenium(
                driver=driver,
                wait=wait,
                url=url,
                report_filename=report_filename,
                price_ceiling=ceiling,
                max_results=OW_MAX_RESULTS
            )
            depart_str = depart_date.isoformat()
            if status == "GOOD":
                state_store.mark_good(origin, dest, "OW", depart_str, None, price=min_price, cooldown_days=1)
            elif status == "BAD":
                state_store.mark_bad(origin, dest, "OW", depart_str, None, price=min_price if min_price > 0 else None, cooldown_hours=6)
            else:
                state_store.mark_no_data(origin, dest, "OW", depart_str, None, cooldown_hours=12)
            checked += 1
            print(f"[BOOT-OW] {origin}->{dest} {depart_str}: {status} min={min_price}")
    return checked

def bootstrap_baseline_rt(driver, wait, origin: str, dests: list[str], start: datetime.date, horizon_days: int = RT_HORIZON_DAYS):
    print(f"[BOOT-RT] Baseline RT de {start.isoformat()} por {horizon_days} dias | {len(dests)} destinos")
    checked = 0
    dep_candidates = list(date_range(start, horizon_days))
    for dest in dests:
        if dest == origin:
            continue
        if dest not in cfg.IATA_TO_SLUG:
            print(f"[BOOT-RT][WARN] Sem slug para {dest}. Pulando.")
            continue
        ceiling = cfg.PRICE_CEILINGS_RT.get(dest, cfg.DEFAULT_PRICE_CEILING_RT)
        for dep in dep_candidates:
            for n in RT_NIGHTS:
                ret = dep + datetime.timedelta(days=n)
                depart_str = dep.isoformat()
                return_str = ret.isoformat()
                url = build_results_url_roundtrip(origin, dest, dep, ret)
                report_filename = os.path.join(BASE_DIR, f"boot_relatorio_RT_{origin}_{dest}_{depart_str}_{return_str}.txt")
                flights, min_price, status = scrape_with_selenium(
                    driver=driver,
                    wait=wait,
                    url=url,
                    report_filename=report_filename,
                    price_ceiling=ceiling,
                    max_results=RT_MAX_RESULTS
                )
                if min_price and min_price > 0:
                    state_store.rt_add_history(origin, dest, depart_str, return_str, min_price)
                if status == "GOOD":
                    state_store.mark_good_rt(origin, dest, depart_str, return_str, min_price, cooldown_days=1)
                elif status == "BAD":
                    state_store.mark_bad_rt(origin, dest, depart_str, return_str, min_price if min_price > 0 else None, cooldown_hours=6)
                else:
                    state_store.mark_no_data_rt(origin, dest, depart_str, return_str, cooldown_hours=12)
                checked += 1
                print(f"[BOOT-RT] {origin}->{dest} {depart_str}<->{return_str}: {status} min={min_price}")
    return checked

def main():
    origin = cfg.ORIGIN_IATA
    daily = []
    for key in cfg.DAILY_DEST_IATA:
        daily.extend(cfg.DESTINATION_GROUPS.get(key, [key]))
    weekly = []
    for key in cfg.WEEKLY_BR_DEST_IATA:
        weekly.extend(cfg.DESTINATION_GROUPS.get(key, [key]))
    today = datetime.date.today()
    start = next_monday(today)
    print(f"[BOOT] Hoje: {today.isoformat()} | Semana começando em: {start.isoformat()}")
    state_store.setup_database()
    driver, wait = setup_driver(headless=False)
    try:
        driver.get("https://www.kiwi.com/br/")
        checked_ow = bootstrap_week_ow(driver, wait, origin, daily, start, days=OW_DAYS_TO_SCRAPE)
        checked_rt = bootstrap_baseline_rt(driver, wait, origin, daily, start, horizon_days=14)
        print(f"[BOOT] Concluído. OW checks={checked_ow} | RT checks={checked_rt}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
