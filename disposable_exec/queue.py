import json
import uuid

import redis

from disposable_exec.status import set_status


r = redis.Redis()
QUEUE = "exec_queue"


def enqueue_job(script: str, key_id: str, user_id: str | None = None):
    execution_id = str(uuid.uuid4())

    job = {
        "execution_id": execution_id,
        "script": script,
        "key_id": key_id,
        "user_id": user_id,
    }

    r.lpush(QUEUE, json.dumps(job))
    set_status(execution_id, "queued", key_id=key_id, user_id=user_id)

    return {"execution_id": execution_id}


def dequeue_job():
    job = r.rpop(QUEUE)

    if not job:
        return None

    return json.loads(job)