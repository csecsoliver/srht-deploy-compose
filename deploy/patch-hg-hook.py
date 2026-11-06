#!/usr/bin/env python3
"""Make the packaged Hg changegroup hook use its internal service URL."""

from pathlib import Path

hook = Path("/usr/bin/hg.sr.ht-hook-changegroup")
source = hook.read_text()
old = 'origin = cfg("hg.sr.ht", "origin")'
new = 'origin = cfg("hg.sr.ht", "internal-origin", default=cfg("hg.sr.ht", "origin"))'
if source.count(new) == 1:
    raise SystemExit(0)
if source.count(old) != 1:
    raise SystemExit(f"Expected one upstream Hg hook origin setting in {hook}")
hook.write_text(source.replace(old, new))
