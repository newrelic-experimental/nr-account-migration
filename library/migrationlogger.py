import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


LOG_LEVEL = logging.INFO
LOGS_DIR = "logs/"
LOG_FILE = "migration.log"
FIVE_MB = 5 * 1024 * 1024
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_logger(script_name = None):
    return logging.getLogger(script_name)

def setup_console_handler(logger):
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


def setup_rotating_file_handler(log_file_name, logger):
    handler = RotatingFileHandler(
        LOGS_DIR + log_file_name,
        maxBytes=FIVE_MB,
        backupCount=5
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return formatter

def set_log_level(log_level, logger = logging.getLogger()):
    logger.setLevel(log_level)

def init_logging():
    logs_dir = Path(LOGS_DIR)
    logs_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
    log_file_name = LOG_FILE
    root_logger = logging.getLogger()
    setup_rotating_file_handler(log_file_name, root_logger)
    setup_console_handler(root_logger)
    root_logger.setLevel(LOG_LEVEL)

init_logging()