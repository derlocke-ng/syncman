# Configuration

syncman reads its settings from `~/.config/syncman/syncman.conf`, one
`KEY=value` per line. Comments go on their own line, starting with `#`.

## Settings

| Key | Default | What it does |
|---|---|---|
| `INTERVAL` | `30` | Seconds between two passes of a running job. A job reads it when it starts, so restart running jobs after a change (`syncman restart all`). |
| `JOBS_DIR` | `~/.config/syncman/jobs` | The folder with the job files. A leading `~` means your home folder. |
| `ICON_COLOR` | empty | The colourway of the app icon; empty means the stock icon. Set it in the panel. |
| `ICON_STYLE` | `classic` | The style of the app icon: `classic`, `flat` or `night`. |
| `ICON_FILE` | empty | One of your own icon files from `~/.config/syncman/icons/`; it wins over the two above. |

The panel also keeps its window size in `~/.config/syncman/window.json`.

## Several machines

The job files can live in a folder that Nextcloud (or another sync client)
keeps the same on all your machines:

```ini
JOBS_DIR=~/Nextcloud/syncman-jobs
```

Paths differ between machines, so give each machine its own jobs and end
their names with the machine's host name, for example `game-saves-papaya` and
`game-saves-lychee`. Start on each machine only the job with its own name. The
panel checks those jobs for you (see [Using syncman](usage.md#the-panel)). The
second folder of each pair is in the Nextcloud tree, and Nextcloud carries the
files from machine to machine.

## The app icon

The stock icon is the cloud kiwi from
[kiwi-icons](https://github.com/derlocke-ng/kiwi-icons). In the panel, under
**Appearance**, you can choose:

- **App Icon**: the stock icon, the same kiwi in one of the kiwi-icons
  colourways (Ember, Ocean, Forest, the two-tones and the others), or one of
  your own files.
- **Icon Style**: classic, flat or night.

For your own icon, put a PNG or SVG file in `~/.config/syncman/icons/` (the
folder button next to **App Icon** opens it) and open the panel again.

The panel writes the chosen icon to
`~/.local/share/icons/hicolor/scalable/apps/eu.kiwinetwork.Syncman.svg`, where
the app grid finds it. The app grid shows the change once the desktop reloads
its icons, at the latest after you log in again. An update of syncman keeps
your choice. The kiwi-updater app list always shows the stock icon, because it
reads the icon from syncman's repository.
