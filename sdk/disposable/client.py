import requests

API_URL = "http://130.51.23.85:8000/run"

def run(script: str):
    r = requests.post(API_URL, json={"script": script})
    return r.json()
