# Using syncman

You describe what to sync in a *job*, then start the job. A started job runs
in the background as the systemd user service `syncjob@<job>.service`, and it
starts again after every login until you stop it.

## Jobs

A job is a text file in `~/.config/syncman/jobs/` (or in the folder
`JOBS_DIR` names, see [Configuration](configuration.md)). Its name is the file
name without `.job`, and may contain letters, digits, `.`, `_` and `-`.

Each line is one *pair*: two folders separated by ` :: ` (a space, two colons,
a space). Spaces inside paths need no quoting, and a leading `~` means your
home folder. Text after `#` is a comment.

```
# ~/.config/syncman/jobs/game-saves.job
~/.local/share/Steam/steamapps/common/Half-Life/SAVE :: ~/Nextcloud/game-saves/half-life
~/Games/duke3d/saves :: ~/Nextcloud/game-saves/duke3d
```

The first folder of a pair must exist, or the pair is skipped with a warning
in the job's log. The second folder is created when it is missing. A running
job reads the file again before every pass, so a pair you add or change takes
effect without a restart.

## Commands

| Command | What it does |
|---|---|
| `syncman list` | shows every job with its number of pairs and whether its service runs and is enabled |
| `syncman add <job>` | creates an empty job file, and opens it in `$EDITOR` when you run it in a terminal with `$EDITOR` set |
| `syncman edit <job>` | opens the job file in `$EDITOR`, or in `nano` |
| `syncman exclude` | opens the global exclude list in `$EDITOR`, or in `nano` (see [Configuration](configuration.md#leave-files-out)) |
| `syncman start <job>` | enables and starts the job's service |
| `syncman stop <job>` | stops and disables it |
| `syncman restart <job>` | restarts a running service, for example after you changed `INTERVAL` |
| `syncman sync <job>` | runs one pass now, in the terminal, without the service |
| `syncman log <job>` | follows the job's log in the journal |
| `syncman version` | prints the version |

`start`, `stop`, `restart` and `sync` also take `all`, and use `all` when you
give no job.

## The panel

`syncman-panel`, **Syncman** in the app grid, shows the same jobs. It is
laid out like the other Kiwi apps:

- **+** in the header creates an empty job.
- **Sync Jobs**: one row per job. Open a row for its pairs and its buttons:
  Start or Stop, Sync Now, Log (the last 80 lines), Add Pair (pick the two
  folders), Edit (the job file) and Delete (stops the job and deletes its file;
  the synced folders stay). The button on a pair edits that pair's
  `.syncman-ignore` file.
- **Start Selected** and **Stop Selected**, above the jobs, act on the jobs
  whose check box is ticked, or on all jobs when none is. A job whose name
  ends in `-<this machine's host name>` is ticked when the panel opens.
- **The menu (☰)** opens the jobs folder and the trash folder, and has Help
  and About.
- **The gear** opens Preferences:
  - **Syncing**: the sync interval (saved to `syncman.conf` at once; restart
    the running jobs to use it), a button that opens the jobs folder, and
    the global exclude list.
  - **Deletions**: **Sync Deletions** and how many days the trash keeps
    deleted files, with a button that opens the trash. See
    [How syncing works](how-it-works.md#deletions).
  - **Appearance**: the app icon, see
    [Configuration](configuration.md#the-app-icon).
  - **Window**: the size, with a Reset button.

The panel reads the job states again every five seconds. It opens at the size
it had when you last closed it.
