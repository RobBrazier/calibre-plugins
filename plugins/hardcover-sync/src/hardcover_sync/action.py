from calibre.gui2.actions import InterfaceAction
from qt.core import QMenu, QToolButton


class HardcoverSyncAction(InterfaceAction):
    name = "Hardcover Sync"
    # Create our top-level menu/toolbar action (text, icon_path, tooltip, keyboard shortcut)
    action_spec = (_("Hardcover"), None, None, None)
    popup_type = QToolButton.InstantPopup
    action_type = "current"

    def genesis(self):
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)
        self.qaction.setIcon(get_icons("images/hardcover-symbol.png"))
