import os

def validate_workdir(path: str) -> bool:
    return bool(path) and os.path.isdir(path)
