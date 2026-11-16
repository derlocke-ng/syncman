# syncman

syncman keeps pairs of folders on one Linux machine in step, in both
directions. It was written for game saves: you pair a game's save folder with
a folder in your Nextcloud tree, and the saves follow you to every machine
that syncs that tree. It works for any two folders.

It is part of the Kiwi desktop: apps that kiwi-updater installs from git
catalogs. It needs only `rsync` and systemd user services, runs entirely as
your user, and has a GTK4 panel.

- Latest release: **v0.5.0**, in the [Kiwi catalog](https://github.com/derlocke-ng/kiwi-catalog)
- Runs on: Linux with systemd user services; the panel needs GTK4 and
  libadwaita 1.5 or newer. CI tests the sync logic on Ubuntu 24.04.
- License: GPL-3.0-or-later

## Install

```bash
kiwi install syncman
```

Or from a checkout: `./install.sh install`. The installer writes only to your
home folder (`~/.local` and `~/.config`) and never needs root.

## Quick start

```bash
syncman add game-saves      # creates ~/.config/syncman/jobs/game-saves.job
```

Add one line per folder pair to that file, the two folders separated by
` :: `:

```
~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Half-Life/SAVE :: ~/Nextcloud/game-saves/half-life
```

Then `syncman start game-saves` runs the job in the background, now and after
every login. `syncman-panel` (**Syncman** in your app grid) does the same with
buttons.

**Note.** By default syncman copies new and newer files in both directions
and never deletes anything, so a file you delete on one side comes back from
the other. Switch on **Sync Deletions** to move it to syncman's trash on the
other side too. [How syncing works](docs/how-it-works.md) explains both, and
how to leave files out.

## Documentation

| Page | What it covers |
|---|---|
| [Install](docs/install.md) | requirements, install, update, uninstall |
| [Using syncman](docs/usage.md) | jobs, every command, the panel |
| [Configuration](docs/configuration.md) | `syncman.conf`, exclude lists, several machines, the app icon |
| [How syncing works](docs/how-it-works.md) | what is copied and deleted when, and the known gaps |
| [Development](docs/development.md) | tests, CI, releases |

## License

GPL-3.0-or-later; see [LICENSE](LICENSE).
