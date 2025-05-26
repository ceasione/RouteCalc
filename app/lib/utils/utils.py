
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


def __sliding_window(iterable, n):
    # yields a number of lists where len=n sliced from iterable
    if len(iterable) > n > 0:
        possible_windows = len(iterable) - n + 1
        for pointer in range(0, possible_windows):
            closing = pointer+n
            yield iterable[pointer:closing]
    else:
        yield iterable
