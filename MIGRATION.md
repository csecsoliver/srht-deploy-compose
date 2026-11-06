# Changes from the original Compose setup

This deployment replaces the development-oriented Compose stack with a persistent SourceHut installation behind Caddy TLS termination. The release package contains templates and bootstrap scripts, not generated credentials or runtime data.

## Services and Compose

The original Compose file ran Redis, PostgreSQL, and MinIO with five applications (Meta, Todo, Git, Man, and Paste) from local source checkouts. It used Flask debug servers, Compose watch, development ports, and a local LMTP service. It did not provide public TLS, Pages, Hub, or Mercurial.

The new `compose.yaml` builds Alpine 3.22 packages for Meta, Git, Hg, Todo, Man, Paste, Pages, and Hub. Caddy on the host terminates HTTPS, and Nginx routes application requests on a loopback-only HTTP port. A unified SSH service handles Git and Hg access. PostgreSQL uses separate application roles and databases. Authenticated Redict provides Redis-compatible storage, and Silo provides S3-compatible object storage. Persistent volumes hold state. Initialization, schema migration, scheduled jobs, and webhooks have dedicated services. Build and mailing-list services, including incoming Todo email, are excluded.

## Configuration and credentials

The old `config.ini` contained example credentials, shared database access, demo PGP material, local SMTP defaults, development origins, and hostnames. Those values are no longer shipped as active configuration. `config.ini.template` and `config.ssh.ini.template` document generated settings. `scripts/bootstrap.py` creates `.env`, both configs, PGP keys, and Nginx configuration. Generated files are ignored by Git and excluded from release archives.

SMTP values are placeholders. Configure a real relay and set up Caddy with trusted certificates before public use. Pages wildcard certificates require a DNS challenge module. The installation guide documents SMTP settings and Caddy. SSH shell users receive a reduced configuration for Git and Hg. The image build patches the Hg changegroup hook to use the internal service origin for container requests.

## Removed development artifacts

The deployment no longer uses the old Makefile, `hut-config`, checked-in PostgreSQL initialization script, demo PGP keys, or checked-in SSH host keys and configuration. Source checkouts and generated files are not part of the archive. The image installs system packages rather than building from local checkouts.

## Package contents

Run `scripts/package.sh [version]` to create a dated archive under `dist/`. It contains deployment files, templates, documentation, and scripts, and omits `.env`, generated configuration, keys, certificates, database volumes, backups, and local source checkouts.
