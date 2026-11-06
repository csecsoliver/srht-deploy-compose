#!/bin/sh
set -eu

port=${1:?usage: healthcheck PORT}
status=$(curl --silent --show-error --max-time 3 --output /dev/null \
    --write-out '%{http_code}' "http://127.0.0.1:${port}/" || true)
case "$status" in
    2??|3??|4??) exit 0 ;;
    *) echo "service on port ${port} returned HTTP ${status:-000}" >&2; exit 1 ;;
esac
