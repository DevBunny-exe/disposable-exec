import json

STATUS_FILE = "status.json"


def set_status(execution_id, status):

    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
    except:
        data = {}

    data[execution_id] = status

    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)


def get_status(execution_id):

    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
    except:
        return None

    return data.get(execution_id)