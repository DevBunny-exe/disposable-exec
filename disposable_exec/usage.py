import json
import os

USAGE_FILE = "usage.json"


def load_usage():
    if not os.path.exists(USAGE_FILE):
        return {}

    with open(USAGE_FILE, "r") as f:
        return json.load(f)


def save_usage(data):
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f)


def increment_usage(api_key):

    usage = load_usage()

    if api_key not in usage:
        usage[api_key] = 0

    usage[api_key] += 1

    save_usage(usage)

    return usage[api_key]