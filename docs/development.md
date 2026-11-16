# Development

syncman is three bash scripts and one Python program: `bin/syncman` (the
command), `bin/syncjob` (the worker that runs one job), `install.sh`, and
`gui/syncman-panel` (the GTK 4 panel). `gui/kiwi_icon.py` is the icon kit
from [kiwi-icons](https://github.com/derlocke-ng/kiwi-icons) (`kit/kiwi_icon.py`),
copied unchanged; replace it with a newer copy rather than editing it.

## Tests

| Script | What it does |
|---|---|
| `tests/sync.sh` | Runs one-shot passes of `syncjob` on real folders in a throwaway home folder and checks the result: copying, deletions, the trash, exclude lists, names with spaces and non-ASCII characters. Prints `ok` or `BUG` per check. Needs only bash, rsync and GNU coreutils, and touches nothing outside a temporary folder. |
| `tests/check-version.sh` | The release gate: `VERSION` in `kiwi.manifest`, `SYNCMAN_VERSION` in `bin/syncman` and the newest `CHANGELOG.md` section agree, and the scripts are executable in git. |

Run before a pull request:

```bash
shellcheck -S warning bin/syncman bin/syncjob install.sh tests/*.sh
python3 -m py_compile gui/syncman-panel gui/kiwi_icon.py
bash tests/check-version.sh
bash tests/sync.sh
python3 .claude/skills/kiwi-docs/scripts/check-docs.py .
```

No test starts a systemd service or the panel.

## CI

Every push and pull request runs the commands above on Ubuntu 24.04 in
GitHub Actions (`.github/workflows/ci.yml`).

## Releases

A release is a signed tag. kiwi installs an app's newest version tag, so the
tag is the release. A maintainer makes and signs it; CI holds no key.

1. CI is green.
2. `VERSION` in `kiwi.manifest` and `SYNCMAN_VERSION` in `bin/syncman` are the
   new version.
3. `CHANGELOG.md` starts with a `## X.Y.Z — YYYY-MM-DD` section for it.
4. Merge, then on `main`:

   ```bash
   kiwi-release tag --push
   ```

   `kiwi-release` comes with
   [kiwi-updater](https://kiwi-network.eu/docs/desktop/kiwi-updater/). It
   tags `vX.Y.Z`, signed with your release key, after running
   `tests/check-version.sh`. Without it: `git tag -s vX.Y.Z -m vX.Y.Z` and
   `git push origin vX.Y.Z`.

For a pushed `v*` tag, `.github/workflows/release.yml` checks that the tag is
annotated, signed by a key in `.github/allowed_signers`, equal to `VERSION` in
`kiwi.manifest` and newer than every other release, and runs
`tests/check-version.sh`. It then publishes the GitHub release with the
matching section of `CHANGELOG.md` as its notes. The workflow is the same file
in every kiwi app (kiwi-updater's `templates/release.yml`); keep the copies
identical.

The docs in this folder reach kiwi-network.eu with the next release tag, so
run the docs checker before you tag.
