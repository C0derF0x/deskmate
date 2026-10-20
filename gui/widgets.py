from PySide6.QtWidgets import QLabel, QTextEdit
from PySide6.QtCore import Qt, Signal, QTimer


class MessageBubble(QLabel):
    def __init__(self, message, is_user=False):
        super().__init__()

        self.setWordWrap(True)
        self.setMaximumWidth(450)

        if is_user:
            self.setText(message)

            self.setStyleSheet("""
                QLabel {
                    background-color: #3b82f6;
                    color: white;
                    font-size: 14px;
                    padding: 10px 14px;
                    border-radius: 14px;
                }
            """)

        else:
            # Convert the small amount of Markdown we care about
            # into HTML so QLabel can render it.
            formatted_message = message

            formatted_message = formatted_message.replace(
                "**", "<b>", 1
            )

            # Properly handle pairs of **
            parts = message.split("**")

            if len(parts) >= 3:
                formatted_message = ""

                for i, part in enumerate(parts):
                    if i % 2 == 1:
                        formatted_message += f"<b>{part}</b>"
                    else:
                        formatted_message += part

            formatted_message = formatted_message.replace(
                "\n", "<br>"
            )

            self.setText(formatted_message)

            self.setStyleSheet("""
                QLabel {
                    background-color: #252525;
                    color: #eeeeee;
                    font-size: 14px;
                    padding: 10px 14px;
                    border-radius: 14px;
                }
            """)

        self.setAlignment(Qt.AlignmentFlag.AlignLeft)


class MessageInput(QTextEdit):
    send_requested = Signal()

    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key.Key_Return
            and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.send_requested.emit()
            return

        super().keyPressEvent(event)


class TypingIndicator(QLabel):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QLabel {
                background-color: #252525;
                padding: 9px 6px;
                border-radius: 14px;
            }
        """)

        self.setFixedHeight(34)
        self.setMinimumWidth(0)
        self.setMaximumWidth(48)

        self.step = 0

        self.update_dots()

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(300)

    def update_dots(self):
        dots = []

        for i in range(3):
            if i == self.step:
                dots.append(
                    '<span style="color: #eeeeee;">●</span>'
                )
            else:
                dots.append(
                    '<span style="color: #555555;">●</span>'
                )

        self.setText(
            f"""
            <div style="
                font-size: 10px;
                white-space: nowrap;
            ">
                {dots[0]}&nbsp;&nbsp;{dots[1]}&nbsp;&nbsp;{dots[2]}
            </div>
            """
        )

    def animate(self):
        self.step = (self.step + 1) % 3
        self.update_dots()

    def stop(self):
        self.timer.stop()