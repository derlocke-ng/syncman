"""syncman.conf, the job files and the `syncman` command.

syncman.conf (KEY=value lines) belongs to the bash side: bin/syncman and
bin/syncjob read it. The panel's own choices (icon, window) are in
settings.json and window.json, which the kit keeps.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path

from .. import INFO

HOSTNAME = socket.gethostname()
HOME = os.path.expanduser("~")
CONF_DIR = str(INFO.config_dir())
CONF_FILE = os.path.join(CONF_DIR, "syncman.conf")
EXCLUDE_FILE = os.path.join(CONF_DIR, "exclude")
IGNORE_NAME = ".syncman-ignore"
TRASH_DIR = str(INFO.data_dir() / "trash")

EXCLUDE_SKELETON = """\
# syncman — left out of every job. One rsync pattern per line:
#   *.tmp       files ending in .tmp, in any folder
#   cache/      every folder named cache, with all it holds
#   /logs/      only the folder logs at the top of a pair's folders
"""
IGNORE_SKELETON = """\
# syncman — left out for this folder and everything below it.
# This file syncs too, so both sides of the pair use it.
# One rsync pattern per line:
#   *.tmp       files ending in .tmp
#   cache/      every folder named cache, with all it holds
"""
JOB_SKELETON = """\
# syncman job — one pair per line, separated by " :: "
# newer files win in both directions; nothing is deleted unless you switch
# on Sync Deletions. A leading ~ is your home folder.
#/path/to/source :: /path/to/destination
"""


def find_cli() -> str | None:
    here = Path(__file__).resolve()
    for c in (
        shutil.which("syncman"),
        os.path.expanduser("~/.local/bin/syncman"),
        str(here.parents[3] / "bin" / "syncman"),  # a checkout
    ):
        if c and os.path.exists(c):
            return os.path.realpath(c)
    return None


def run(cmd: list[str], timeout: int = 20) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except OSError as exc:
        return 1, "", str(exc)


def conf_get(key: str, default: str) -> str:
    try:
        with open(CONF_FILE) as fh:
            for line in fh:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return default


def conf_set(key: str, value) -> None:
    os.makedirs(CONF_DIR, exist_ok=True)
    lines, found = [], False
    try:
        with open(CONF_FILE) as fh:
            lines = fh.readlines()
    except OSError:
        pass
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
    if not found:
        lines.append(f"{key}={value}\n")
    with open(CONF_FILE, "w") as fh:
        fh.writelines(lines)


def conf_drop(keys: tuple[str, ...]) -> None:
    """Remove KEY= lines (keys that moved out of syncman.conf)."""
    try:
        with open(CONF_FILE) as fh:
            lines = fh.readlines()
    except OSError:
        return
    kept = [ln for ln in lines if not ln.startswith(tuple(f"{k}=" for k in keys))]
    if kept != lines:
        with open(CONF_FILE, "w") as fh:
            fh.writelines(kept)


def conf_int(key: str, default: int) -> int:
    try:
        return int(conf_get(key, str(default)))
    except ValueError:
        return default


def jobs_dir() -> str:
    return os.path.expanduser(conf_get("JOBS_DIR", os.path.join(CONF_DIR, "jobs")))


def parse_pairs(fpath: str) -> list[tuple[str, str]]:
    """Pairs from a .job file — same rules as the syncjob worker."""
    pairs = []
    try:
        with open(fpath) as fh:
            for line in fh:
                line = line.split("#", 1)[0]
                if " :: " not in line:
                    continue
                src, dst = line.split(" :: ", 1)
                pairs.append((os.path.expanduser(src.strip()), os.path.expanduser(dst.strip())))
    except OSError:
        pass
    return pairs


def get_jobs() -> list[dict]:
    jobs = []
    d = jobs_dir()
    try:
        names = sorted(f[:-4] for f in os.listdir(d) if f.endswith(".job"))
    except OSError:
        return jobs
    for name in names:
        fpath = os.path.join(d, f"{name}.job")
        unit = f"syncjob@{name}.service"
        _, active, _ = run(["systemctl", "--user", "is-active", unit], timeout=5)
        _, enabled, _ = run(["systemctl", "--user", "is-enabled", unit], timeout=5)
        jobs.append(
            {
                "name": name,
                "file": fpath,
                "pairs": parse_pairs(fpath),
                "active": active == "active",
                "enabled": enabled == "enabled",
            }
        )
    return jobs


def shorten(path: str, maxlen: int = 60) -> str:
    if path == HOME or path.startswith(HOME + os.sep):
        path = "~" + path[len(HOME) :]
    return path if len(path) <= maxlen else "…" + path[-(maxlen - 1) :]


def status_attrs(job: dict) -> tuple[str, str, str]:
    if job["active"]:
        return "active", "media-playback-start-symbolic", "success"
    if job["enabled"]:
        return "enabled (inactive)", "media-playback-pause-symbolic", "warning"
    return "stopped", "media-playback-stop-symbolic", "dim-label"


def add_pair(fpath: str, src: str, dst: str) -> None:
    # a file saved without a final newline would glue the new pair onto the
    # previous line, and the service parsed that as one broken pair
    with open(fpath, "rb+") as fh:
        fh.seek(0, os.SEEK_END)
        if fh.tell() > 0:
            fh.seek(-1, os.SEEK_END)
            if fh.read(1) != b"\n":
                fh.write(b"\n")
    with open(fpath, "a") as fh:
        fh.write(f"{src} :: {dst}\n")
