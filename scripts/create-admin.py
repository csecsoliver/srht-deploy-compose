#!/usr/bin/env python3
"""Create or update the configured SourceHut administrator account."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
values: dict[str, str] = {}
for line in (ROOT / ".env").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == "'":
        value = value[1:-1].replace("\\'", "'").replace("\\\\", "\\")
    values[key] = value

try:
    password = values["ADMIN_PASSWORD"]
    username = values["ADMIN_USER"]
    email = values["ADMIN_EMAIL"]
except KeyError as error:
    sys.exit(f"Missing {error.args[0]} in .env; run scripts/bootstrap.py first")

command = [
    "docker", "compose", "exec", "-T", "meta",
    "/usr/bin/meta.sr.ht-manageuser", "-p", "-s", "-t", "ADMIN",
    "-e", email, username,
]
subprocess.run(command, input=password + "\n", text=True, check=True, cwd=ROOT)
print(f"Administrator account {username!r} is ready. The password is stored in .env.")
