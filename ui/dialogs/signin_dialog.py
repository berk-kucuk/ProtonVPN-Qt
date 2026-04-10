"""Sign-in dialog penceresi"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt


class SignInDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Proton VPN — Sign In")
        self.setFixedSize(420, 280)
        self.setStyleSheet("""
            QDialog { background: #12131d; border-radius: 12px; }
            QLabel  { color: #e2e8f0; font-family: 'Sora', sans-serif; }
            QPushButton {
                background: #10b981; color: white; border: none;
                border-radius: 8px; padding: 12px; font-weight: bold;
                font-size: 13px; font-family: 'Sora', sans-serif;
            }
            QPushButton:hover { background: #059669; }
            QPushButton#cancel {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.12);
            }
            QPushButton#cancel:hover { background: rgba(255,255,255,0.12); }
        """)

        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(30, 30, 30, 30)

        logo = QLabel("🔒  Proton VPN")
        logo.setStyleSheet("font-size: 20px; font-weight: 800; color: #10b981;")
        sub  = QLabel("Authentication via terminal required")
        sub.setStyleSheet("color: #64748b; font-size: 12px;")

        info = QLabel("CLI security policy prevents password input from GUI.\n"
                     "Please run in terminal:\n<code>protonvpn signin &lt;username&gt;</code>")
        info.setStyleSheet("color: #94a3b8; font-size: 11px; font-family: 'JetBrains Mono';")
        info.setTextFormat(Qt.RichText)
        info.setWordWrap(True)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("cancel")
        btn_ok     = QPushButton("Open Terminal")
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)

        lay.addWidget(logo)
        lay.addWidget(sub)
        lay.addSpacing(6)
        lay.addWidget(info)
        lay.addLayout(btn_row)
