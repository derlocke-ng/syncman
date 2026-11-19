"""syncman's panel — the GTK window for the `syncman` command.

The command (bin/syncman) and the worker (bin/syncjob) are bash and do all
the syncing; this package is the window on top of them. Its shared parts
(header, menu, About, Preferences, icon chooser, window size) are the kit
from kiwi-template, in kit/, copied unchanged.
"""

from pathlib import Path

from .kit import AppInfo

__version__ = "0.6.0"
APP = "syncman"
APP_ID = "eu.kiwinetwork.Syncman"
NAME = "Syncman"
HOMEPAGE = "https://github.com/derlocke-ng/syncman"

# install.sh puts data/ next to the package; in a checkout it is two levels up.
_HERE = Path(__file__).resolve().parent
_DATA = next((d for d in (_HERE.parent / "data", _HERE.parent.parent / "data") if d.is_dir()), _HERE)

INFO = AppInfo(
    app=APP,
    app_id=APP_ID,
    name=NAME,
    version=__version__,
    description="Bidirectional pair-wise folder sync as systemd user services",
    homepage=HOMEPAGE,
    docs="https://kiwi-network.eu/docs/desktop/syncman/",
    glyph="cloud",
    stock_icon=_DATA / "syncman.svg",
    # Wide enough for a job's whole button row and a readable path.
    default_size=(760, 820),
    min_size=(560, 480),
)
