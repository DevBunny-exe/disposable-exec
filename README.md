# Disposable Exec

Safe sandbox for AI-generated code.

Disposable Exec is a lightweight hosted execution layer for AI agents, automation tools, and LLM-powered products. It allows untrusted or AI-generated Python code to run in an isolated Docker sandbox instead of on your main machine or application host.

## Positioning

Disposable Exec is not a general cloud compute platform and is not trying to compete with heavy sandbox infrastructure platforms.

Its lane is:

- lightweight hosted execution
- safer runtime for AI-generated code
- developer-friendly integration for agents and automations

## Core capabilities

- Run short-lived Python scripts remotely
- Return structured results:
  - `stdout`
  - `stderr`
  - `exit_code`
  - `duration`
- Queue-based execution with worker model
- API key authentication
- Monthly plan quota enforcement
- Subscription-aware access control
- Provider-agnostic billing webhook layer
- Docker sandbox execution with:
  - CPU limits
  - memory limits
  - PID limits
  - read-only root filesystem
  - no outbound network
  - timeout enforcement

## Current pricing model

- Free: 50 executions
- Starter: $9 / month, 3,000 executions
- Pro: $29 / month, 20,000 executions
- Scale: $99 / month, 100,000 executions

## Who this is for

- AI builders
- agent developers
- automation developers
- small teams shipping LLM-powered tools
- developers who do not want to build and maintain their own sandbox runtime

## Why use it

AI agents can generate code easily. Running that code safely in production is harder.

Disposable Exec helps by providing:

- isolated execution
- usage controls
- key lifecycle
- quota enforcement
- remote execution results
- lower operational overhead than self-hosting everything from scratch

## API overview

### Run a script

`POST /run`

Request:

```json
{
  "script": "print(2 + 2)"
}
```

Response:

```json
{
  "execution_id": "..."
}
```

### Check status

`GET /status/{execution_id}`

Returns one of:

- `queued`
- `running`
- `finished`
- `failed`

### Fetch result

`GET /result/{execution_id}`

Example response:

```json
{
  "stdout": "4\n",
  "stderr": "",
  "exit_code": 0,
  "duration": 0.12
}
```

### Inspect current identity

`GET /me`

Returns current API key info and latest subscription snapshot.

### Manage API keys

- `GET /apikey`
- `POST /apikey`
- `DELETE /apikey/{key_id}`

## Local development

### Build sandbox image

```bash
docker build -t disposable-exec-sandbox -f Dockerfile.sandbox .
```

### Start Redis

```bash
redis-server --daemonize yes
```

### Start API

```bash
python3 -m uvicorn disposable_exec.server:app --host 0.0.0.0 --port 8000
```

### Start worker

```bash
python3 -m disposable_exec.worker
```

## Example request

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"script":"print(7+7)"}'
```

## Admin endpoints

Admin endpoints are intended for internal or operator use.

Examples:

```bash
curl -H "X-Admin-Token: change-this-admin-token" \
http://127.0.0.1:8000/admin/users
```

```bash
curl -H "X-Admin-Token: change-this-admin-token" \
http://127.0.0.1:8000/admin/subscriptions
```

## Billing webhook routes

Current webhook routes:

- `POST /billing/webhook/paddle`
- `POST /billing/webhook/lemon`
- `POST /billing/webhook/polar`
- `POST /billing/webhook/stripe`

These currently normalize incoming billing events into a shared internal subscription model.

## Current architecture

- FastAPI
- Redis queue
- Worker process
- SQLite (current development storage)
- Docker sandbox
- API key auth
- usage quota tracking
- billing webhook abstraction

## Current project state

This project is currently an MVP or early production skeleton.

Already implemented:

- Docker sandbox execution
- timeout and network isolation
- SQLite-backed key, usage, result, and status storage
- API key lifecycle basics
- subscription lifecycle basics
- provider-agnostic billing adapter basics
- rate limiting basics
- admin protection basics

Still expected to improve:

- richer billing lifecycle handling
- production-grade database migration beyond SQLite
- monitoring and observability
- stronger abuse controls
- more examples and SDK polish

## Security notes

This project is designed for short-lived execution workloads, not long-running infrastructure or persistent user sessions.

The current sandbox model includes:

- Docker-based isolation
- low memory and CPU limits
- process limits
- no outbound network
- timeout kill

## Roadmap

Planned next steps:

- stronger billing lifecycle handling
- examples for agent frameworks
- LangChain, MCP, and tool integrations
- improved production deployment workflow
- stronger production database setup
- better monitoring and abuse visibility

## License

MIT