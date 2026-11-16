# How syncing works

Each pass of a job runs `rsync` twice for every pair: first from the first
folder to the second, then back. Files on an exclude list are skipped (see
[Leave files out](configuration.md#leave-files-out)). Each run copies a file when the other side
does not have it or has an older version of it, and keeps the file's times and
permissions.

## When a pass runs

A started job runs one pass at once, then one pass every `INTERVAL` seconds
(30 by default). If `inotifywait` is installed, a pass also starts as soon as
a file in one of the folders or the job file changes, so the interval is only
the longest wait. Without changes, a pass costs very little, because rsync
compares sizes and times and copies nothing.

The service runs with low CPU priority (`Nice=10`) and idle I/O priority, so
it does not slow down a game that is writing its saves. If it fails, systemd
starts it again after 10 seconds.

## What wins

When a file differs on the two sides, the side with the newer modification
time wins and overwrites the other. There is no conflict copy. If you change
the same file on two machines before they synced, the older change is lost.

## Deletions

With `DELETES=off`, the default, syncman never deletes anything. A file you
delete on one side is copied back from the other side on the next pass. A
renamed file is a new file to rsync, so its old name comes back as well.

With `DELETES=on` (**Sync Deletions** in the panel), syncman remembers after
every pass which files and folders both sides of a pair have. It keeps that
list in `~/.local/state/syncman/`. On the next pass, before copying:

- A file on the list that is gone on one side, and was not changed on the
  other side since the last pass, was deleted. syncman moves the other side's
  copy to the trash.
- If the other side's copy was changed since the last pass, the change wins.
  syncman keeps it and copies it back.
- A folder on the list that is gone on one side is removed on the other side
  if it is empty by then.
- If one side of a pair has no files at all while the list is not empty,
  syncman deletes nothing for that pair and writes a warning to the job's log.
  An empty side is usually a disk that is not mounted or a sync client that has
  not finished yet, not something you deleted.

So a rename moves the file to its new name on both sides, and the old name
goes to the trash. The first pass after you switch deletions on only builds
the list and deletes nothing. Switching deletions off removes the lists, so
switching on again later starts fresh.

The trash is `~/.local/share/syncman/trash/<job>/<date>/`, followed by the
full path the file had. syncman empties the folders of days older than
`TRASH_DAYS` (30 by default) at the start of each pass. To get a file back,
copy it from there to where it was. Uninstalling syncman, even with
`--purge`, keeps the trash, because it holds your files.

## Known gaps

- **Emptying a whole side does not sync.** If you delete every file on one
  side of a pair, syncman takes that for a missing disk and copies the files
  back. Delete them on both sides instead.
- **Only running jobs empty the trash.** The trash of a job you stopped or
  deleted stays until you remove it from
  `~/.local/share/syncman/trash/<job>/`.
- **One machine per pass.** A pass only syncs folders on the same machine.
  Between machines, syncman relies on Nextcloud or another sync client (see
  [Several machines](configuration.md#several-machines)).
