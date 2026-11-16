#!/usr/bin/env bash
# What syncjob does to real folders: copying, deletions, the trash, exclude
# lists, odd names. Each check runs one-shot passes (syncjob <job> --once) in a
# throwaway HOME, so no systemd, no root and nothing outside it is touched.
# Needs bash, rsync and GNU coreutils.  Usage: bash tests/sync.sh
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
SYNCJOB="$PWD/bin/syncjob"

fails=0
ok()  { printf 'ok    %s\n' "$1"; }
bug() { printf 'BUG   %s\n' "$1"; fails=$((fails + 1)); }
check() { if "${@:2}"; then ok "$1"; else bug "$1"; fi; }

# fresh HOME with one job "t" pairing ~/A and ~/B; $1 = syncman.conf lines
setup() {
    H="$(mktemp -d)"
    mkdir -p "$H/.config/syncman/jobs" "$H/A"
    printf '%s\n' "${1:-}" > "$H/.config/syncman/syncman.conf"
    # a job line with ~ on purpose: syncjob expands it
    # shellcheck disable=SC2088
    echo '~/A :: ~/B' > "$H/.config/syncman/jobs/t.job"
}
pass() { HOME="$H" XDG_CONFIG_HOME='' XDG_DATA_HOME='' XDG_STATE_HOME='' bash "$SYNCJOB" t --once >"$H/log" 2>&1; }
done_with() { rm -rf "$H"; }
trashed() { find "$H/.local/share/syncman/trash" -name "$1" 2>/dev/null | grep -q .; }

# ── copying ──────────────────────────────────────────────────────────────────
setup
echo a > "$H/A/a"; mkdir -p "$H/A/sub"; echo s > "$H/A/sub/s"
pass
check "copies both ways, ~ is the home folder" test -f "$H/B/sub/s"
echo b > "$H/B/b"; pass
check "a new file on the second side comes back" test -f "$H/A/b"
sleep 1; echo newer > "$H/B/a"; pass
check "the newer copy wins" grep -qx newer "$H/A/a"
done_with

# ── deletions off (the default) ─────────────────────────────────────────────
setup
echo a > "$H/A/a"; pass; rm "$H/A/a"; pass
check "deletions off: a deleted file comes back" test -f "$H/A/a"
check "deletions off: no state is kept" test ! -e "$H/.local/state/syncman/t"
done_with

# ── deletions on ─────────────────────────────────────────────────────────────
setup "DELETES=on"
echo 1 > "$H/A/gone"; echo 2 > "$H/A/kept"; mkdir -p "$H/A/d/e"; echo 3 > "$H/A/d/e/f"
pass
check "the first pass with deletions on deletes nothing" test -f "$H/B/gone"
rm "$H/A/gone"; rm -r "$H/B/d"; pass
check "deleted on the first side: deleted on the second" test ! -e "$H/B/gone"
check "deleted on the second side: deleted on the first" test ! -e "$H/A/d"
check "deleted files go to the trash" trashed gone
check "the trash keeps the full path" test -f "$H/.local/share/syncman/trash/t/$(date +%F)$H/A/d/e/f"
rm "$H/A/kept"; sleep 1; echo changed > "$H/B/kept"; pass
check "changed on one side, deleted on the other: the change wins" grep -qx changed "$H/A/kept"
mv "$H/A/kept" "$H/A/renamed"; pass
check "a rename is a rename on both sides" test -f "$H/B/renamed" -a ! -e "$H/B/kept"
mv "$H/B" "$H/B.away"; mkdir "$H/B"; pass
check "an empty side deletes nothing" test -f "$H/A/renamed"
check "an empty side is named in the log" grep -q "is empty" "$H/log"
done_with

setup "DELETES=on"
printf x > "$H/A/ü.txt"; printf x > "$H/A/-dash file"; echo s > "$H/A/stays"; pass
rm "$H/B/ü.txt" "$H/B/-dash file"; pass
check "non-ASCII names and a leading dash delete too" test ! -e "$H/A/ü.txt" -a ! -e "$H/A/-dash file"
done_with

setup "DELETES=on"
echo a > "$H/A/a"; pass
sed -i 's/DELETES=on/DELETES=off/' "$H/.config/syncman/syncman.conf"; pass
check "switching deletions off drops the state" test ! -e "$H/.local/state/syncman/t"
done_with

# ── the trash empties itself ────────────────────────────────────────────────
setup "TRASH_DAYS=7"
mkdir -p "$H/.local/share/syncman/trash/t/2000-01-01" "$H/.local/share/syncman/trash/t/$(date +%F)"
echo a > "$H/A/a"; pass
check "trash days older than TRASH_DAYS are emptied" test ! -e "$H/.local/share/syncman/trash/t/2000-01-01"
check "today's trash stays" test -d "$H/.local/share/syncman/trash/t/$(date +%F)"
done_with

# ── exclude lists ────────────────────────────────────────────────────────────
setup "DELETES=on"
echo '*.tmp' > "$H/.config/syncman/exclude"
echo 'cache/' > "$H/A/.syncman-ignore"
echo t > "$H/A/x.tmp"; mkdir -p "$H/A/cache"; echo c > "$H/A/cache/c"; echo k > "$H/A/keep"
pass
check "the global exclude list leaves files out" test ! -e "$H/B/x.tmp"
check ".syncman-ignore leaves folders out" test ! -e "$H/B/cache"
check ".syncman-ignore itself syncs" test -f "$H/B/.syncman-ignore"
echo t > "$H/B/x.tmp"; rm "$H/A/x.tmp"; pass
check "an excluded file is never deleted" test -f "$H/B/x.tmp"
done_with

echo
if (( fails )); then echo "$fails check(s) failed"; exit 1; fi
echo "all checks passed"
