# SourceHut production Compose deployment

For the configuration changes from the original development stack, see [MIGRATION.md](MIGRATION.md). Create a release archive with `scripts/package.sh [version]`.

This Compose project runs the SourceHut suite on Alpine packages from the
signed SourceHut package repository. It includes meta, git, Mercurial, todo,
man, paste, pages, and hub. Mailing lists and builds are not deployed. Incoming
email is disabled; outgoing email uses an external SMTP relay that you provide.

The stack includes PostgreSQL, Redict, Silo for S3-compatible object storage,
OpenSSH, and an Nginx TLS reverse proxy. Persistent data is stored in Docker
volumes. This is a single-host deployment; production DNS and trusted TLS are
required before exposing it publicly.

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

The `*.sites` wildcard serves user Pages sites. Allow inbound TCP ports 80,
443, and 22 (or the custom ports configured below). Generate the private
runtime configuration and start the stack in one step:

```sh
scripts/setup.sh srht.example.org
```

This creates `.env`, `config.ini`, a PGP signing key, the Nginx configuration,
and a temporary self-signed TLS certificate, then builds the stack and creates
an admin account. These files contain secrets and
are excluded from Git. Install a trusted certificate covering the base domain,
all service subdomains, and `*.sites.srht.example.org` as
`certs/fullchain.pem` and `certs/privkey.pem` before public use.

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
python3 scripts/create-admin.py
docker compose ps
```

The admin password is held in `.env`; retrieve it locally and change it after
first login. Do not commit or share `.env`, `config.ini`, `pgp/`, or `certs/`.
If ports 80, 443, or 22 are already in use, set `HTTP_PORT`, `HTTPS_PORT`, or
`SSH_PORT` in `.env` before starting the stack.

## Operations

Check service logs and status with:

```sh
docker compose ps
docker compose logs -f
```

After changing SMTP settings, TLS files, or other rendered settings, rerun
`python3 scripts/bootstrap.py` when applicable, then recreate the affected
services with `docker compose up -d`. The Compose migration job initializes
empty databases and applies pending migrations on subsequent deployments.

Back up PostgreSQL and all persistent data regularly. At minimum, retain the
PostgreSQL dump, Silo object data, git and Mercurial repository volumes, Pages
certificate volume, SSH host keys, `.env`, `config.ini`, PGP keys, and TLS
certificate. Keep backups encrypted and test restoring them. Do not use
`docker compose down -v` for routine maintenance; it deletes the data volumes.

For upgrades, review the SourceHut release notes and package changes, take a
verified backup, then rebuild and recreate the services:

```sh
docker compose build --pull
docker compose up -d
docker compose ps
```

Configure the host kernel with `vm.overcommit_memory=1` for Redict persistence,
and monitor disk space, PostgreSQL, Silo, and the Docker host. SMTP delivery
cannot work until valid external relay settings are supplied.
