"""Syncman's dialogs: a job's log, and a text file to edit."""

from __future__ import annotations

import os

from gi.repository import Adw, Gtk

from ..core import conf


def _text_dialog(title: str, subtitle: str, text: str, *, editable: bool, width: int, height: int):
    dialog = Adw.Dialog(title=title, content_width=width, content_height=height)
    header = Adw.HeaderBar()
    header.set_title_widget(Adw.WindowTitle(title=title, subtitle=subtitle))
    view = Gtk.TextView(
        editable=editable,
        monospace=True,
        wrap_mode=Gtk.WrapMode.NONE,
        left_margin=10,
        right_margin=10,
        top_margin=8,
        bottom_margin=8,
    )
    view.get_buffer().set_text(text)
    toolbar = Adw.ToolbarView(content=Gtk.ScrolledWindow(child=view))
    toolbar.add_top_bar(header)
    dialog.set_child(toolbar)
    return dialog, header, view


def show_log(parent, name: str) -> None:
    """The last 80 lines of a job's journal."""
    _, out, err = conf.run(
        ["journalctl", "--user", "-u", f"syncjob@{name}.service", "-n", "80", "--no-pager"],
        timeout=10,
    )
    dialog, _header, _view = _text_dialog(
        f"Log — {name}", "", out or err or "(no log output)", editable=False, width=900, height=460
    )
    dialog.present(parent)


def edit_file(parent, fpath: str, skeleton: str | None, on_saved, on_error) -> None:
    """Edit a text file; with a skeleton, a missing file starts as that and is
    only created on Save. on_saved(basename) and on_error(text) report back."""
    try:
        with open(fpath) as fh:
            content = fh.read()
    except FileNotFoundError:
        if skeleton is None:
            on_error(f"Cannot read: {fpath} is missing")
            return
        content = skeleton
    except OSError as exc:
        on_error(f"Cannot read: {exc}")
        return
    dialog, header, view = _text_dialog(
        os.path.basename(fpath),
        conf.shorten(os.path.dirname(fpath), 50),
        content,
        editable=True,
        width=720,
        height=420,
    )

    def save(*_args) -> None:
        buf = view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        try:
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
            with open(fpath, "w") as fh:
                fh.write(text if text.endswith("\n") or not text else text + "\n")
        except OSError as exc:
            on_error(f"Save failed: {exc}")
        else:
            on_saved(os.path.basename(fpath))
        dialog.close()

    button = Gtk.Button(label="Save")
    button.add_css_class("suggested-action")
    button.connect("clicked", save)
    header.pack_end(button)
    dialog.present(parent)
