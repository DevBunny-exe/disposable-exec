import requests
from .runtime import ensure_runtime

BASE = "http://127.0.0.1:8000"

def run(code):

    ensure_runtime()

    r = requests.post(
        BASE + "/run",
        json={"script": code}
    )

    return r.json()