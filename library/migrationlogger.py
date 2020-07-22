import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


LOG_LEVEL = logging.INFO
LOGS_DIR = "logs/"
LOG_FILE = "migration.log"
FIVE_MB = 5 * 1024 * 1024
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_logger(script_name):
    logs_dir = Path(LOGS_DIR)
    logs_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
    log_file_name = LOG_FILE
    logger = logging.getLogger(script_name)
    setup_rotating_file_handler(log_file_name, logger)
    setup_console_handler(logger)
    logger.setLevel(LOG_LEVEL)
    return logger


def setup_console_handler(logger):
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVEL)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def setup_rotating_file_handler(log_file_name, logger):
    handler = RotatingFileHandler(LOGS_DIR + log_file_name, maxBytes=FIVE_MB, backupCount=5)
    handler.setLevel(LOG_LEVEL)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return formatter