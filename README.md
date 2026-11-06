# SourceHut production Compose deployment

For the configuration changes from the original development stack, see [MIGRATION.md](MIGRATION.md). Create a release archive with `scripts/package.sh [version]`.

This Compose project runs the SourceHut suite on Alpine packages from the
signed SourceHut package repository. It includes meta, git, Mercurial, todo,
man, paste, pages, and hub. Mailing lists and builds are not deployed. Incoming
email is disabled; outgoing email uses an external SMTP relay that you provide.

The stack includes PostgreSQL, Redict, Silo for S3-compatible object storage,
OpenSSH, and Nginx for application routing. Caddy runs on the host and owns
public HTTPS; Nginx is reachable only through `127.0.0.1:8080`. Persistent data
is stored in Docker volumes.

## First deployment

Use a real base domain, such as `srht.example.org`. Create DNS records pointing
the base domain and each service subdomain to this host:

```text
srht.example.org
meta.srht.example.org
git.srht.example.org
hg.srht.example.org
todo.srht.example.org
man.srht.example.org
paste.srht.example.org
pages.srht.example.org
hub.srht.example.org
*.sites.srht.example.org
```

The `*.sites` wildcard serves user Pages sites. Caddy should listen publicly on
ports 80 and 443; SourceHut SSH uses port 22 by default. Generate the private
runtime configuration and start the stack in one step:

```sh
scripts/setup.sh srht.example.org
```

This creates `.env`, `config.ini`, a PGP signing key, and the Nginx
configuration, then builds the stack and creates an admin account. These files
contain secrets and are excluded from Git. Nginx binds only to the loopback
interface on port 8080; it does not terminate TLS or publish a public web port.

Configure Caddy to reverse proxy the SourceHut hostnames to
`127.0.0.1:8080`. Start from [`deploy/Caddyfile.example`](deploy/Caddyfile.example)
and replace `example.org` with the base domain. The Pages wildcard host
`*.sites.<domain>` requires Caddy's DNS challenge module for your DNS provider;
the example shows Cloudflare. Caddy must pass the original Host and
`X-Forwarded-Proto` headers (Caddy's `reverse_proxy` does this by default).
Keep Caddy's certificate storage persistent. Then reload Caddy.

Edit `.env` and set the SMTP relay values supplied by your provider:
`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_AUTH`,
`SMTP_ENCRYPTION`, and `SMTP_FROM`. Then regenerate the rendered configuration
and start the services:

`SMTP_ENCRYPTION` accepts `starttls`, `tls`, or `insecure`; `SMTP_AUTH` accepts
`plain` or `none`.

```sh
python3 scripts/bootstrap.py
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

The admin password is held in `.env`; retrieve it locally and change it after
first login. Do not commit or share `.env`, `config.ini`, or `pgp/`. If another
process uses SSH port 22, set `SSH_PORT` in `.env` to a free external port.
`HTTP_PORT` changes the loopback-only port Caddy proxies to; update the Caddyfile
to match.

## Fedora and SELinux

Compose bind mounts use SELinux relabel options: shared `:z` labels for the
application config and PGP directory, and private `:Z` labels for files mounted
into one service. This lets PostgreSQL read its initialization script on Fedora
without disabling SELinux or running `chcon` manually. After updating, run
`docker compose up -d` so Compose recreates containers with the new labels.

## Operations

Check service logs and status with:

```sh
docker compose ps
docker compose logs -f
```

After changing SMTP settings or other rendered settings, rerun
`python3 scripts/bootstrap.py` when applicable, then recreate the affected
services with `docker compose up -d`. The initial setup script has already created
the admin account; use `python3 scripts/create-admin.py` only if you need to
create or reset it later. The Compose migration job initializes
empty databases and applies pending migrations on subsequent deployments.

Back up PostgreSQL and all persistent data regularly. At minimum, retain the
PostgreSQL dump, Silo object data, git and Mercurial repository volumes, Pages
certificate volume, SSH host keys, `.env`, `config.ini`, and PGP keys. Back up
Caddy's certificate storage with the host. Keep backups encrypted and test
restoring them. Do not use
`docker compose down -v` for routine maintenance; it deletes the data volumes.

For upgrades, review the SourceHut release notes and package changes, take a
verified backup, then rebuild and recreate the services:

```sh
docker compose build --pull
docker compose up -d
docker compose ps
```

Configure the host kernel with `vm.overcommit_memory=1` for Redict persistence,
and monitor disk space, PostgreSQL, Silo, and the Docker host. SMTP delivery cannot work until valid external relay settings are supplied.
