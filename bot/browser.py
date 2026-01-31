from __future__ import annotations

import logging
import os
import sys
from typing import Optional, Tuple, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)


def open_browser(
    headless: bool = False,
    user_data_dir: Optional[str] = None,
    profile_dir: Optional[str] = None,
    scope: Optional[str] = None,
    kind: Optional[str] = None,
) -> Tuple[webdriver.Chrome, Dict[str, Any]]:
    chrome_options = Options()

    chrome_binary = os.environ.get("CHROME_BINARY")
    if chrome_binary:
        chrome_options.binary_location = chrome_binary
        logger.info("Chrome binary from CHROME_BINARY: %s", chrome_binary)
    else:
        logger.info("Chrome binary: default")

    if headless:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--window-size=1400,900")
    chrome_options.add_argument("--disable-gpu")

    if sys.platform.startswith("linux"):
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

    if user_data_dir:
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        if profile_dir:
            chrome_options.add_argument(f"--profile-directory={profile_dir}")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
        logger.info("ChromeDriver from CHROMEDRIVER_PATH: %s", chromedriver_path)
    else:
        service = Service()
        logger.info("ChromeDriver: Selenium Manager")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )

    meta = {
        "headless": headless,
        "user_data_dir": user_data_dir,
        "profile_dir": profile_dir,
        "chrome_binary": chrome_binary,
        "chromedriver_path": chromedriver_path,
    }

    return driver, meta


def close_browser(driver: Optional[webdriver.Chrome]) -> None:
    if not driver:
        return
    try:
        driver.quit()
    except Exception:
        pass


def warm_start(driver: webdriver.Chrome, kind: str = "kiwi") -> None:
    """Compatibilidade com imports antigos; no modo atual não faz nada."""
    return
import os
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def open_browser(headless=False, user_data_dir=None, profile_dir=None, scope=None, kind=None):
    chrome_options = Options()

    # Chrome Beta 145
    chrome_options.binary_location = (
        r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe"
    )

    if headless:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,900")

    # Usar perfil de usuário real, se fornecido
    if user_data_dir:
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        if profile_dir:
            chrome_options.add_argument(f"--profile-directory={profile_dir}")

    # Oculta o aviso "Chrome está sendo controlado por um software de teste automatizado"
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(
        executable_path=(
            r"C:\tools\chromedriver145\chromedriver.exe\chromedriver-win64\chromedriver.exe"
        )
    )

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    # Remove a propriedade webdriver do navigator (nem sempre necessário, mas ajuda)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
    )

    return driver, None
    """Compatibilidade com imports antigos; no modo atual não faz nada."""
    return

def close_browser(driver: Optional[webdriver.Chrome]) -> None:
    if not driver:
        return
    try:
        driver.quit()
    except Exception:
        pass


def warm_start(driver: webdriver.Chrome, kind: str = "kiwi") -> None:
    """Compatibilidade com imports antigos; no modo atual não faz nada."""
    return

    def close_browser(driver: Optional[webdriver.Chrome]) -> None:
        if not driver:
            return
        try:
            driver.quit()
        except Exception:
            pass
    opts.add_argument("--disable-gpu")
    if cfg.headless:
        opts.add_argument("--headless=new")
    # Não adiciona opções experimentais para máxima compatibilidade
    if cfg.extra_args:
        for a in cfg.extra_args:
            if a:
                opts.add_argument(a)
    return opts


def _is_driver_alive(driver: webdriver.Chrome) -> bool:
    # Função legacy, não usada na versão minimalista
    return True



