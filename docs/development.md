# Development

syncman is three bash scripts and one Python package: `bin/syncman` (the
command), `bin/syncjob` (the worker that runs one job), `install.sh`, and
`src/syncman` (the GTK 4 panel).

The panel follows the layout of
[kiwi-template](https://github.com/derlocke-ng/kiwi-template):

| Folder | What |
|---|---|
| `src/syncman/core/` | reading and writing `syncman.conf` and the job files, calling the command. No GTK. |
| `src/syncman/ui/` | the window, its dialogs and syncman's groups in Preferences |
| `src/syncman/kit/` | the kit: header bar, menu, About, Preferences, icon chooser, window size. The same folder in every Kiwi app. |

Do not edit `src/syncman/kit`. It is changed in kiwi-template and copied
from there:

```bash
tools/kit-update.sh
```

`tools/kit-check.sh` fails when the copy differs from the kit it came from.

Run the panel from a checkout with `PYTHONPATH=src python3 -m syncman.ui`.

## Tests

| Script | What it does |
|---|---|
| `tests/sync.sh` | Runs one-shot passes of `syncjob` on real folders in a throwaway home folder and checks the result: copying, deletions, the trash, exclude lists, names with spaces and non-ASCII characters. Prints `ok` or `BUG` per check. Needs only bash, rsync and GNU coreutils, and touches nothing outside a temporary folder. |
| `tests/panel.sh` | Runs `syncman-panel --apply-icon` in a throwaway home folder: an icon chosen before 0.6.0 moves from `syncman.conf` to `settings.json` and is drawn. Needs Python 3, no display. |
| `tests/check-version.sh` | The release gate: `VERSION` in `kiwi.manifest`, `SYNCMAN_VERSION` in `bin/syncman`, `__version__` in `src/syncman/__init__.py` and the newest `CHANGELOG.md` section agree, and the scripts are executable in git. |

Run before a pull request:

```bash
shellcheck -S warning bin/syncman bin/syncjob install.sh tests/*.sh tools/*.sh
bash tools/kit-check.sh
python3 -m compileall -q src
bash tests/check-version.sh
bash tests/sync.sh
bash tests/panel.sh
python3 .claude/skills/kiwi-docs/scripts/check-docs.py .
```

No test starts a systemd service or opens the panel's window.

## CI

Every push and pull request runs the commands above on Ubuntu 24.04 in
GitHub Actions (`.github/workflows/ci.yml`).

## Releases

A release is a signed tag. kiwi installs an app's newest version tag, so the
tag is the release. A maintainer makes and signs it; CI holds no key.

1. CI is green.
2. `VERSION` in `kiwi.manifest`, `SYNCMAN_VERSION` in `bin/syncman` and
   `__version__` in `src/syncman/__init__.py` are the new version.
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
