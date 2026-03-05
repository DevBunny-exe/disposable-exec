# Disposable Execution Runtime for Running Untrusted Scripts

Run untrusted scripts safely in a disposable environment.

Instead of running unknown install scripts on your machine:

curl something.sh | bash

Run them inside a disposable runtime first.

The script runs in an isolated container.
Logs are captured.
The environment is destroyed after execution.

---

## Why

Many install scripts do more than expected:

• download extra files  
• open outbound connections  
• modify PATH  
• run background processes  

This runtime lets you inspect what a script does before running it on your system.

---

## Quick Example (API)

Run a script:


```bash
curl http://130.51.23.85:8000/run \
  -H "Content-Type: application/json" \
  -d '{"script":"curl https://example.com/install.sh | bash"}'
```


Example response:


```json
{
 "job_id": "c19ed036-da52",
 "stdout": "installing dependencies...\ndone",
 "stderr": "",
 "exit_code": 0
}
```


---

## How It Works

Execution flow:

user command  
→ disposable container created  
→ command executed  
→ logs captured  
→ container destroyed  

The host machine is never exposed to the executed script.

---

## Typical Use Cases

• testing `curl | bash` installers  
• inspecting GitHub install scripts  
• running unknown CLI tools safely  
• verifying AI agent commands  

---

## Security

Each script runs in an isolated container.

Container limits:
• 1 CPU
• 512MB RAM
• ephemeral filesystem

The container is destroyed after execution.


## Limits

Designed for short CLI scripts.

Not designed for:

• long-running services  
• persistent infrastructure  
• GUI applications

---

## Example Script


curl https://example.com/install.sh | bash

Example installer script.

---

## Roadmap

Planned features:

• Python SDK  
• CLI tool  
• Web playground  
• Script inspection (network / files)

---

## License

MIT
