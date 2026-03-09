from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from .auth import verify_api_key
from .plans import get_plan_quota
from .usage import get_usage_count, increment_usage
from .billing import handle_paddle_webhook
from .queue import enqueue_job
from .status import get_status
from .results import get_result

app = FastAPI(title="Disposable Exec API")


class RunRequest(BaseModel):
    script: str


@app.get("/")
def root():
    return {"ok": True, "service": "disposable-exec"}


@app.post("/run")
def run_code(payload: RunRequest, api_key=Depends(verify_api_key)):
    plan = api_key.get("plan", "Free")
    key_id = api_key.get("id")

    if not key_id:
        raise HTTPException(status_code=500, detail="API key record missing id")

    quota = get_plan_quota(plan)
    used = get_usage_count(key_id)

    if used >= quota:
        raise HTTPException(status_code=403, detail="Monthly execution quota exceeded")

    job = enqueue_job(payload.script, key_id)
    increment_usage(key_id)

    return {
        "execution_id": job["execution_id"],
        "plan": plan,
        "used": used + 1,
        "quota": quota,
    }


@app.get("/status/{execution_id}")
def status(execution_id: str, api_key=Depends(verify_api_key)):
    data = get_status(execution_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return data


@app.get("/result/{execution_id}")
def result(execution_id: str, api_key=Depends(verify_api_key)):
    data = get_result(execution_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return data


@app.post("/billing/webhook")
def billing_webhook(payload: dict):
    return handle_paddle_webhook(payload)
