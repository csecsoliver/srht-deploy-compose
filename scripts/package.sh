#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
version=${1:-$(date -u +%Y%m%d)}
case "$version" in
    *[!A-Za-z0-9._-]*|'') echo "Invalid version: $version" >&2; exit 2 ;;
esac
name="sourcehut-compose-$version"
mkdir -p "$root/dist"
archive="$root/dist/$name.tar.gz"
cd "$root"
tar -czf "$archive" --exclude='*/__pycache__' --exclude='*.pyc' \
    --exclude='deploy/nginx.conf' --transform="s,^,$name/," \
    README.md MIGRATION.md LICENSE Dockerfile compose.yaml .dockerignore .gitignore \
    config.ini.template config.ssh.ini.template deploy scripts
echo "Created $archive"
