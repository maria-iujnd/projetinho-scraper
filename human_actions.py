import random
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

class HumanActionsConfig:
    def __init__(self,
                 short_range=(0.2, 0.9),
                 medium_range=(1, 3),
                 rare_range=(6, 12),
                 rare_chance=0.05,
                 typing_micro_delay=(0.03, 0.12),
                 typing_think_chance=0.07,
                 typing_think_range=(0.4, 1.2),
                 scroll_step_range=(40, 120),
                 scroll_pause_range=(0.08, 0.22),
                 scroll_up_chance=0.12,
                 scroll_up_range=(10, 60),
                 click_offset_range=(-3, 3),
                 click_hover_pause=(0.12, 0.35)):
        self.short_range = short_range
        self.medium_range = medium_range
        self.rare_range = rare_range
        self.rare_chance = rare_chance
        self.typing_micro_delay = typing_micro_delay
        self.typing_think_chance = typing_think_chance
        self.typing_think_range = typing_think_range
        self.scroll_step_range = scroll_step_range
        self.scroll_pause_range = scroll_pause_range
        self.scroll_up_chance = scroll_up_chance
        self.scroll_up_range = scroll_up_range
        self.click_offset_range = click_offset_range
        self.click_hover_pause = click_hover_pause

class HumanActions:
    def __init__(self, driver: WebDriver, config: HumanActionsConfig = None):
        self.driver = driver
        self.config = config or HumanActionsConfig()

    # --- Delays ---
    def short_pause(self):
        time.sleep(random.uniform(*self.config.short_range))

    def medium_pause(self):
        time.sleep(random.uniform(*self.config.medium_range))

    def rare_pause(self):
        time.sleep(random.uniform(*self.config.rare_range))

    def maybe_rare_pause(self):
        if random.random() < self.config.rare_chance:
            self.rare_pause()

    def human_pause(self):
        self.medium_pause()
        self.maybe_rare_pause()

    # --- Digitação humana ---
    def type(self, element: WebElement, text: str):
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(*self.config.typing_micro_delay))
            if random.random() < self.config.typing_think_chance:
                time.sleep(random.uniform(*self.config.typing_think_range))

    # --- Scroll humanizado ---
    def scroll(self, total_scroll=1000):
        scrolled = 0
        last_pos = self.driver.execute_script("return window.pageYOffset;")
        while scrolled < total_scroll:
            # Aceleração/desaceleração leve
            if scrolled < total_scroll * 0.2 or scrolled > total_scroll * 0.8:
                step = random.randint(self.config.scroll_step_range[0], int(self.config.scroll_step_range[1]*0.7))
            else:
                step = random.randint(int(self.config.scroll_step_range[0]*1.2), self.config.scroll_step_range[1])
            self.driver.execute_script(f"window.scrollBy(0, {step});")
            scrolled += step
            last_pos += step
            time.sleep(random.uniform(*self.config.scroll_pause_range))
            # Ocasionalmente scroll para cima
            if random.random() < self.config.scroll_up_chance:
                up = random.randint(*self.config.scroll_up_range)
                self.driver.execute_script(f"window.scrollBy(0, {-up});")
                last_pos -= up
                time.sleep(random.uniform(*self.config.scroll_pause_range))
        self.driver.execute_script(f"window.scrollTo(0, {last_pos});")

    # --- Clique humanizado ---
    def click(self, element: WebElement):
        offset_x = random.randint(*self.config.click_offset_range)
        offset_y = random.randint(*self.config.click_offset_range)
        actions = ActionChains(self.driver)
        actions.move_to_element_with_offset(element, offset_x, offset_y)
        actions.pause(random.uniform(*self.config.click_hover_pause))
        actions.click()
        actions.perform()

    # --- Hover ---
    def hover(self, element: WebElement):
        actions = ActionChains(self.driver)
        actions.move_to_element(element)
        actions.pause(random.uniform(*self.config.click_hover_pause))
        actions.perform()

    # --- Seleção de texto ---
    def select_text(self, element: WebElement, offset=80):
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click_and_hold().move_by_offset(offset, 0).release().perform()
        self.short_pause()

# Exemplo de uso:
# from human_actions import HumanActions, HumanActionsConfig
# actions = HumanActions(driver)
# actions.type(element, "texto")
# actions.click(element)
# actions.scroll(1500)
# actions.hover(element)
# actions.select_text(element)
