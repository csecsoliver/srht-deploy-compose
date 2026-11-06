#!/bin/sh
set -eu

create_database() {
	role=$1
	database=$2
	password=$3
	psql --username "$POSTGRES_USER" --dbname postgres \
		--set ON_ERROR_STOP=1 \
		--set role_name="$role" \
		--set database_name="$database" \
		--set role_password="$password" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'role_name', :'role_password') \gexec
SELECT format('CREATE DATABASE %I OWNER %I', :'database_name', :'role_name') \gexec
SQL
}

create_database meta 'meta.sr.ht' "$DB_META_PASSWORD"
create_database git 'git.sr.ht' "$DB_GIT_PASSWORD"
create_database hg 'hg.sr.ht' "$DB_HG_PASSWORD"
create_database todo 'todo.sr.ht' "$DB_TODO_PASSWORD"
create_database man 'man.sr.ht' "$DB_MAN_PASSWORD"
create_database paste 'paste.sr.ht' "$DB_PASTE_PASSWORD"
create_database pages 'pages.sr.ht' "$DB_PAGES_PASSWORD"
create_database hub 'hub.sr.ht' "$DB_HUB_PASSWORD"
