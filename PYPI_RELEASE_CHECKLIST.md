# PyPI Release Checklist

Status: Canonical release checklist
Last reviewed: 2026-04-02

## Before release

- Confirm the version in `app/setup.py` is the next intended release version.
- Confirm `app/README.md` reflects the current external install path and API flow: `/me` -> optional `/diagnose` -> `/run` -> `/status` -> `/result`.
- Confirm the package name is still `disposable-exec`.
- Confirm the upload account and PyPI token are ready before building.

## Build

From `app/`:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

## Publish

From `app/`:

```bash
python -m twine upload dist/*
```

## Fresh install validation

Use a clean virtual environment:

```bash
python -m venv .venv-release-check
. .venv-release-check/bin/activate
pip install --upgrade pip
pip install disposable-exec
```

Set:

```bash
export DISPOSABLE_EXEC_BASE_URL="https://api.disposable-exec.com"
export DISPOSABLE_EXEC_API_KEY="YOUR_API_KEY"
```

## API validation

Check `/me`:

```bash
curl -sS "$DISPOSABLE_EXEC_BASE_URL/me" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY"
```

Optional `/diagnose`:

```bash
curl -sS \
  -X POST "$DISPOSABLE_EXEC_BASE_URL/diagnose" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"script":"print(2 + 2)"}'
```

Submit `/run`:

```bash
curl -sS \
  -X POST "$DISPOSABLE_EXEC_BASE_URL/run" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"script":"print(2 + 2)"}'
```

Poll `/status` with the returned execution id:

```bash
curl -sS "$DISPOSABLE_EXEC_BASE_URL/status/EXECUTION_ID" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY"
```

Fetch `/result`:

```bash
curl -sS "$DISPOSABLE_EXEC_BASE_URL/result/EXECUTION_ID" \
  -H "Authorization: Bearer $DISPOSABLE_EXEC_API_KEY"
```

## Release sanity

- Confirm the package installs without local path hacks.
- Confirm README rendering passed via `twine check`.
- Confirm `/me` works with the published package.
- Confirm `/diagnose` works with the published package.
- Confirm `/run`, `/status`, and `/result` work with the published package.

## If release is bad

- Stop promoting the released version immediately.
- Fix the package in repo, bump to a new version, and publish a clean follow-up release.
- Do not overwrite or delete the bad PyPI version.
- Record the bad version number, user-facing symptom, and the fixed replacement version.
