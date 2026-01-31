import os
import time
import logging
import traceback
from selenium.common.exceptions import WebDriverException

class SeleniumResilience:
    def __init__(self, driver, rate_limit=0.5, max_retries=3, backoff_factor=2, log_path="selenium_resilience.log", debug_dir="debug_selenium"):
        self.driver = driver
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.log_path = log_path
        self.debug_dir = debug_dir
        os.makedirs(debug_dir, exist_ok=True)
        logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    def run_action(self, action, *args, **kwargs):
        retries = 0
        delay = self.rate_limit
        while retries <= self.max_retries:
            try:
                result = action(*args, **kwargs)
                time.sleep(self.rate_limit)
                return result
            except Exception as e:
                retries += 1
                logging.error(f"Erro na ação {action.__name__}: {e}\n{traceback.format_exc()}")
                self._capture_debug(f"{action.__name__}_fail_{int(time.time())}")
                if retries > self.max_retries:
                    logging.error(f"Ação {action.__name__} falhou após {self.max_retries} tentativas.")
                    raise
                time.sleep(delay)
                delay *= self.backoff_factor

    def _capture_debug(self, prefix):
        try:
            screenshot_path = os.path.join(self.debug_dir, f"{prefix}.png")
            html_path = os.path.join(self.debug_dir, f"{prefix}.html")
            self.driver.save_screenshot(screenshot_path)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logging.info(f"Screenshot salvo em {screenshot_path}, HTML salvo em {html_path}")
        except WebDriverException as e:
            logging.error(f"Falha ao capturar debug: {e}")

# Exemplo de uso:
# resilience = SeleniumResilience(driver, rate_limit=0.7)
# resilience.run_action(lambda: driver.get("https://www.google.com"))
