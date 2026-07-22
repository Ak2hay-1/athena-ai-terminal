"""Docker entrypoint: migrate then exec the API command."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> None:
    print("Running database migrations...", flush=True)
    subprocess.check_call([sys.executable, "-m", "alembic", "upgrade", "head"])
    if not sys.argv[1:]:
        raise SystemExit("No command provided to docker-entrypoint")
    print("Starting Athena API...", flush=True)
    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
