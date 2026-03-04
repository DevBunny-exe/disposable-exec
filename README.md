# disposable-env
Run untrusted scripts safely in disposable containers. Logs returned, environment destroyed after execution.
# Disposable Exec

Run untrusted scripts safely in disposable containers.

Each execution runs in an isolated environment.

After execution:
- logs are returned
- container is destroyed

## Why

Running random scripts from the internet can be risky.

This tool lets you run them safely without risking your machine.

## Use cases

- testing unknown GitHub scripts
- verifying AI generated code
- running install scripts safely
- analyzing suspicious commands

## Example

./run.sh "curl example.com/install.sh | bash"

Execution happens inside a disposable container.

Logs are returned and the environment is destroyed afterwards.
