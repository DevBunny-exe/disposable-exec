import requests

API_URL = "http://130.51.23.85/run"
TOKEN = "exec_secret_123"

def run(script):
    r = requests.post(
        API_URL,
        json={"script": script},
        headers={"x-token": TOKEN}
    )
    return r.json()
