# Changelog

Releases before 0.4.0 were the Nova Network edition; their history is in the
release commit subjects.

## 0.6.0 — 2026-11-19

- **The panel is laid out like the other Kiwi apps.** It is built on the kit
  from [kiwi-template](https://github.com/derlocke-ng/kiwi-template), the
  first app to use it.
  - **+** in the header creates a job; the "New Sync Job" row is gone.
  - A menu (☰) with Start Selected, Stop Selected, Help and About.
  - Settings moved behind the gear, into Preferences: Syncing (interval,
    jobs folder, exclude list), Deletions, Appearance and Window. The
    interval is saved as you change it; there is no Save button.
  - Results are shown as toasts; the status line at the bottom is gone, the
    number of jobs is under the title.
  - With no job, the window says what a job is and offers to create one.
  - The log and the editor are dialogs in the window, not windows of their own.
- The app icon choice moved from `syncman.conf` (`ICON_COLOR`, `ICON_STYLE`,
  `ICON_FILE`) to `~/.config/syncman/settings.json`. It is moved the first
  time 0.6.0 runs, and the update keeps your icon.
- The panel is a Python package in `~/.local/lib/syncman/`;
  `~/.local/share/syncman/` no longer holds program files, only the trash.
- The command and the worker are unchanged.

## 0.5.1 — 2026-11-16

- A started job now finds `inotifywait` when it is installed with Homebrew.
  The service does not get the PATH of your login shell, so it looked only in
  the system folders and checked for changes every `INTERVAL` seconds instead
  of syncing as soon as a file changed.

## 0.5.0 — 2026-11-16

- **Deletions can sync.** With `DELETES=on` in `syncman.conf` (**Sync
  Deletions** in the panel), a file deleted on one side since the last pass is
  moved to syncman's trash on the other side too, and a rename shows up as a
  rename on both sides. A copy changed on the other side since the last pass
  wins and comes back. If one side of a pair is suddenly empty (a disk not
  mounted, a sync client not finished), nothing is deleted. Off by default.
- **The trash** is `~/.local/share/syncman/trash/<job>/<date>/`; days older
  than `TRASH_DAYS` (30) are emptied. Uninstalling keeps it.
- **Exclude lists**: `~/.config/syncman/exclude` for every job
  (`syncman exclude`), and a `.syncman-ignore` file in a pair's folder for that
  folder and below. Both take rsync patterns; the panel edits both.
- **Choose the app icon** in the panel: the stock cloud kiwi, any kiwi-icons
  colourway and style, or a PNG or SVG of your own. An update keeps it.
- **The panel's window** opens at 760×820, uses a wider column, and remembers
  its size like the other kiwi apps. Paths show `~` for the home folder.
- A leading `~` in a job's pair now means your home folder; it was taken
  literally.
- Uninstall no longer removes `~/.local/share/syncman` as a whole, where the
  trash lives.
- The documentation follows the kiwi-docs guide: a short README and pages in
  `docs/`.

## 0.4.1 — 2026-10-28

- A pair added while a job runs is picked up by the running job: `syncjob`
  reads the job file before every pass, and with `inotifywait` watches it.
- A job file whose last line had no newline got the next pair glued onto that
  line. The panel now ends the file with a newline before it appends.

## 0.4.0 — 2026-10-20

- The Kiwi Network edition: `kiwi.manifest` and a kiwi installer, the
  kiwi-icons cloud kiwi as the icon, `uninstall --purge`, and GPL-3.0-or-later
  as the license.
