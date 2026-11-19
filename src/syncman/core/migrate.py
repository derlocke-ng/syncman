"""Until 0.5.1 the icon choice was in syncman.conf (ICON_FILE, ICON_COLOR,
ICON_STYLE). It is in settings.json now, with the kit's other settings.
Moved once; the old lines are then removed."""

from __future__ import annotations

from ..kit.settings import Store
from . import conf

OLD = {"ICON_FILE": "kit.icon_file", "ICON_COLOR": "kit.icon_color", "ICON_STYLE": "kit.icon_style"}


def icon_settings(store: Store) -> bool:
    """True if something was moved."""
    found = {old: conf.conf_get(old, "") for old in OLD}
    if not any(found.values()):
        return False
    for old, new in OLD.items():
        if found[old]:
            store.set(new, found[old])
    conf.conf_drop(tuple(OLD))
    return True
