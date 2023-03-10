import functools
import time


def timed(f):

    @functools.wraps(f)
    def wrapper(*a, **kw):
        b = time.perf_counter()
        return f(*a, **kw), time.perf_counter() - b

    return wrapper
