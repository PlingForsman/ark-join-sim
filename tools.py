import threading
from functools import wraps
from typing import Callable
import time

class State:
    """Controls the state of the program."""

    running = True
    paused = False
    
    def __init__(self) -> None:
        raise RuntimeError("State class is not meant to be initialized")

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
