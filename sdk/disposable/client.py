import requests
import time

API_URL = "http://130.51.23.85/run"
RESULT_URL = "http://130.51.23.85/result/"
TOKEN = "free_test_key"

def run(script):
    r = requests.post(
        API_URL,
        json={"script": script},
        headers={"x-token": TOKEN}
    )

    data = r.json()

    if data["status"] != "queued":
        return data

    job_id = data["job_id"]

    while True:
        r = requests.get(RESULT_URL + job_id)
        result = r.json()

        if result["status"] != "running":
            return result

        time.sleep(0.5)
