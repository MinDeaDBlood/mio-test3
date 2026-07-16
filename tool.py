#!/bin/env python3
import sys
import time

sys_stdout = sys.stdout
sys_stderr = sys.stderr
if sys.version_info.major == 3:
    if sys.version_info.minor < 8:
        input(
            f"Not supported: [{sys.version}] yet\nEnter to quit\nSorry for any inconvenience caused"
        )
        sys.exit(1)
try:
    from src.app.entrypoint import init
except Exception as e:
    sys.stdout = sys_stdout
    sys.stderr = sys_stderr
    print(e)
    print("Sorry! We cannot init the tool.\nPlease report this error to developers.!")
    time.sleep(3)
    sys.exit(1)

if __name__ == "__main__":
    init(sys.argv)
