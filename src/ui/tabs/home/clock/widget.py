import time

def current_time_text() -> str:
    return time.strftime('%H:%M:%S', time.localtime())
