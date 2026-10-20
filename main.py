import sys

from PySide6.QtWidgets import QApplication
from gui.window import AssistantWindow
from core.hotkey import HotkeyListener


def main():
    app = QApplication(sys.argv)

    window = AssistantWindow()
    window.show()

    hotkey = HotkeyListener()

    def toggle_window():
        if window.isVisible():
            window.hide()
        else:
            window.show()
            window.showNormal()
            window.raise_()
            window.activateWindow()

    hotkey.activated.connect(toggle_window)
    hotkey.start()

    app.aboutToQuit.connect(hotkey.stop)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
