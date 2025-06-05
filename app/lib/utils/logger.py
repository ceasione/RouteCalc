
from app.settings import LOGLEVEL
import logging


log_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

logger = logging.getLogger('RouteCalc')
logger.setLevel(log_levels[LOGLEVEL.upper()])

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('LOGGER.handler was set up')

logger.propagate = False

logger.info(f'loglevel is {LOGLEVEL.upper()}')
