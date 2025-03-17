import threading
from functools import wraps
from typing import Callable
import time


def threaded(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs).start()
    
    return wrapper

def await_condition(condition: Callable[[], bool], timeout: float) -> bool:

    start = time.time()

    while time.time() - start <= timeout:

        if condition():
            return True
        
    return False