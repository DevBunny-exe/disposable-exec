from fastapi import FastAPI, Depends, HTTPException
from disposable_exec.auth import verify_api_key
from disposable_exec.rate_limit import check_rate_limit
from disposable_exec.queue import enqueue_job
from disposable_exec.plans import check_quota
from disposable_exec.results import get_result
from disposable_exec.status import get_status

app = FastAPI()


@app.post("/run")
def run_code(data: dict, api_key: str = Depends(verify_api_key)):

    check_rate_limit(api_key)

    allowed, quota, used = check_quota(api_key)

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Quota exceeded: {used}/{quota}"
        )

    script = data["script"]

    return enqueue_job(script, api_key)


@app.get("/status/{execution_id}")
def status(execution_id: str):

    status = get_status(execution_id)

    if not status:
        return {"status": "unknown"}

    return {"status": status}

@app.get("/result/{execution_id}")
def result(execution_id: str):

    result = get_result(execution_id)

    if not result:
        return {"status": "pending"}

    return result


