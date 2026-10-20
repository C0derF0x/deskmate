
from pynput import keyboard
from PySide6.QtCore import QObject, Signal


class HotkeyListener(QObject):
    activated = Signal()

    def __init__(self):
        super().__init__()

        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+<space>': self._on_hotkey
        })

    def _on_hotkey(self):
        self.activated.emit()

    def start(self):
        self.listener.start()

    def stop(self):
        if self.listener.is_alive():
            self.listener.stop()
