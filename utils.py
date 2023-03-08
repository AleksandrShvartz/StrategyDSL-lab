import functools
import time


def timed(f):
    b = time.perf_counter()

    @functools.wraps(f)
    def wrapper(*a, **kw):
        return f(*a, **kw), time.perf_counter() - b

    return wrapper
