from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import QObject, QThread, Signal, Qt

from .styles import STYLESHEET
from .widgets import MessageBubble, MessageInput, TypingIndicator
from ai.client import get_response
from core.system import format_system_info


class AIWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, history):
        super().__init__()
        self.history = history

    def run(self):
        try:
            response = get_response(self.history)
            self.finished.emit(response)

        except Exception as e:
            self.error.emit(str(e))


class AssistantWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Deskmate")
        self.resize(700, 500)
        self.setStyleSheet(STYLESHEET)

        self.thread = None
        self.worker = None

        # Conversation history
        self.conversation_history = []

        self.setup_ui()

    def setup_ui(self):

        # =========================
        # Main layout
        # =========================

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)

        # =========================
        # Header
        # =========================

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Title + subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(3)

        title = QLabel("✦  Deskmate")
        title.setObjectName("title")

        subtitle = QLabel("Your intelligent PC companion")
        subtitle.setObjectName("subtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        # New Chat button
        self.new_chat_button = QPushButton("＋ New Chat")
        self.new_chat_button.setObjectName("newChatButton")
        self.new_chat_button.setFixedHeight(38)
        self.new_chat_button.setFixedWidth(115)

        self.new_chat_button.clicked.connect(self.new_chat)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.new_chat_button)

        # =========================
        # Chat scroll area
        # =========================

        self.chat_scroll = QScrollArea()

        self.chat_scroll.setWidgetResizable(True)

        self.chat_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.chat_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # Container for messages
        self.chat_container = QWidget()

        self.chat_layout = QVBoxLayout()

        self.chat_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        self.chat_layout.setSpacing(12)

        # Keep messages at the top
        self.chat_layout.addStretch()

        self.chat_container.setLayout(self.chat_layout)

        self.chat_scroll.setWidget(self.chat_container)

        # =========================
        # Input area
        # =========================

        self.input_box = MessageInput()

        self.input_box.setPlaceholderText(
            "Ask me anything..."
        )

        self.input_box.setFixedHeight(70)

        # Enter = send
        self.input_box.send_requested.connect(
            self.send_message
        )

        # Send button
        self.send_button = QPushButton("Send")

        self.send_button.setFixedWidth(90)
        self.send_button.setFixedHeight(45)

        self.send_button.clicked.connect(
            self.send_message
        )

        # Input + button
        input_layout = QHBoxLayout()

        input_layout.addWidget(
            self.input_box
        )

        input_layout.addWidget(
            self.send_button
        )

        # =========================
        # Add everything
        # =========================

        main_layout.addLayout(
            header_layout
        )

        main_layout.addWidget(
            self.chat_scroll
        )

        main_layout.addLayout(
            input_layout
        )

        self.setLayout(main_layout)

    # =========================
    # Add message
    # =========================

    def add_message(self, message, is_user):

        bubble = MessageBubble(
            message,
            is_user
        )

        # Make sure the bubble gets enough space
        bubble.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )

        # Create row
        row = QHBoxLayout()

        row.setContentsMargins(
            0,
            0,
            0,
            0
        )

        if is_user:

            # User → right
            row.addStretch()
            row.addWidget(bubble)

        else:

            # Assistant → left
            row.addWidget(bubble)
            row.addStretch()

        # Container for row
        container = QWidget()

        container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        container.setLayout(row)

        # Insert before final stretch
        self.chat_layout.insertWidget(
            self.chat_layout.count() - 1,
            container
        )

        # Force layout update
        self.chat_container.adjustSize()

        # Scroll to bottom
        self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        )

    # =========================
    # Send message
    # =========================

    def send_message(self):

        message = self.input_box.toPlainText().strip()

        if not message:
            return

        if message.lower() in [
            "system info",
            "system information",
            "pc info"
        ]:

            self.add_message(
                message,
                True
            )

            response = format_system_info()

            self.add_message(
                response,
                False
            )

            self.input_box.clear()
            self.input_box.setFocus()

            return

        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "parts": [
                {
                    "text": message
                }
            ],
        })

        # Add user message to GUI
        self.add_message(
            message,
            True
        )

        # Clear input
        self.input_box.clear()

        # Disable Send while AI is working
        self.send_button.setEnabled(False)

        # =========================
        # Typing indicator
        # =========================

        self.thinking_bubble = TypingIndicator()

        self.chat_layout.insertWidget(
            self.chat_layout.count() - 1,
            self.thinking_bubble
        )

        # =========================
        # Create worker thread
        # =========================

        self.thread = QThread()

        # Give worker a copy of history
        history_copy = self.conversation_history.copy()

        self.worker = AIWorker(
            history_copy
        )

        self.worker.moveToThread(
            self.thread
        )

        # Start worker
        self.thread.started.connect(
            self.worker.run
        )

        # Handle result
        self.worker.finished.connect(
            self.handle_response
        )

        self.worker.error.connect(
            self.handle_error
        )

        # Stop thread
        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.error.connect(
            self.thread.quit
        )

        # Clean up worker
        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.worker.error.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        # Start thread
        self.thread.start()

    # =========================
    # AI response
    # =========================

    def handle_response(self, response):

        # Stop typing animation
        self.thinking_bubble.stop()

        # Remove typing indicator
        self.chat_layout.removeWidget(
            self.thinking_bubble
        )

        self.thinking_bubble.deleteLater()

        # Add response to GUI
        self.add_message(
            response,
            False
        )

        # Save response to conversation
        self.conversation_history.append({
            "role": "model",
            "parts": [
                {
                    "text": response
                }
            ],
        })

        # Re-enable Send
        self.send_button.setEnabled(True)

        # Return focus to input
        self.input_box.setFocus()

    # =========================
    # Error handling
    # =========================

    def handle_error(self, error):

        # Stop typing animation
        self.thinking_bubble.stop()

        # Remove typing indicator
        self.chat_layout.removeWidget(
            self.thinking_bubble
        )

        self.thinking_bubble.deleteLater()

        # Show error
        self.add_message(
            f"Sorry, something went wrong:\n{error}",
            False
        )

        # Re-enable Send
        self.send_button.setEnabled(True)

        # Return focus to input
        self.input_box.setFocus()

    # =========================
    # New chat
    # =========================

    def new_chat(self):

        # Clear conversation history
        self.conversation_history.clear()

        # Remove all chat messages
        while self.chat_layout.count() > 1:

            item = self.chat_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        # Clear input
        self.input_box.clear()

        # Make sure Send is enabled
        self.send_button.setEnabled(True)

        # Return focus to input
        self.input_box.setFocus()