import requests


class Client:
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:8000"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def run(self, script: str):
        response = requests.post(
            f"{self.base_url}/run",
            headers=self.headers,
            json={"script": script},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def status(self, execution_id: str):
        response = requests.get(
            f"{self.base_url}/status/{execution_id}",
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def result(self, execution_id: str):
        response = requests.get(
            f"{self.base_url}/result/{execution_id}",
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()