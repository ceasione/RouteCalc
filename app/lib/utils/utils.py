
import logging


def setup_logger(loglevel: str) -> None:
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    logging.basicConfig(level=log_levels[loglevel.upper()],
                        format='%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info(f'loglevel is {loglevel.upper()}')
