# Install syncman

syncman installs into your home folder and runs as your user. Nothing it
installs needs root.

## Requirements

| What | Why |
|---|---|
| `rsync` | copies the files |
| systemd with user services (`systemctl --user`) | runs each started job in the background |
| GTK4, libadwaita 1.5 or newer, PyGObject and Python 3 | only for the panel, `syncman-panel` |
| `inotifywait` from inotify-tools (optional) | starts a pass as soon as a file changes, instead of waiting for the interval. The service finds it on the system and in Homebrew (`/home/linuxbrew/.linuxbrew/bin` or `~/.linuxbrew/bin`) |

On a machine without GTK4 the installer leaves the panel out and installs the
command-line tools only.

## Install with kiwi

syncman is in the Kiwi catalog. If you have not added the catalog yet:

```bash
kiwi catalog add https://github.com/derlocke-ng/kiwi-catalog.git
kiwi install syncman
```

`kiwi install syncman --cli-only` leaves out the panel on a desktop as well.
kiwi updates syncman with your other apps; see
[kiwi-updater](https://kiwi-network.eu/docs/desktop/kiwi-updater/).

## Install from a checkout

```bash
git clone https://github.com/derlocke-ng/syncman.git
cd syncman
./install.sh install
```

## What the installer writes

| Path | What |
|---|---|
| `~/.local/bin/syncman`, `syncjob`, `syncman-panel` | the command, the worker that runs one job, and the panel |
| `~/.local/lib/syncman/` | the panel (a Python package) and the stock icon |
| `~/.local/share/applications/eu.kiwinetwork.Syncman.desktop` | the app-grid entry |
| `~/.local/share/icons/hicolor/scalable/apps/eu.kiwinetwork.Syncman.svg` | the app icon |
| `~/.config/systemd/user/syncjob@.service` | one service template; each started job is an instance of it |
| `~/.config/syncman/syncman.conf` and `jobs/` | your settings and jobs, created on the first install only |

## Update

`kiwi update` (or `./install.sh update` in a checkout) installs the new files
and restarts the jobs that are running, so they use the new worker. An app
icon you chose in the panel is kept.

## Uninstall

```bash
kiwi uninstall syncman
```

This stops and disables every job and removes everything in the table above
except `~/.config/syncman`. Your settings and jobs stay, so a later install
picks them up. `kiwi uninstall syncman --purge` removes `~/.config/syncman`
too. A jobs folder you moved outside it with `JOBS_DIR` is never deleted,
because other machines may read it. The synced folders themselves are never
touched.
