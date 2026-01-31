import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import json
import os
import sys

from bot.browser import open_browser, close_browser
from bot.viajala_scraper import scrape_with_selenium


def main() -> None:
    driver = None
    try:
        print("PYTHON:", sys.executable)
        print("CWD:", os.getcwd())
        driver, _ = open_browser(headless=False)
        print("DRIVER OK")
        offers = scrape_with_selenium(driver, "REC", "GRU", "2026-02-15", max_cards=15)
        print("TOTAL OFFERS:", len(offers))

        for offer in offers[:5]:
            print(json.dumps(offer, indent=2, ensure_ascii=False))

        total = len(offers)
        with_price = sum(1 for o in offers if o.get("price") is not None)
        with_airline = sum(1 for o in offers if o.get("airline"))
        with_duration = sum(1 for o in offers if o.get("duration_min") is not None)

        print("\n[RESUMO]")
        print(f"total: {total}")
        print(f"com_price: {with_price}")
        print(f"com_airline: {with_airline}")
        print(f"com_duration_min: {with_duration}")
        if total == 0:
            print("DEBUG: verifique a pasta debug/ (viajala_last.html e viajala_last.png)")
            debug_dir = os.path.join(os.getcwd(), "debug")
            try:
                items = os.listdir(debug_dir)[:3]
                print("DEBUG FILES:", items)
            except Exception as e:
                print("DEBUG FILES: error", e)
            url_path = os.path.join(debug_dir, "viajala_last_url.txt")
            try:
                if os.path.exists(url_path):
                    with open(url_path, "r", encoding="utf-8") as f:
                        print("DEBUG URL:", f.read().strip())
            except Exception as e:
                print("DEBUG URL: error", e)
            html_path = os.path.join(debug_dir, "viajala_last.html")
            try:
                if os.path.exists(html_path):
                    with open(html_path, "r", encoding="utf-8") as f:
                        for _ in range(20):
                            line = f.readline()
                            if not line:
                                break
                            print(line.rstrip())
            except Exception as e:
                print("DEBUG HTML: error", e)
    finally:
        close_browser(driver)


if __name__ == "__main__":
    main()
