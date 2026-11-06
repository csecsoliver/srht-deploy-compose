#!/usr/bin/env python3
"""Create private runtime settings for the SourceHut Compose deployment."""

from __future__ import annotations

import argparse
import base64
import os
import re
import secrets
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == "'":
            value = value[1:-1].replace("\\'", "'").replace("\\\\", "\\")
        elif len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        values[key.strip()] = value
    return values


def write_env(path: Path, values: dict[str, str]) -> None:
    lines = [
        "# Private deployment settings. Keep this file out of version control.",
        *[f"{key}='{value.replace(chr(92), chr(92) * 2).replace(chr(39), chr(92) + chr(39))}'" for key, value in values.items()],
        "",
    ]
    path.write_text("\n".join(lines))
    path.chmod(0o600)


def ensure_pgp(values: dict[str, str]) -> None:
    pgp_dir = ROOT / "pgp"
    private_key = pgp_dir / "privkey.asc"
    public_key = pgp_dir / "pubkey.asc"
    if private_key.exists() and public_key.exists() and values.get("PGP_KEY_ID"):
        return
    if not shutil.which("gpg"):
        raise SystemExit("GnuPG is required to create the SourceHut mail-signing key")

    gnupg_home = pgp_dir / "gnupg"
    gnupg_home.mkdir(parents=True, exist_ok=True)
    gnupg_home.chmod(0o700)
    identity = f"{values['SITE_NAME']} <postmaster@{values['DOMAIN']}>"
    subprocess.run(
        [
            "gpg", "--homedir", str(gnupg_home), "--batch", "--pinentry-mode",
            "loopback", "--passphrase", "", "--quick-generate-key", identity,
            "ed25519", "sign", "0",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    listing = subprocess.check_output(
        ["gpg", "--homedir", str(gnupg_home), "--batch", "--with-colons", "--list-secret-keys"],
        text=True,
    )
    fingerprint = next(
        line.split(":")[9]
        for line in listing.splitlines()
        if line.startswith("fpr:")
    )
    secret = subprocess.check_output(
        ["gpg", "--homedir", str(gnupg_home), "--batch", "--armor", "--export-secret-keys", fingerprint]
    )
    public = subprocess.check_output(
        ["gpg", "--homedir", str(gnupg_home), "--batch", "--armor", "--export", fingerprint]
    )
    private_key.write_bytes(secret)
    private_key.chmod(0o600)
    public_key.write_bytes(public)
    public_key.chmod(0o644)
    values["PGP_KEY_ID"] = fingerprint[-16:]


def render(template: Path, destination: Path, values: dict[str, str], mode: int) -> None:
    source = template.read_text()
    missing = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", source)) - values.keys())
    if missing:
        raise SystemExit(f"Missing settings for {destination}: {', '.join(missing)}")
    for key, value in values.items():
        source = source.replace("{{" + key + "}}", value)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(source)
    destination.chmod(mode)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain", nargs="?", help="base DNS domain, e.g. srht.example.org")
    args = parser.parse_args()

    env_path = ROOT / ".env"
    values = read_env(env_path)
    domain = args.domain or values.get("DOMAIN")
    if not domain or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", domain):
        raise SystemExit("Usage: scripts/bootstrap.py <base-domain> (use a real public domain for production)")

    http_port = values.get("HTTP_PORT", "8080")
    if http_port == "80":
        http_port = "8080"  # Migrate the previous public-HTTP default to the Caddy backend port.

    values.update({
        "DOMAIN": domain.lower(),
        "SITE_NAME": values.get("SITE_NAME", "SourceHut"),
        "SITE_BLURB": values.get("SITE_BLURB", "the hacker's forge"),
        "OWNER_NAME": values.get("OWNER_NAME", "Instance administrator"),
        "OWNER_EMAIL": values.get("OWNER_EMAIL", f"postmaster@{domain}"),
        "SMTP_HOST": values.get("SMTP_HOST", "smtp.example.net"),
        "SMTP_PORT": values.get("SMTP_PORT", "587"),
        "SMTP_USER": values.get("SMTP_USER", ""),
        "SMTP_PASSWORD": values.get("SMTP_PASSWORD", ""),
        "SMTP_FROM": values.get("SMTP_FROM", f"sourcehut@{domain}"),
        "SMTP_ENCRYPTION": values.get("SMTP_ENCRYPTION", "starttls"),
        "SMTP_AUTH": values.get("SMTP_AUTH", "none"),
        "HTTP_PORT": http_port,
        "SSH_PORT": values.get("SSH_PORT", "22"),
        "POSTGRES_PASSWORD": values.get("POSTGRES_PASSWORD", secrets.token_hex(32)),
        "REDICT_PASSWORD": values.get("REDICT_PASSWORD", secrets.token_hex(32)),
        "DB_META_PASSWORD": values.get("DB_META_PASSWORD", secrets.token_hex(32)),
        "DB_GIT_PASSWORD": values.get("DB_GIT_PASSWORD", secrets.token_hex(32)),
        "DB_HG_PASSWORD": values.get("DB_HG_PASSWORD", secrets.token_hex(32)),
        "DB_TODO_PASSWORD": values.get("DB_TODO_PASSWORD", secrets.token_hex(32)),
        "DB_MAN_PASSWORD": values.get("DB_MAN_PASSWORD", secrets.token_hex(32)),
        "DB_PASTE_PASSWORD": values.get("DB_PASTE_PASSWORD", secrets.token_hex(32)),
        "DB_PAGES_PASSWORD": values.get("DB_PAGES_PASSWORD", secrets.token_hex(32)),
        "DB_HUB_PASSWORD": values.get("DB_HUB_PASSWORD", secrets.token_hex(32)),
        "S3_ACCESS_KEY": values.get("S3_ACCESS_KEY", "GK" + secrets.token_hex(16)),
        "S3_SECRET_KEY": values.get("S3_SECRET_KEY", secrets.token_hex(32)),
        "SERVICE_KEY": values.get("SERVICE_KEY", secrets.token_hex(32)),
        "NETWORK_KEY": values.get(
            "NETWORK_KEY", base64.b64encode(secrets.token_bytes(32)).decode("ascii")
        ),
        "WEBHOOK_PRIVATE_KEY": values.get(
            "WEBHOOK_PRIVATE_KEY", base64.b64encode(secrets.token_bytes(32)).decode("ascii")
        ),
        "ADMIN_USER": values.get("ADMIN_USER", "admin"),
        "ADMIN_EMAIL": values.get("ADMIN_EMAIL", f"admin@{domain}"),
        "ADMIN_PASSWORD": values.get("ADMIN_PASSWORD", secrets.token_urlsafe(24)),
    })

    ensure_pgp(values)
    write_env(env_path, values)
    render(ROOT / "config.ini.template", ROOT / "config.ini", values, 0o600)
    render(ROOT / "config.ssh.ini.template", ROOT / "config.ssh.ini", values, 0o600)
    render(ROOT / "deploy/nginx.conf.template", ROOT / "deploy/nginx.conf", values, 0o644)
    print("Runtime config generated. Caddy should terminate public HTTPS and proxy to the local Nginx port.")
    print("SMTP is configured for an external STARTTLS relay; set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, and SMTP_AUTH in .env.")
    print(f"Admin account: {values['ADMIN_USER']} (initial password is stored in .env)")


if __name__ == "__main__":
    main()
