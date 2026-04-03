# Disposable Exec

Website: https://disposable-exec.com  
Install: https://pypi.org/project/disposable-exec/  
Source: https://github.com/DevBunny-exe/disposable-exec

Run unknown shell or Python code in a disposable environment before it touches your real machine.

Disposable Exec is a short-lived execution API for:
- testing unknown install scripts
- isolating risky shell/python commands
- giving AI agents a controlled execution backend
- capturing stdout, stderr, exit code, and execution status

It is not a general cloud platform, not a long-running container service, and not a replacement for your main host.

## Why use it

Sometimes you see commands like:

```bash
curl something.sh | bash
```

The problem is not only malware. The real problem is uncertainty:
- What files does it create?
- Does it make network requests?
- Does it spawn background processes?
- Does it fail halfway and leave junk behind?
- Do you really want that touching your machine?

Disposable Exec lets you run first, inspect first, and decide later.

## Good fit

Use Disposable Exec when you want to:
- test unknown install/setup steps
- isolate risky CLI commands
- add disposable execution to an automation tool
- give an AI agent code execution without exposing your app host

## Quickstart

Install from PyPI:

```bash
pip install disposable-exec
```

Set your API credentials:

```bash
export DISPOSABLE_EXEC_BASE_URL="https://api.disposable-exec.com"
export DISPOSABLE_EXEC_API_KEY="YOUR_API_KEY"
```

Windows PowerShell:

```powershell
$env:DISPOSABLE_EXEC_BASE_URL="https://api.disposable-exec.com"
$env:DISPOSABLE_EXEC_API_KEY="YOUR_API_KEY"
```

### Minimal Python example

```python
from disposable_exec.client import Client

client = Client()

me = client.me()
print(me)

run_resp = client.run("print('hello from disposable exec')")
execution_id = run_resp["execution_id"]

status = client.status(execution_id)
print(status)

result = client.result(execution_id)
print(result)
```

## Core API flow

Typical flow:

1. `me()` — check quota/account state
2. `run()` or `run_files()` — submit execution
3. `status(execution_id)` — poll execution state
4. `result(execution_id)` — fetch stdout/stderr/exit code

Canonical terminal states:
- `completed`
- `failed`

## Client methods

Current Python client methods:

```python
from disposable_exec.client import Client
```

- `Client().me()`
- `Client().run(script)`
- `Client().run_files(entrypoint, files)`
- `Client().diagnose_script(script)`
- `Client().diagnose_files(entrypoint, files)`
- `Client().status(execution_id)`
- `Client().result(execution_id)`

## Examples

### 1) Test a single script

```python
from disposable_exec.client import Client

client = Client()
resp = client.run("print('hello world')")
print(resp)
```

### 2) Diagnose a script before running it

```python
from disposable_exec.client import Client

client = Client()
diag = client.diagnose_script("print('hello from diagnose')")
print(diag)
```

### 3) Run multiple Python files

```python
from disposable_exec.client import Client

client = Client()

files = [
    {"path": "main.py", "content": "from utils import add\nprint(add(2, 2))"},
    {"path": "utils.py", "content": "def add(a, b):\n    return a + b"},
]

resp = client.run_files("main.py", files)
print(resp)
```

### 4) Agent / automation use case

If you are building an agent or automation system, Disposable Exec can be the execution layer instead of letting tools run directly on your app host.

Use it when you want:
- isolated execution
- structured results
- low host risk
- easy API control

## Product positioning

Disposable Exec sells isolation and controlled execution.

It does **not** sell:
- long-lived compute
- arbitrary infrastructure hosting
- a full CI platform
- “just another VPS”

## Pricing

Current plans:

- Free — 50 executions/month
- Starter — 3,000 executions/month
- Pro — 12,000 executions/month
- Scale — 40,000 executions/month

Check the live website for current pricing and plan details.

## Safety note

Disposable Exec reduces the chance that unknown scripts touch your real machine directly. It does not mean every script is safe or that you should stop reviewing suspicious behavior. Isolation is the point, not blind trust.

## Links

- PyPI: https://pypi.org/project/disposable-exec/
- Website: https://disposable-exec.com
- GitHub: https://github.com/DevBunny-exe/disposable-env

## Contact

For product questions or integration inquiries:

- devbunny.exe@gmail.com
