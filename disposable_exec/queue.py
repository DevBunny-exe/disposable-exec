import redis
import json
import uuid
from disposable_exec.status import set_status

r = redis.Redis()
QUEUE = "exec_queue"


def enqueue_job(script, key_id):
    execution_id = str(uuid.uuid4())

    job = {
        "execution_id": execution_id,
        "script": script,
        "key_id": key_id,
    }

    r.lpush(QUEUE, json.dumps(job))
    set_status(execution_id, "queued")

    return {"execution_id": execution_id}


def dequeue_job():
    job = r.rpop(QUEUE)

    if not job:
        return None

    return json.loads(job)
