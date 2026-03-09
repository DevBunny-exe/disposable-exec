import os
import subprocess
import tempfile
import time
from pathlib import Path


SANDBOX_IMAGE = "disposable-exec-sandbox"


def build_sandbox_image():
    root_dir = Path(__file__).resolve().parent.parent
    dockerfile_path = root_dir / "Dockerfile.sandbox"

    subprocess.run(
        [
            "docker",
            "build",
            "-t",
            SANDBOX_IMAGE,
            "-f",
            str(dockerfile_path),
            str(root_dir),
        ],
        check=True,
    )


def run_script_in_docker(script: str, timeout: int = 10):
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script)
            temp_path = f.name

        start = time.time()

        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--memory=128m",
                "--cpus=0.5",
                "--pids-limit=64",
                "--network=none",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=16m",
                "-v",
                f"{temp_path}:/sandbox/script.py:ro",
                SANDBOX_IMAGE,
                "python",
                "/sandbox/script.py",
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        duration = time.time() - start

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "duration": round(duration, 3),
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Execution timed out",
            "exit_code": -1,
            "duration": float(timeout),
        }

    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "duration": 0.0,
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
