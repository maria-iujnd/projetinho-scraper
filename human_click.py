import random
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains

def human_click(driver: WebDriver, element: WebElement, offset_range=(-3, 3), hover_pause_range=(0.12, 0.35)):
    """
    Move o mouse até o elemento, faz uma pausa e clica com offset aleatório.
    :param driver: Selenium WebDriver
    :param element: WebElement alvo
    :param offset_range: Intervalo de offset aleatório (pixels)
    :param hover_pause_range: Pausa após hover (segundos)
    """
    # Calcula offsets aleatórios
    offset_x = random.randint(*offset_range)
    offset_y = random.randint(*offset_range)
    actions = ActionChains(driver)
    # Move para o centro do elemento com offset
    actions.move_to_element_with_offset(element, offset_x, offset_y)
    actions.pause(random.uniform(*hover_pause_range))
    actions.click()
    actions.perform()

# Exemplo de uso:
# from human_click import human_click
# human_click(driver, driver.find_element(...))
