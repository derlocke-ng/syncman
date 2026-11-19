#!/usr/bin/env bash
# Release gate: the version is the same everywhere it is written down, and the
# scripts are executable in git. The release workflow runs this before it
# publishes, kiwi-release before it tags, and CI on every push.
set -euo pipefail
cd "$(dirname "$0")/.."

rc=0
bad() { echo "check-version: $*" >&2; rc=1; }

m="$(sed -n 's/^VERSION=//p' kiwi.manifest | head -1)"
b="$(sed -n 's/^SYNCMAN_VERSION="\(.*\)"/\1/p' bin/syncman | head -1)"
c="$(grep -m1 -oE '^## [0-9]+(\.[0-9]+)*' CHANGELOG.md | cut -c4-)"
[[ $b == "$m" ]] || bad "bin/syncman says $b, kiwi.manifest says $m"
[[ $c == "$m" ]] || bad "the newest CHANGELOG.md section is $c, kiwi.manifest says $m"
p="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' src/syncman/__init__.py | head -1)"
[[ $p == "$m" ]] || bad "src/syncman/__init__.py says $p, kiwi.manifest says $m"

for f in bin/syncman bin/syncjob install.sh tests/*.sh tools/*.sh; do
    mode="$(git ls-files -s -- "$f" | cut -d' ' -f1)"
    [[ -z $mode || $mode == 100755 ]] || bad "$f is not executable in git (git update-index --chmod=+x $f)"
done

(( rc )) || echo "check-version: ok ($m)"
exit $rc
