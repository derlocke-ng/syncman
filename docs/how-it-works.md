# How syncing works

Each pass of a job runs `rsync` twice for every pair: first from the first
folder to the second, then back. Each run copies a file when the other side
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

## Known gaps

- **Deleting does not sync.** syncman never deletes. A file you delete on one
  side is copied back from the other side on the next pass. To get rid of a
  file for good, delete it on both sides while the job is stopped.
- **Renaming leaves the old name.** A renamed file is a new file to rsync, so
  the old name comes back from the other side.
- **No exclude list.** Every file in both folders is synced. There is no way
  yet to leave out files or subfolders of a pair.
- **One machine per pass.** A pass only syncs folders on the same machine.
  Between machines, syncman relies on Nextcloud or another sync client (see
  [Several machines](configuration.md#several-machines)).
