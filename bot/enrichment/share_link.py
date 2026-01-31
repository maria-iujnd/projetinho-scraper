"""
ShareLinkEnricher: adiciona o link compartilhável real a uma oferta.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time

def extract_share_link_from_modal(driver):
    try:
        input_el = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//input[contains(@value,'kiwi.com')]"
            ))
        )
        return input_el.get_attribute("value")
    except Exception:
        return None

class ShareLinkEnricher:
    @staticmethod
    def apply(driver, card):
        actions = ActionChains(driver)
        actions.move_to_element(card).perform()
        time.sleep(0.5)
        try:
            share_btn = WebDriverWait(card, 5).until(
                lambda _: card.find_element(By.XPATH, ".//button[@data-test='ResultCardShareButton']")
            )
        except Exception as e:
            print(f"[SHARE] Botão Compartilhar não apareceu após hover: {e}")
            return None
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", share_btn)
        time.sleep(0.3)
        try:
            share_btn.click()
            print("[SHARE] Share button clicked.")
        except Exception as e:
            print(f"[SHARE] Click falhou: {e}. Tentando via JS...")
            driver.execute_script("arguments[0].click();", share_btn)
            print("[SHARE] Share button clicked (JS click).")
        time.sleep(1)
        try:
            copy_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Copiar')]"))
            )
            copy_btn.click()
            time.sleep(0.5)
            share_link = extract_share_link_from_modal(driver)
            if not share_link or "kiwi.com" not in share_link:
                print("[SHARE] Falha ao capturar link de compartilhamento!")
                return None
            print(f"[SHARE LINK] {share_link}")
            return share_link
        except Exception as e:
            print(f"[SHARE] Falha ao clicar/copiar: {e}")
            return None
