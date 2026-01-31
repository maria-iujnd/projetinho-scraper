import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


options = Options()
options.add_argument(r"--user-data-dir=C:\Users\mbjr2\AppData\Local\Google\Chrome Beta\User Data")
options.add_argument("--profile-directory=Default")
driver = webdriver.Chrome(options=options)

def parse_price_brl(label: str) -> int | None:
    match = re.search(r"A partir de\s*([0-9\.]+)", label)
    if not match:
        match = re.search(r"R\$\s*([0-9\.]+)", label)
    if not match:
        return None
    value = match.group(1).replace(".", "")
    if not value.isdigit():
        return None
    return int(value)

def parse_duration_to_minutes(text: str) -> int | None:
    match = re.search(r"(\d+)h(?:\s*(\d+)\s*min)?", text)
    if not match:
        return None
    hours = int(match.group(1))
    minutes = int(match.group(2)) if match.group(2) else 0
    return hours * 60 + minutes

def parse_flight_from_text(text: str) -> dict | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 5:
        return None
    times = lines[0]
    airline = lines[1]
    duration = lines[2]
    route = lines[3]
    price_line = lines[4]

    if "–" not in times or "–" not in route:
        return None

    dep, arr = [t.strip() for t in times.split("–", 1)]
    origin, destination = [x.strip() for x in route.split("–", 1)]
    price = parse_price_brl(price_line)
    if price is None:
        return None

    return {
        "departure_time": dep,
        "arrival_time": arr,
        "airline": airline,
        "duration": duration,
        "duration_min": parse_duration_to_minutes(duration),
        "origin": origin,
        "destination": destination,
        "price_brl": price,
    }

def get_best_flight_by_price() -> dict | None:
    cards = driver.find_elements(By.CSS_SELECTOR, "[role='link'][aria-label*='A partir de']")
    best = None
    for card in cards:
        label = card.get_attribute("aria-label") or ""
        flight = parse_flight_from_text(label)
        if not flight:
            continue
        if best is None or flight["price_brl"] < best["price_brl"]:
            best = flight
    return best

driver.get("https://www.google.com/travel/flights")

WebDriverWait(driver, 30).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[role='link'][aria-label*='A partir de']"))
)

best = get_best_flight_by_price()
if best:
    print(f"Melhor opção por preço: R$ {best['price_brl']}")
    print(best)
else:
    print("Nenhum cartão de voo encontrado.")

driver.quit()
