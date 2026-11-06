# SourceHut's supported runtime is Alpine Linux. Build from the signed sr.ht
# package repository instead of compiling development trees in the image.
FROM alpine:3.22 AS platform

ARG SRHT_REPOSITORY=https://mirror.sr.ht/alpine/v3.22/sr.ht
RUN apk add --no-cache ca-certificates curl \
 && echo "${SRHT_REPOSITORY}" >> /etc/apk/repositories \
 && curl -fsSLo /etc/apk/keys/alpine@sr.ht.rsa.pub \
      https://mirror.sr.ht/alpine/alpine%40sr.ht.rsa.pub \
 && apk add --no-cache \
      core.sr.ht sourcehut-migrate \
      meta.sr.ht git.sr.ht hg.sr.ht todo.sr.ht \
      man.sr.ht paste.sr.ht pages.sr.ht hub.sr.ht \
      openssh fcgiwrap spawn-fcgi su-exec dcron curl postgresql-client git-daemon \
 && rm -rf /var/cache/apk/*

# The forced git/hg SSH commands need a small shared group to read their
# restricted dispatcher config without exposing the complete service config.
RUN addgroup -S srht-shell \
 && addgroup git srht-shell \
 && addgroup hg srht-shell

COPY deploy/sshd_config /etc/ssh/sshd_config
COPY deploy/crontab /etc/crontabs/root
COPY deploy/healthcheck.sh /usr/local/bin/healthcheck
COPY deploy/app-entrypoint.sh /usr/local/bin/app-entrypoint
COPY deploy/patch-hg-hook.py /tmp/patch-hg-hook.py
RUN python3 /tmp/patch-hg-hook.py && rm /tmp/patch-hg-hook.py
RUN chmod 0755 /usr/local/bin/healthcheck /usr/local/bin/app-entrypoint
ENTRYPOINT ["/usr/local/bin/app-entrypoint"]
