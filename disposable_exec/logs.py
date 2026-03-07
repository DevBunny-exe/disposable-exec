import json
import time
import uuid
import os

LOG_FILE = "execution_logs.jsonl"


def write_log(api_key, stdout, stderr, exit_code, duration):

    log = {
        "execution_id": str(uuid.uuid4()),
        "api_key": api_key,
        "timestamp": int(time.time()),
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "duration": duration
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log) + "\n")