#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <domain>" >&2
    exit 2
fi
domain=$1
for tool in docker python3 gpg; do
    command -v "$tool" >/dev/null 2>&1 || { echo "Required command not found: $tool" >&2; exit 1; }
done
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 is required." >&2; exit 1; }

umask 077
python3 scripts/bootstrap.py "$domain"
docker compose config --quiet
docker compose up -d --build
python3 scripts/create-admin.py

cat <<EOF2

Initial deployment is running for $domain.
Configure Caddy to proxy HTTPS requests to the loopback port in .env (8080
by default) before public use, and configure a real SMTP relay in .env.
See README.md for the Caddy example and operations instructions.
EOF2
