# disposable-exec

`disposable-exec` is a Python client for a hosted isolated execution API.

Use it when your agent, automation, or product needs to run short-lived remote code without running that code on your app server, worker host, or end-user machine.

## What this is

Disposable Exec gives you a narrow, practical execution surface:

- API key auth
- remote isolated execution
- cheap diagnostics preflight via `/diagnose`
- single-script and multi-file Python execution
- `/me`, `/run`, `/status`, and `/result`

## Current package scope

This repository currently contains the Python client and related project code used to support the hosted execution service. The published PyPI package is focused on the client install path and API usage flow.

## Who it is for

- agent builders
- automation teams
- backend products with "run generated code" features
- teams that want isolated execution instead of local subprocesses

## Why use it instead of running code locally

Running generated or user-supplied code locally pushes risk and operational burden onto your app infrastructure.

Disposable Exec gives you a separate execution layer so your app can submit code, track execution, and fetch results without embedding sandboxing into the main product.

## 30-second quickstart

1. Choose Free or a paid plan.
2. For Free, complete the self-serve onboarding flow. For paid plans, complete checkout.
3. Get your API key.
4. Call `/me`.
5. Optionally call `/diagnose`.
6. Submit `/run`.
7. Poll `/status`.
8. Fetch `/result`.

Free access is self-serve with `50` credits per month.

Install from PyPI:

```bash
pip install disposable-exec
```

Set your API base URL and key:

```bash
export DISPOSABLE_EXEC_BASE_URL="https://api.disposable-exec.com"
export DISPOSABLE_EXEC_API_KEY="de_xxx"
```

Then initialize the client with explicit values or let it read those environment variables:

```python
from disposable_exec import Client

client = Client()
```

## Minimal curl example

Single script:

```bash
curl -sS "$DISPOSABLE_EXEC_BASE_URL/me" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY"

curl -sS \
  -X POST "$DISPOSABLE_EXEC_BASE_URL/run" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"script":"print(2 + 2)"}'
```

Multi-file Python:

```bash
curl -sS \
  -X POST "$DISPOSABLE_EXEC_BASE_URL/run" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "entrypoint": "main.py",
    "files": [
      {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
      {"path": "utils.py", "content": "def add(a, b):\n    return a + b"}
    ]
  }'
```

Single-script diagnostics:

```bash
curl -sS \
  -X POST "https://api.disposable-exec.com/diagnose" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"script":"print(2 + 2)"}'
```

Multi-file diagnostics:

```bash
curl -sS \
  -X POST "https://api.disposable-exec.com/diagnose" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "entrypoint": "main.py",
    "files": [
      {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
      {"path": "utils.py", "content": "def add(a, b):\n    return a + b"}
    ]
  }'
```

## Minimal Python example

```python
import time

from disposable_exec import Client

client = Client()

print(client.me())

run_response = client.run("print(2 + 2)")
execution_id = run_response["execution_id"]

while True:
    status = client.status(execution_id)
    if status["status"] in {"finished", "completed", "failed"}:
        break
    time.sleep(0.5)

print(client.result(execution_id))
```

Multi-file Python:

```python
import time

from disposable_exec import Client

client = Client()

run_response = client.run_files(
    entrypoint="main.py",
    files=[
        {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
        {"path": "utils.py", "content": "def add(a, b):\n    return a + b"},
    ],
)

execution_id = run_response["execution_id"]

while True:
    status = client.status(execution_id)
    if status["status"] in {"finished", "completed", "failed"}:
        break
    time.sleep(0.5)

print(client.result(execution_id))
```

Diagnostics:

```python
from disposable_exec import Client

client = Client()

print(client.diagnose_script("print(2 + 2)"))
print(
    client.diagnose_files(
        entrypoint="main.py",
        files=[
            {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
            {"path": "utils.py", "content": "def add(a, b):\n    return a + b"},
        ],
    )
)
```

## API shape

Core endpoints:

- `GET /me`
- `POST /diagnose`
- `POST /run`
- `GET /status`
- `GET /result`

Client methods:

- `me()`
- `diagnose_script(script)`
- `diagnose_files(entrypoint, files)`
- `run(script)`
- `run_files(entrypoint, files)`
- `status(execution_id)`
- `result(execution_id)`

Typical flow:

1. get an API key
2. call `/me`
3. optionally call `/diagnose`
4. submit `/run`
5. poll `/status`
6. fetch `/result`

Files payload shape:

```json
{
  "entrypoint": "main.py",
  "files": [
    {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
    {"path": "utils.py", "content": "def add(a, b):\n    return a + b"}
  ]
}
```

Use `script` for the existing single-script path or `entrypoint` plus `files` for multi-file Python execution.

## Diagnostics

`/diagnose` is a cheap preflight layer for obvious issues before full execution.

Diagnostics V1 checks:

- payload shape
- path safety
- entrypoint presence
- hard limits
- Python syntax
- basic local import and file-structure issues where that can be checked cheaply

Diagnostics does not replace execution. `/run` still performs the real execution, and runtime failure handling still stops at the first unhandled runtime failure.

## Usage and credit foundations

Diagnostics and execution are tracked separately.

- diagnostics is the lower-cost preflight layer
- execution is the full isolated run path
- monthly plan quotas are enforced as monthly credits
- payload complexity is based primarily on total content size, not file count alone
- file count is still useful for limits and observability

Current credit computation is a V1 foundation for usage accounting. It is intentionally simple and may evolve without changing the core `/diagnose` or `/run` flow.

## Runtime limits

Disposable Exec is for short-lived execution, not long-running jobs.

Current hosted baseline:

- Python execution
- hard timeout: `30` seconds
- memory limit: `128 MB`
- CPU share limit: `0.5 CPU`
- PID limit: `64`
- read-only root filesystem
- outbound network disabled

Files-mode hard limits:

- max file count: `10`
- max single file size: `256 KB`
- max total content size: `1 MB`

## Local development

```bash
docker build -t disposable-exec-sandbox -f Dockerfile.sandbox .
cp .env.example .env
bash scripts/start_redis.sh
bash scripts/start_server.sh
bash scripts/start_worker.sh
```
