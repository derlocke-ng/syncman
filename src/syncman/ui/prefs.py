"""Syncman's own groups on the General page of Preferences. The dialog,
Appearance and Window are the kit's."""

from __future__ import annotations

import os

from gi.repository import Adw, Gio, GLib, Gtk

from .. import INFO
from ..core import conf
from ..kit.prefs import Preferences
from . import dialogs


def _open_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)
    Gio.AppInfo.launch_default_for_uri(GLib.filename_to_uri(path, None), None)


def show(window) -> None:
    dialog = Preferences(INFO, window.store, window, own_groups=_groups(window))

    def say(text: str) -> None:
        dialog.toast(text)

    window._prefs_say = say
    dialog.connect("closed", lambda *_a: setattr(window, "_prefs_say", None))
    dialog.present(window)


def _groups(window) -> list:
    def say(text: str) -> None:
        (window._prefs_say or window.toast)(text)

    def save(key: str, value, done: str = "") -> None:
        try:
            conf.conf_set(key, value)
        except OSError as exc:
            say(f"Not saved: {exc}")
        else:
            if done:
                say(done)

    # ── Syncing ───────────────────────────────────────────────────────────
    syncing = Adw.PreferencesGroup(title="Syncing")
    interval = Adw.SpinRow(
        title="Sync Interval",
        subtitle="seconds between sync passes; restart running jobs to use it",
        adjustment=Gtk.Adjustment(
            value=conf.conf_int("INTERVAL", 30), lower=1, upper=3600,
            step_increment=1, page_increment=10,
        ),
    )
    interval.connect("notify::value", lambda row, _p: save("INTERVAL", int(row.get_value())))
    syncing.add(interval)

    folder = Adw.ActionRow(title="Jobs Folder", subtitle=conf.jobs_dir())
    open_jobs = Gtk.Button(
        icon_name="folder-open-symbolic", valign=Gtk.Align.CENTER, tooltip_text="Open Jobs Folder"
    )
    open_jobs.add_css_class("flat")
    open_jobs.connect("clicked", lambda *_a: _open_folder(conf.jobs_dir()))
    folder.add_suffix(open_jobs)
    syncing.add(folder)

    exclude = Adw.ActionRow(title="Exclude List", subtitle="files and folders no job syncs")
    edit = Gtk.Button(label="Edit", valign=Gtk.Align.CENTER)
    edit.connect(
        "clicked",
        lambda *_a: dialogs.edit_file(
            window,
            conf.EXCLUDE_FILE,
            conf.EXCLUDE_SKELETON,
            lambda name: window.toast(f"Saved {name}. A running job picks it up by itself."),
            window.toast,
        ),
    )
    exclude.add_suffix(edit)
    syncing.add(exclude)

    # ── Deletions ─────────────────────────────────────────────────────────
    deletions = Adw.PreferencesGroup(
        title="Deletions",
        description="Off: nothing is ever deleted, and a file deleted on one side "
        "comes back from the other. On: it is moved to the trash on "
        "the other side too.",
    )
    deletes = Adw.SwitchRow(
        title="Sync Deletions",
        subtitle="for every job, from the next pass on",
        active=conf.conf_get("DELETES", "off") == "on",
    )
    deletes.connect(
        "notify::active",
        lambda row, _p: save(
            "DELETES",
            "on" if row.get_active() else "off",
            "Deletions sync from the next pass on."
            if row.get_active()
            else "Deletions no longer sync; nothing is deleted.",
        ),
    )
    deletions.add(deletes)
    trash = Adw.SpinRow(
        title="Keep Trash",
        subtitle="days; 0 keeps it until you empty it",
        adjustment=Gtk.Adjustment(
            value=conf.conf_int("TRASH_DAYS", 30), lower=0, upper=3650,
            step_increment=1, page_increment=7,
        ),
    )
    trash.connect("notify::value", lambda row, _p: save("TRASH_DAYS", int(row.get_value())))
    open_trash = Gtk.Button(
        icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER, tooltip_text="Open the Trash Folder"
    )
    open_trash.add_css_class("flat")
    open_trash.connect("clicked", lambda *_a: _open_folder(conf.TRASH_DIR))
    trash.add_suffix(open_trash)
    deletions.add(trash)
    return [syncing, deletions]
