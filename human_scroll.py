import random
import time
from selenium.webdriver.remote.webdriver import WebDriver

def human_scroll(driver: WebDriver, total_scroll=1000, step_range=(40, 120), pause_range=(0.08, 0.22), up_chance=0.12, up_range=(10, 60)):
    """
    Realiza scroll humanizado na página.
    :param driver: Instância do Selenium WebDriver
    :param total_scroll: Distância total a rolar (pixels)
    :param step_range: Intervalo de pixels por passo
    :param pause_range: Intervalo de pausa entre passos (segundos)
    :param up_chance: Probabilidade de ajustar levemente para cima
    :param up_range: Intervalo de ajuste para cima (pixels)
    """
    scrolled = 0
    last_pos = driver.execute_script("return window.pageYOffset;")
    while scrolled < total_scroll:
        # Aceleração/desaceleração leve
        if scrolled < total_scroll * 0.2 or scrolled > total_scroll * 0.8:
            step = random.randint(step_range[0], int(step_range[1]*0.7))
        else:
            step = random.randint(int(step_range[0]*1.2), step_range[1])
        driver.execute_script(f"window.scrollBy(0, {step});")
        scrolled += step
        last_pos += step
        time.sleep(random.uniform(*pause_range))
        # Ocasionalmente scroll para cima
        if random.random() < up_chance:
            up = random.randint(*up_range)
            driver.execute_script(f"window.scrollBy(0, {-up});")
            last_pos -= up
            time.sleep(random.uniform(*pause_range))
    # Garante que não passa do limite
    driver.execute_script(f"window.scrollTo(0, {last_pos});")

# Exemplo de uso:
# from human_scroll import human_scroll
# human_scroll(driver, total_scroll=2000)
