import subprocess
import resource
import tempfile
import os
import time

from disposable_exec.logs import write_log
from disposable_exec.queue import dequeue_job
from disposable_exec.usage import increment_usage
from disposable_exec.results import save_result
from disposable_exec.status import set_status


def set_limits():
    # CPU limit (seconds)
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))

    # Memory limit (128MB)
    memory_limit = 128 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

    # Process limit
    resource.setrlimit(resource.RLIMIT_NPROC, (10, 10))


print("Worker started...")

while True:

    job = dequeue_job()

    if not job:
        time.sleep(0.2)
        continue

    execution_id = job["execution_id"]
    code = job["script"]
    api_key = job["api_key"]

    set_status(execution_id, "running")

    path = None

    try:

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            f.write(code.encode())
            path = f.name

        start = time.time()

        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=10,
            preexec_fn=set_limits
        )

        duration = time.time() - start

        write_log(
            api_key,
            result.stdout,
            result.stderr,
            result.returncode,
            duration
        )

        save_result(
            execution_id,
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "duration": duration
            }
        )

        set_status(execution_id, "finished")

        print("Job finished")

    except Exception as e:

        set_status(execution_id, "failed")

        save_result(
            execution_id,
            {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "duration": 0
            }
        )

    finally:

        increment_usage(api_key)

        if path and os.path.exists(path):
            os.remove(path)