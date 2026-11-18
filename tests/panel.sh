#!/usr/bin/env bash
# What the panel does without a display: `syncman-panel --apply-icon`, which
# install.sh runs. An icon chosen before 0.6.0 (ICON_* in syncman.conf) moves
# to settings.json and is drawn; the stock choice writes nothing.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
export XDG_CONFIG_HOME="$tmp/config" XDG_DATA_HOME="$tmp/data" PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
rc=0
check() { if eval "$2"; then echo "ok   $1"; else echo "BUG  $1"; rc=1; fi; }
icon="$XDG_DATA_HOME/icons/hicolor/scalable/apps/eu.kiwinetwork.Syncman.svg"

python3 -m syncman.ui --apply-icon
check "stock choice: nothing written" '[[ ! -e $icon && ! -e $XDG_CONFIG_HOME/syncman/settings.json ]]'

mkdir -p "$XDG_CONFIG_HOME/syncman"
printf 'INTERVAL=30\nICON_COLOR=ocean\nICON_STYLE=night\nICON_FILE=\n' > "$XDG_CONFIG_HOME/syncman/syncman.conf"
python3 -m syncman.ui --apply-icon
check "old choice moved to settings.json" 'grep -q "\"kit.icon_color\": \"ocean\"" "$XDG_CONFIG_HOME/syncman/settings.json" && grep -q "\"kit.icon_style\": \"night\"" "$XDG_CONFIG_HOME/syncman/settings.json"'
check "ICON_ lines gone, the rest kept" '! grep -q "^ICON_" "$XDG_CONFIG_HOME/syncman/syncman.conf" && grep -q "^INTERVAL=30" "$XDG_CONFIG_HOME/syncman/syncman.conf"'
check "the chosen icon is drawn" 'grep -q "<svg" "$icon"'
# shellcheck disable=SC2034  # read inside check's eval
before="$(sha256sum "$icon")"
python3 -m syncman.ui --apply-icon
check "a second run changes nothing" '[[ "$(sha256sum "$icon")" == "$before" ]]'
exit $rc
