import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "kiwi_bot"):
    """
    Retorna logger configurado:
      - console (sempre)
      - arquivo opcional via env LOG_FILE
      - formato com timestamp
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger  # Prevent duplicate handlers
    level = logging.DEBUG if os.environ.get("DEBUG", "0") == "1" else logging.INFO
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    # File handler if LOG_FILE is set
    log_file = os.environ.get("LOG_FILE")
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger
