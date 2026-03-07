import subprocess
import sys
import requests
import time

BASE = "http://127.0.0.1:8000"

def ensure_runtime():

    try:
        requests.get(BASE + "/docs", timeout=1)
        return

    except:
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "disposable_exec.server:app", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        time.sleep(1)