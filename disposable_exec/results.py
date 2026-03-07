import json
import uuid
import time

RESULT_FILE = "results.json"

def save_result(execution_id, result):
    try:
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}

    data[execution_id] = result

    with open(RESULT_FILE, "w") as f:
        json.dump(data, f)


def get_result(execution_id):
    try:
        with open(RESULT_FILE, "r") as f:
            data = json.load(f)
    except:
        return None

    return data.get(execution_id)