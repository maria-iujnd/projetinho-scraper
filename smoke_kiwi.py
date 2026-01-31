from bot.browser import open_browser
from bot.kiwi_scraper import scrape_with_selenium
from bot.kiwi_urls import build_kiwi_url_ow
from selenium.webdriver.support.ui import WebDriverWait
import time

from bot.browser import open_browser
from bot.kiwi_scraper import scrape_with_selenium
from bot.kiwi_urls import build_kiwi_url_ow
from selenium.webdriver.support.ui import WebDriverWait
import time

# Parâmetros do smoke test
origin = "REC"
dest = "GRU"
date = "2026-02-15"
url = build_kiwi_url_ow(origin, dest, date)

print(f"[SMOKE] URL: {url}")

driver = open_browser(headless=False)
wait = WebDriverWait(driver, 30)

# Diagnóstico: imprimir linhas com data-test= logo após carregar a página
try:
    driver.get(url)
    html = driver.page_source
    print("\n[DATA-TEST SNIPPETS]")
    for line in html.splitlines():
        if "data-test=" in line:
            print(line.strip())
    # Agora roda o scraping normalmente
    result = scrape_with_selenium(driver, wait, url, price_ceiling=9999)
finally:
    driver.quit()

print("[SMOKE] status:", result.status)
print("[SMOKE] reason:", result.reason)
print("[SMOKE] n_flights:", len(result.flights))
if result.status == 0 and result.flights:
    print("[SMOKE] SUCESSO: resultados encontrados!")
else:
    print("[SMOKE] FALHA ou BLOQUEIO!")
date = "2026-02-15"
url = build_kiwi_url_ow(origin, dest, date)

print(f"[SMOKE] URL: {url}")

driver.quit()

driver = open_browser(headless=False)
wait = WebDriverWait(driver, 30)

# Diagnóstico: imprimir linhas com data-test= logo após carregar a página
driver.get(url)
html = driver.page_source
print("\n[DATA-TEST SNIPPETS]")
for line in html.splitlines():
    if "data-test=" in line:
        print(line.strip())

result = scrape_with_selenium(driver, wait, url, price_ceiling=9999)
driver.quit()

print("[SMOKE] status:", result.status)
print("[SMOKE] reason:", result.reason)
print("[SMOKE] n_flights:", len(result.flights))
if result.status == 0 and result.flights:
    print("[SMOKE] SUCESSO: resultados encontrados!")
else:
    print("[SMOKE] FALHA ou BLOQUEIO!")
