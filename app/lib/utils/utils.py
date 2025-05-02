

def log_safely(message):
    try:
        print(message)
    except OSError:
        pass


def __sliding_window(iterable, n):
    # yields a number of lists where len=n sliced from iterable
    if len(iterable) > n > 0:
        possible_windows = len(iterable) - n + 1
        for pointer in range(0, possible_windows):
            closing = pointer+n
            yield iterable[pointer:closing]
    else:
        yield iterable
