
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time

def hover_card(driver, card):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
        ActionChains(driver).move_to_element(card).pause(0.2).perform()
        return True
    except Exception:
        # Fallback: tenta hover em um filho (header, etc)
        try:
            header = card.find_element(By.CSS_SELECTOR, 'header, [data-test*="Header"]')
            ActionChains(driver).move_to_element(header).pause(0.2).perform()
            return True
        except Exception:
            return False

def find_share_button(card, wait=None, timeout=2):
    selectors = [
        (By.XPATH, ".//button[contains(., 'Compartilhar') or contains(., 'Share') or contains(@aria-label, 'share') or contains(@aria-label, 'Compartilhar')]") ,
        (By.XPATH, ".//*[contains(@data-test, 'share') or contains(@class, 'share') or contains(@aria-label, 'share') or contains(@aria-label, 'Compartilhar')]") ,
        (By.XPATH, ".//button[contains(., '...') or contains(., 'Mais') or contains(., 'more')]")
    ]
    for by, sel in selectors:
        try:
            if wait:
                btn = wait.until(EC.element_to_be_clickable((by, sel)), timeout=timeout)
            else:
                btn = card.find_element(by, sel)
            return btn
        except Exception:
            continue
    return None

def extract_link_from_share_modal(modal):
    # Tenta input, textarea, href
    try:
        # 1. input com value
        inputs = modal.find_elements(By.CSS_SELECTOR, 'input[value^="http"], textarea')
        for inp in inputs:
            val = inp.get_attribute('value') or inp.text or ''
            val = val.strip()
            if val.startswith('http') and 'kiwi' in val:
                return val
        # 2. href
        links = modal.find_elements(By.CSS_SELECTOR, 'a[href^="http"]')
        for a in links:
            href = a.get_attribute('href')
            if href and href.startswith('http') and 'kiwi' in href:
                return href
        # 3. textContent
        spans = modal.find_elements(By.CSS_SELECTOR, '*')
        for s in spans:
            txt = s.text.strip()
            if txt.startswith('http') and 'kiwi' in txt:
                return txt
    except Exception:
        pass
    return None

def enrich_share_link(driver, wait, *, card_element=None, card_index=0):
    """
    Retorna (share_link, reason). Reason sempre preenchido.
    """
    try:
        # 1. Encontrar card
        if card_element is None:
            cards = driver.find_elements(By.CSS_SELECTOR, '[data-test="ResultCardWrapper"]')
            if not cards or card_index >= len(cards):
                return None, 'CARD_NOT_FOUND'
            card = cards[card_index]
        else:
            card = card_element
        # 2. Hover confiável
        if not hover_card(driver, card):
            return None, 'HOVER_FAILED'
        # 3. Encontrar botão Compartilhar
        share_btn = find_share_button(card, wait)
        if not share_btn:
            return None, 'SHARE_BUTTON_NOT_FOUND'
        # 4. Clicar e esperar modal
        try:
            share_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", share_btn)
        try:
            modal = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@role,'dialog') or contains(@class,'modal') or contains(@data-test,'ShareDialog')]")), timeout=3)
        except TimeoutException:
            return None, 'MODAL_NOT_FOUND'
        # 5. Extrair link do DOM
        link = extract_link_from_share_modal(modal)
        if not link:
            return None, 'LINK_NOT_FOUND'
        # 6. Fechar modal
        try:
            close_btns = modal.find_elements(By.XPATH, ".//button[contains(.,'Fechar') or contains(.,'Close') or contains(@aria-label,'close') or contains(@aria-label,'Fechar')]")
            if close_btns:
                close_btns[0].click()
            else:
                # ESC como fallback
                from selenium.webdriver.common.keys import Keys
                modal.send_keys(Keys.ESCAPE)
        except Exception:
            pass
        return link, 'OK'
    except Exception as e:
        return None, f'SELENIUM_ERROR: {e}'
