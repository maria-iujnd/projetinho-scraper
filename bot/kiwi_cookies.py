from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
import time

def try_accept_cookies(driver, wait, timeout=3) -> bool:
    """
    Tenta aceitar cookies de forma robusta e segura.
    Retorna True se aceitou, False se não achou/não precisou.
    Nunca lança exception por não achar.
    """
    selectors = [
        # Botão por texto
        (By.XPATH, "//button[contains(translate(., 'ACEITAR', 'aceitar'), 'aceitar') or contains(translate(., 'ACCEPT', 'accept'), 'accept')]") ,
        # aria-label
        (By.XPATH, "//button[contains(@aria-label, 'cookie') or contains(@aria-label, 'Cookie')]") ,
        # data-test
        (By.XPATH, "//button[contains(@data-test, 'cookie') or contains(@data-test, 'Cookie')]") ,
        # Dentro de container típico
        (By.XPATH, "//div[contains(@class, 'cookie') or contains(@id, 'cookie')]//button") ,
        # Banner fixo
        (By.XPATH, "//div[contains(@style, 'position:fixed')]//button")
    ]
    for by, sel in selectors:
        try:
            btn = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, sel)))
            btn.click()
            time.sleep(0.5)
            # Espera sumir
            try:
                WebDriverWait(driver, 2).until(EC.invisibility_of_element(btn))
            except Exception:
                pass
            print("[COOKIES] accepted=True")
            return True
        except Exception:
            continue
    print("[COOKIES] accepted=False (not found)")
    return False

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
import time


def try_accept_cookies(driver, timeout: int = 3) -> bool:
    """
    Tenta aceitar cookies de forma segura.
    Retorna True se clicou, False se não encontrou.
    Nunca lança exceção.
    """
    selectors = [
        # Texto do botão
        (By.XPATH, "//button[contains(translate(., 'ACEITAR', 'aceitar'), 'aceitar') or contains(translate(., 'ACCEPT', 'accept'), 'accept')]") ,
        # aria-label
        (By.XPATH, "//button[contains(@aria-label, 'cookie') or contains(@aria-label, 'Cookie')]") ,
        # data-test
        (By.XPATH, "//button[contains(@data-test, 'cookie') or contains(@data-test, 'Cookie')]") ,
        # container típico
        (By.XPATH, "//div[contains(@class, 'cookie') or contains(@id, 'cookie')]//button") ,
        # overlay fixo
        (By.XPATH, "//div[contains(@style, 'position:fixed')]//button") ,
    ]

    for by, sel in selectors:
        try:
            btn = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, sel))
            )
            btn.click()
            time.sleep(0.4)
            try:
                WebDriverWait(driver, 2).until(EC.invisibility_of_element(btn))
            except Exception:
                pass
            print("[COOKIES] accepted=True")
            return True
        except Exception:
            continue

    print("[COOKIES] accepted=False")
    return False


def is_overlay_blocking(driver) -> bool:
    """
    Detecta se há overlay/modal bloqueando interações.
    Deve ser a ÚNICA fonte dessa lógica no projeto.
    """
    try:
        overlays = driver.find_elements(
            By.XPATH,
            "//*[contains(@style,'position:fixed') or contains(@style,'z-index')]"
        )

        for el in overlays:
            try:
                if el.is_displayed() and el.size.get("height", 0) > 30 and el.size.get("width", 0) > 100:
                    return True
            except Exception:
                continue

        # fallback: tentativa de clique no body
        try:
            driver.find_element(By.TAG_NAME, "body").click()
        except ElementClickInterceptedException:
            return True
        except Exception:
            pass

        return False
    except Exception:
        return False
    """
    Detecta overlay/modal visível que bloqueia cliques.
    """
    try:
        # Overlays comuns
        overlays = driver.find_elements(By.XPATH, "//*[contains(@style,'position:fixed') or contains(@style,'z-index')]")
        for el in overlays:
            if el.is_displayed() and el.size['height'] > 30 and el.size['width'] > 100:
                return True
        # Fallback: tenta clicar em body
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.click()
        except ElementClickInterceptedException:
            return True
        except Exception:
            pass
        return False
    except Exception:
        return False
