import random
import time
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys

def human_type(element: WebElement, text: str, think_chance=0.07, think_range=(0.4, 1.2), micro_delay_range=(0.03, 0.12)):
    """
    Digita texto caractere por caractere em um campo, simulando digitação humana.
    :param element: WebElement do Selenium
    :param text: Texto a ser digitado
    :param think_chance: Probabilidade de pausa longa (pensar)
    :param think_range: Intervalo de pausa longa em segundos
    :param micro_delay_range: Intervalo de delay entre teclas em segundos
    """
    for i, char in enumerate(text):
        element.send_keys(char)
        # Micro delay entre teclas
        time.sleep(random.uniform(*micro_delay_range))
        # Ocasionalmente "pensar"
        if random.random() < think_chance:
            time.sleep(random.uniform(*think_range))

# Exemplo de uso:
# from human_typing import human_type
# human_type(driver.find_element(...), "texto de exemplo")
