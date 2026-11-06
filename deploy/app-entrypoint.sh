#!/bin/sh
set -eu

service_user=${SRHT_USER:-root}
config_mode=${SRHT_CONFIG_MODE:-0440}
config_group=${SRHT_CONFIG_GROUP:-$service_user}
id "$service_user" >/dev/null

install -d -m 0750 -o "$service_user" -g "$service_user" /etc/sr.ht/pgp
install -m "$config_mode" -o "$service_user" -g "$service_user" \
	/run/secrets/config.ini /etc/sr.ht/config.ini
if [ "$config_group" != "$service_user" ]; then
	chgrp "$config_group" /etc/sr.ht/config.ini
fi
for key in pubkey.asc privkey.asc; do
	if [ -f "/run/secrets/pgp/$key" ]; then
		install -m 0440 -o "$service_user" -g "$service_user" \
			"/run/secrets/pgp/$key" "/etc/sr.ht/pgp/$key"
	fi
done

exec su-exec "$service_user" "$@"
