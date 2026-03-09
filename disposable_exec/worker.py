import time

from disposable_exec.logs import write_log
from disposable_exec.queue import dequeue_job
from disposable_exec.results import save_result
from disposable_exec.runtime import run_script_in_docker
from disposable_exec.status import set_status


print("Worker started...")


while True:
    job = dequeue_job()

    if not job:
        time.sleep(0.2)
        continue

    execution_id = job["execution_id"]
    code = job["script"]
    key_id = job.get("key_id")
    user_id = job.get("user_id")

    set_status(execution_id, "running", key_id=key_id, user_id=user_id)

    try:
        output = run_script_in_docker(code, timeout=10)

        write_log(
            execution_id,
            key_id,
            output["stdout"],
            output["stderr"],
            output["exit_code"],
            output["duration"],
        )

        save_result(
            execution_id,
            output,
            key_id=key_id,
            user_id=user_id,
        )

        if output["exit_code"] == -1:
            set_status(execution_id, "failed", key_id=key_id, user_id=user_id)
        else:
            set_status(execution_id, "finished", key_id=key_id, user_id=user_id)

        print(f"Job finished: {execution_id}")

    except Exception as e:
        set_status(execution_id, "failed", key_id=key_id, user_id=user_id)

        save_result(
            execution_id,
            {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "duration": 0,
            },
            key_id=key_id,
            user_id=user_id,
        )

        print(f"Job failed: {execution_id} - {e}")