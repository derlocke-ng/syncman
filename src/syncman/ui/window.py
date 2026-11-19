"""The main window: the sync jobs.

The kit's: header bar, menu, About, Preferences dialog, window size. Syncman's:
the list of jobs, their buttons and dialogs, its groups in Preferences.
Everything a button does goes through the `syncman` command, so the panel
and the command cannot disagree.
"""

from __future__ import annotations

import os
import re

from gi.repository import Adw, Gio, GLib, Gtk

from .. import INFO
from ..core import conf, migrate
from ..kit import geometry, header, icon, worker
from ..kit.settings import Store
from . import dialogs, prefs

REFRESH_MS = 5000
CONTENT_WIDTH = 720  # the page's column; Adw.PreferencesPage would cap it at 600


class Window(Adw.ApplicationWindow):
    def __init__(self, cli: str, **kwargs) -> None:
        super().__init__(title=INFO.name, **kwargs)
        self.cli = cli
        self.store = Store(INFO)
        if migrate.icon_settings(self.store):
            icon.apply(INFO, self.store)
        geometry.restore(self, INFO)
        self._busy = False
        self._prefs_say = None  # Preferences' own toast, while it is open
        self._job_rows: dict = {}
        self._selected: dict = {}  # name -> checked
        self._build()
        self.refresh()
        GLib.timeout_add(REFRESH_MS, self._auto_refresh)

    # ── layout ────────────────────────────────────────────────────────────
    def _build(self) -> None:
        for name, folder in (("open-jobs", conf.jobs_dir), ("open-trash", lambda: conf.TRASH_DIR)):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda *_a, f=folder: self._open_folder(f()))
            self.add_action(action)
        self.header = header.build(
            self,
            INFO,
            main=("New Sync Job", "list-add-symbolic", self.new_job),
            on_refresh=self.refresh,
            on_preferences=lambda: prefs.show(self),
            menu_actions=[
                ("Open Jobs Folder", "win.open-jobs"),
                ("Open Trash Folder", "win.open-trash"),
            ],
        )

        self._jobs_grp = Adw.PreferencesGroup(title="Sync Jobs")
        # act on the ticked jobs, or on all of them when none is ticked
        bulk = Gtk.Box(spacing=8)
        for label, verb, css in (
            ("Start Selected", "start", "suggested-action"),
            ("Stop Selected", "stop", "destructive-action"),
        ):
            button = Gtk.Button(label=label)
            button.add_css_class(css)
            button.connect("clicked", lambda _b, v=verb: self._bulk(v))
            bulk.append(button)
        self._jobs_grp.set_header_suffix(bulk)
        page = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=24,
            margin_top=24, margin_bottom=24, margin_start=12, margin_end=12,
        )
        page.append(self._jobs_grp)
        # what Adw.PreferencesPage builds, with a wider column
        clamp = Adw.Clamp(
            child=page, maximum_size=CONTENT_WIDTH, tightening_threshold=CONTENT_WIDTH - 120
        )
        scroll = Gtk.ScrolledWindow(child=clamp, vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        empty = Adw.StatusPage(
            icon_name=INFO.app_id,
            title="No Sync Jobs Yet",
            description="A job keeps pairs of folders the same in both directions, "
            "for game saves and anything else.",
        )
        add = Gtk.Button(label="New Sync Job", halign=Gtk.Align.CENTER)
        add.add_css_class("pill")
        add.add_css_class("suggested-action")
        add.connect("clicked", lambda *_a: self.new_job())
        empty.set_child(add)

        self.stack = Gtk.Stack(vexpand=True)
        self.stack.add_named(scroll, "jobs")
        self.stack.add_named(empty, "empty")
        self.toasts = Adw.ToastOverlay(child=self.stack)
        view = Adw.ToolbarView(content=self.toasts)
        view.add_top_bar(self.header)
        self.set_content(view)

    def _open_folder(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        Gio.AppInfo.launch_default_for_uri(GLib.filename_to_uri(path, None), None)

    def toast(self, text: str) -> None:
        self.toasts.add_toast(Adw.Toast(title=GLib.markup_escape_text(text), timeout=4))

    # ── refresh — diff-based, expanders stay open ─────────────────────────
    def _auto_refresh(self) -> bool:
        if not self._busy:
            self.refresh()
        return GLib.SOURCE_CONTINUE

    def refresh(self) -> None:
        worker.run(conf.get_jobs, self._populate)

    def _populate(self, jobs: list[dict]) -> None:
        new_names = [j["name"] for j in jobs]
        for name in set(self._job_rows) - set(new_names):
            self._jobs_grp.remove(self._job_rows[name]["expander"])
            del self._job_rows[name]
        for j in jobs:
            if j["name"] in self._job_rows:
                self._update_job_row(j)
            else:
                row = self._make_job_row(j)
                self._jobs_grp.add(row["expander"])
                self._job_rows[j["name"]] = row
        n = len(jobs)
        active = sum(1 for j in jobs if j["active"])
        self.header.kit_title.set_subtitle(
            f"{n} sync job{'s' if n != 1 else ''} · {active} running" if n else ""
        )
        self.stack.set_visible_child_name("jobs" if jobs else "empty")

    def _subtitle(self, j: dict) -> str:
        status_str, _, _ = conf.status_attrs(j)
        n = len(j["pairs"])
        local = "  ·  this device" if j["name"].endswith(f"-{conf.HOSTNAME}") else ""
        return f"{status_str}  ·  {n} pair{'s' if n != 1 else ''}{local}"

    def _make_job_row(self, j: dict) -> dict:
        status_str, icon_name, css = conf.status_attrs(j)
        expander = Adw.ExpanderRow(
            title=GLib.markup_escape_text(j["name"]), subtitle=self._subtitle(j), icon_name=icon_name
        )

        # checkbox for selective start/stop; this device's jobs pre-checked
        check = Gtk.CheckButton(tooltip_text="For Start Selected and Stop Selected")
        if j["name"] not in self._selected:
            self._selected[j["name"]] = j["name"].endswith(f"-{conf.HOSTNAME}")
        check.set_active(self._selected[j["name"]])
        check.connect(
            "toggled", lambda c, n=j["name"]: self._selected.__setitem__(n, c.get_active())
        )
        expander.add_prefix(check)

        badge = Gtk.Label(label=status_str, valign=Gtk.Align.CENTER)
        badge.add_css_class("caption")
        badge.add_css_class(css)
        expander.add_suffix(badge)

        pair_rows = self._build_pair_rows(j["pairs"])
        for pr in pair_rows:
            expander.add_row(pr)
        action_row, btn_stack = self._build_action_row(j)
        expander.add_row(action_row)

        return {
            "expander": expander, "check": check, "badge": badge, "btn_stack": btn_stack,
            "pairs": list(j["pairs"]), "pair_rows": pair_rows, "action_row": action_row,
        }

    def _build_pair_rows(self, pairs: list) -> list:
        if not pairs:
            return [
                Adw.ActionRow(
                    title="No pairs configured",
                    subtitle="Use 'Add Pair' to set sync paths",
                    selectable=False,
                )
            ]
        rows = []
        for src, dst in pairs:
            row = Adw.ActionRow(
                title=GLib.markup_escape_text(conf.shorten(src)),
                subtitle=GLib.markup_escape_text(f"↔  {conf.shorten(dst)}"),
                selectable=False,
            )
            # the list lives in the first folder; it syncs to the second
            folder = src if os.path.isdir(src) else dst
            ign = Gtk.Button(
                icon_name="action-unavailable-symbolic",
                valign=Gtk.Align.CENTER,
                tooltip_text=f"What this pair leaves out ({conf.IGNORE_NAME})",
            )
            ign.add_css_class("flat")
            ign.connect(
                "clicked",
                lambda _b, f=folder: self._edit_file(
                    os.path.join(f, conf.IGNORE_NAME), conf.IGNORE_SKELETON
                ),
            )
            row.add_suffix(ign)
            rows.append(row)
        return rows

    def _build_action_row(self, j: dict):
        action_row = Adw.ActionRow(selectable=False)
        box = Gtk.Box(
            spacing=8, valign=Gtk.Align.CENTER, hexpand=True, margin_top=6, margin_bottom=6
        )
        name, fpath = j["name"], j["file"]

        btn_stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.CROSSFADE, transition_duration=80
        )
        start_btn = Gtk.Button(label="Start")
        start_btn.add_css_class("suggested-action")
        start_btn.connect("clicked", lambda _b: self._job_action("start", name))
        stop_btn = Gtk.Button(label="Stop")
        stop_btn.add_css_class("destructive-action")
        stop_btn.connect("clicked", lambda _b: self._job_action("stop", name))
        btn_stack.add_named(start_btn, "start")
        btn_stack.add_named(stop_btn, "stop")
        btn_stack.set_visible_child_name("stop" if j["active"] else "start")
        box.append(btn_stack)

        for label, callback in (
            ("Sync Now", lambda _b: self._job_action("sync", name)),
            ("Log", lambda _b: dialogs.show_log(self, name)),
            ("Add Pair", lambda _b: self._add_pair(name, fpath)),
            ("Edit", lambda _b: self._edit_file(fpath)),
        ):
            button = Gtk.Button(label=label)
            button.connect("clicked", callback)
            box.append(button)

        box.append(Gtk.Box(hexpand=True))  # spacer

        del_btn = Gtk.Button(label="Delete")
        del_btn.add_css_class("destructive-action")
        del_btn.connect("clicked", lambda _b: self._delete_job(name, fpath))
        box.append(del_btn)

        action_row.add_suffix(box)
        return action_row, btn_stack

    def _update_job_row(self, j: dict) -> None:
        rd = self._job_rows[j["name"]]
        status_str, icon_name, css = conf.status_attrs(j)
        rd["expander"].set_subtitle(self._subtitle(j))
        rd["expander"].set_icon_name(icon_name)
        badge = rd["badge"]
        badge.set_label(status_str)
        for c in ("success", "warning", "dim-label"):
            badge.remove_css_class(c)
        badge.add_css_class(css)
        rd["btn_stack"].set_visible_child_name("stop" if j["active"] else "start")

        if list(j["pairs"]) != rd["pairs"]:
            expander = rd["expander"]
            for pr in rd["pair_rows"]:
                expander.remove(pr)
            expander.remove(rd["action_row"])
            rd["pair_rows"] = self._build_pair_rows(j["pairs"])
            for pr in rd["pair_rows"]:
                expander.add_row(pr)
            expander.add_row(rd["action_row"])
            rd["pairs"] = list(j["pairs"])

    # ── new job ───────────────────────────────────────────────────────────
    def new_job(self) -> None:
        dialog = Adw.AlertDialog(
            heading="New Sync Job", body="Its name: letters, digits, dots, hyphens, underscores."
        )
        entry = Gtk.Entry(placeholder_text="e.g. game-saves", activates_default=True)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("create", "Create")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")
        dialog.set_close_response("cancel")
        dialog.connect(
            "response", lambda _d, r: r == "create" and self._create_job(entry.get_text().strip())
        )
        dialog.present(self)

    def _create_job(self, name: str) -> None:
        if not name:
            self.toast("A job needs a name.")
            return
        if not re.match(r"^[A-Za-z0-9._-]+$", name):
            self.toast("Only letters, digits, dots, hyphens and underscores in a job's name.")
            return
        fpath = os.path.join(conf.jobs_dir(), f"{name}.job")
        if os.path.exists(fpath):
            self.toast(f"Job '{name}' already exists.")
            return
        try:
            os.makedirs(conf.jobs_dir(), exist_ok=True)
            with open(fpath, "w") as fh:
                fh.write(conf.JOB_SKELETON)
            self.toast(f"Job '{name}' created. Add pairs now.")
        except OSError as exc:
            self.toast(f"Not created: {exc}")
        self.refresh()

    # ── job actions (via the CLI — single source of behavior) ─────────────
    def _job_action(self, verb: str, name: str) -> None:
        if self._busy:
            return
        self._busy = True

        def work() -> str:
            rc, out, err = conf.run([self.cli, verb, name], timeout=120)
            return f"'{name}': {verb} done." if rc == 0 else f"{verb} failed: {err or out}"

        worker.run(work, self._action_done)

    def _action_done(self, msg: str) -> None:
        self._busy = False
        self.toast(msg)
        self.refresh()

    def _bulk(self, verb: str) -> None:
        if self._busy:
            return
        names = [n for n, v in self._selected.items() if v] or list(self._job_rows)
        if not names:
            return
        self._busy = True

        def work() -> str:
            failed = [n for n in names if conf.run([self.cli, verb, n], timeout=60)[0] != 0]
            if not failed:
                return f"{len(names)} job(s): {verb} done."
            ok = len(names) - len(failed)
            return f"{verb}: {ok} of {len(names)} done, failed: {', '.join(failed)}"

        worker.run(work, self._action_done)

    # ── add pair (two folder pickers) ─────────────────────────────────────
    def _add_pair(self, name: str, fpath: str) -> None:
        def chosen_dst(dlg, result, src: str) -> None:
            try:
                dst = dlg.select_folder_finish(result).get_path()
            except GLib.Error:
                return
            try:
                conf.add_pair(fpath, src, dst)
                self.toast(f"Pair added to '{name}'. A running job picks it up by itself.")
            except OSError as exc:
                self.toast(f"Not added: {exc}")
            self.refresh()

        def chosen_src(dlg, result) -> None:
            try:
                src = dlg.select_folder_finish(result).get_path()
            except GLib.Error:
                return
            Gtk.FileDialog(title=f"Second folder for '{name}'").select_folder(
                self, None, lambda d, r: chosen_dst(d, r, src)
            )

        Gtk.FileDialog(title=f"First folder for '{name}'").select_folder(self, None, chosen_src)

    def _edit_file(self, fpath: str, skeleton: str | None = None) -> None:
        def saved(name: str) -> None:
            self.toast(f"Saved {name}. A running job picks it up by itself.")
            self.refresh()

        dialogs.edit_file(self, fpath, skeleton, saved, self.toast)

    # ── delete job ────────────────────────────────────────────────────────
    def _delete_job(self, name: str, fpath: str) -> None:
        dlg = Adw.AlertDialog(
            heading=f"Delete '{name}'?",
            body="This stops the service and removes the job file. The synced folders stay.",
        )
        dlg.add_response("cancel", "Cancel")
        dlg.add_response("delete", "Delete")
        dlg.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dlg.set_default_response("cancel")
        dlg.set_close_response("cancel")
        dlg.connect("response", self._on_delete_response, name, fpath)
        dlg.present(self)

    def _on_delete_response(self, _dlg, response: str, name: str, fpath: str) -> None:
        if response != "delete":
            return
        conf.run([self.cli, "stop", name], timeout=30)
        try:
            os.remove(fpath)
        except FileNotFoundError:
            pass
        self._selected.pop(name, None)
        self.toast(f"Job '{name}' deleted.")
        self.refresh()
