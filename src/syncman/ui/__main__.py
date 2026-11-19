import signal
import sys

from .. import INFO
from ..core import migrate
from ..kit import icon
from ..kit.settings import Store

signal.signal(signal.SIGINT, signal.SIG_DFL)

if sys.argv[1:] == ["--apply-icon"]:
    # install.sh, after an update put the stock icon back. Needs no display.
    store = Store(INFO)
    migrate.icon_settings(store)
    error = icon.apply(INFO, store) if icon.is_custom(store) else None
    if error:
        print(f"syncman-panel: {error}", file=sys.stderr)
    sys.exit(1 if error else 0)

from .app import main  # noqa: E402 - gi only when a window is wanted

sys.exit(main())
