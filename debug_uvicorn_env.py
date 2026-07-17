"""Debug probe: why `uvicorn` is not recognized. Writes NDJSON to debug-36b4e1.log."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# #region agent log
LOG_PATH = Path(__file__).resolve().parent / "debug-36b4e1.log"
SESSION = "36b4e1"


def _log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    payload = {
        "sessionId": SESSION,
        "runId": "pre-fix",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


# #endregion

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"


def main() -> None:
    # #region agent log
    cwd = os.getcwd()
    _log(
        "B",
        "debug_uvicorn_env.py:cwd",
        "current working directory",
        {
            "cwd": cwd,
            "is_backend": Path(cwd).resolve() == BACKEND.resolve(),
            "backend_main_exists": (BACKEND / "app" / "main.py").exists(),
            "cwd_main_exists": (Path(cwd) / "app" / "main.py").exists(),
        },
    )

    uvicorn_on_path = shutil.which("uvicorn")
    scripts_user = Path(os.environ.get("APPDATA", "")) / "Python" / "Python313" / "Scripts"
    uvicorn_exe = scripts_user / "uvicorn.exe"
    path_entries = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    scripts_on_path = str(scripts_user) in path_entries or any(
        "Roaming\\Python\\Python313\\Scripts" in p or "Roaming/Python/Python313/Scripts" in p
        for p in path_entries
    )
    _log(
        "A",
        "debug_uvicorn_env.py:path",
        "uvicorn CLI PATH check",
        {
            "which_uvicorn": uvicorn_on_path,
            "uvicorn_exe_exists": uvicorn_exe.exists(),
            "uvicorn_exe_path": str(uvicorn_exe),
            "user_scripts_on_path": scripts_on_path,
            "path_python_related": [p for p in path_entries if "Python" in p or "Scripts" in p],
        },
    )

    _log(
        "C",
        "debug_uvicorn_env.py:venv",
        "virtualenv status",
        {
            "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
            "venv_dirs": {
                str(p): p.exists()
                for p in [ROOT / ".venv", ROOT / "venv", BACKEND / ".venv", BACKEND / "venv"]
            },
            "in_venv": getattr(sys, "base_prefix", sys.prefix) != sys.prefix,
            "prefix": sys.prefix,
        },
    )

    _log(
        "D",
        "debug_uvicorn_env.py:python",
        "python interpreter",
        {
            "executable": sys.executable,
            "version": sys.version,
            "version_info": list(sys.version_info[:3]),
        },
    )

    mod_ok = False
    mod_err = None
    try:
        import uvicorn as _u

        mod_ok = True
        mod_ver = getattr(_u, "__version__", "unknown")
    except Exception as e:  # noqa: BLE001
        mod_ver = None
        mod_err = repr(e)

    _log(
        "E",
        "debug_uvicorn_env.py:import",
        "uvicorn package import",
        {"import_ok": mod_ok, "version": mod_ver, "error": mod_err},
    )

    module_cli = None
    try:
        r = subprocess.run(
            [sys.executable, "-m", "uvicorn", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        module_cli = {
            "returncode": r.returncode,
            "stdout": (r.stdout or "").strip(),
            "stderr": (r.stderr or "").strip(),
        }
    except Exception as e:  # noqa: BLE001
        module_cli = {"error": repr(e)}

    _log(
        "A",
        "debug_uvicorn_env.py:module_cli",
        "python -m uvicorn works",
        module_cli,
    )
    # #endregion

    print(f"Wrote debug logs to {LOG_PATH}")
    print(f"which uvicorn: {uvicorn_on_path}")
    print(f"python -m uvicorn: {module_cli}")
    print(f"cwd is backend: {Path(cwd).resolve() == BACKEND.resolve()}")


if __name__ == "__main__":
    main()
