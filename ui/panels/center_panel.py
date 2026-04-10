"""Orta panel - Bağlantı kontrolleri - Blur efektli"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QStackedWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QLinearGradient, QPainterPath, QPen

from ..components.shield_widget import ShieldWidget
from ..components.glow_button import GlowButton
from ..components.blur_panel import BlurPanel
from utils.flags import country_flag


class CenterPanel(BlurPanel):
    """Orta panel - Ana kontroller"""

    connect_clicked = Signal()
    disconnect_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, blur_opacity=0.7, border_alpha=20)
        self.setObjectName("centerPanel")
        self._current_country_name = None
        self._current_country_code = None
        self._connection_state = "disconnected"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 44, 40, 36)
        layout.setSpacing(0)

        # Başlık
        self.lbl_title = QLabel("Not Connected")
        self.lbl_title.setObjectName("mainTitle")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("""
            QLabel#mainTitle {
                font-family: 'Sora', sans-serif;
                font-size: 36px;
                font-weight: 800;
                color: #e0e8f0;
                letter-spacing: -0.5px;
            }
        """)

        self.lbl_subtitle = QLabel("Choose a server or connect to the fastest")
        self.lbl_subtitle.setObjectName("mainSubtitle")
        self.lbl_subtitle.setAlignment(Qt.AlignCenter)
        self.lbl_subtitle.setStyleSheet("""
            QLabel#mainSubtitle {
                font-family: 'Sora', sans-serif;
                font-size: 14px;
                color: #8a9aa8;
                font-weight: 400;
            }
        """)

        layout.addWidget(self.lbl_title)
        layout.addSpacing(6)
        layout.addWidget(self.lbl_subtitle)
        layout.addSpacing(30)

        # Kalkan widget
        shield_row = QHBoxLayout()
        shield_row.setAlignment(Qt.AlignHCenter)
        self.shield = ShieldWidget()
        shield_row.addWidget(self.shield)
        layout.addLayout(shield_row)
        layout.addSpacing(32)

        # Tek buton
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)
        btn_row.setAlignment(Qt.AlignHCenter)

        self.btn_stack = QStackedWidget()
        self.btn_stack.setFixedSize(180, 50)

        # Connect butonu
        self.btn_connect = GlowButton("⚡  Connect", "#6b8ba0")
        self.btn_connect.setFixedSize(180, 50)
        self.btn_connect.clicked.connect(self._on_connect_clicked)

        # Disconnect butonu
        self.btn_disconnect = GlowButton("✕  Disconnect", "#8b6b6b")
        self.btn_disconnect.setFixedSize(180, 50)
        self.btn_disconnect.clicked.connect(self._on_disconnect_clicked)

        self.btn_stack.addWidget(self.btn_connect)
        self.btn_stack.addWidget(self.btn_disconnect)

        btn_row.addWidget(self.btn_stack)
        layout.addLayout(btn_row)
        layout.addStretch()

        # İstatistik çubuğu - transparan
        stats = QFrame()
        stats.setObjectName("statsBar")
        stats.setStyleSheet("""
            QFrame#statsBar {
                background: rgba(20, 22, 32, 0.5);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        sg = QGridLayout(stats)
        sg.setContentsMargins(24, 18, 24, 18)
        sg.setHorizontalSpacing(40)
        sg.setVerticalSpacing(6)

        self.lbl_lock = QLabel("⚪  —")
        self.lbl_lock.setObjectName("lockLabel")
        self.lbl_lock.setStyleSheet("""
            QLabel#lockLabel {
                font-family: 'Sora', sans-serif;
                font-size: 15px;
                font-weight: 700;
                color: #9aaab8;
            }
        """)

        self.lbl_ip = self._stat_widget("VPN IP", "— . — . — . —")
        self.lbl_server = self._stat_widget("Server", "—")
        self.lbl_protocol = self._stat_widget("Protocol", "WireGuard")

        sg.addWidget(self.lbl_lock, 0, 0, 1, 3)
        sg.addWidget(self.lbl_ip, 1, 0)
        sg.addWidget(self.lbl_server, 1, 1)
        sg.addWidget(self.lbl_protocol, 1, 2)
        layout.addWidget(stats)

        self.btn_stack.setCurrentIndex(0)

    def _on_connect_clicked(self):
        self.connect_clicked.emit()

    def _on_disconnect_clicked(self):
        self.disconnect_clicked.emit()

    def _stat_widget(self, label, value):
        w = QLabel(
            f"<span style='color:#6a7a8a;font-size:10px;'>{label}</span><br>"
            f"<span style='color:#d0d8e0;font-family:JetBrains Mono;font-size:13px;'>{value}</span>"
        )
        w.setTextFormat(Qt.RichText)
        w.setAlignment(Qt.AlignLeft)
        return w

    def _update_stat(self, widget, label, value):
        widget.setText(
            f"<span style='color:#6a7a8a;font-size:10px;'>{label}</span><br>"
            f"<span style='color:#d0d8e0;font-family:JetBrains Mono;font-size:13px;'>{value}</span>"
        )

    def update_country_selection(self, name, code):
        self._current_country_name = name
        self._current_country_code = code

        if code == "fastest":
            self.lbl_title.setText("Fastest Server")
            self.lbl_subtitle.setText("Optimised for your location")
        else:
            flag = country_flag(code)
            self.lbl_title.setText(f"{flag}  {name}" if flag else name)
            self.lbl_subtitle.setText(f"Ready to connect  ·  {code}")

    def update_connection_state(self, state, details=None):
        self._connection_state = state
        self.shield.set_state(state)

        if state == "connected":
            self.btn_stack.setCurrentIndex(1)
            self.lbl_lock.setText("🟢  Protected")
            self.lbl_lock.setStyleSheet("color: #6b9a7a; font-size: 15px; font-weight: 700;")

            if details:
                self.lbl_title.setText("⚡  Connected")
                self.lbl_subtitle.setText(f"Secure connection active  ·  {details.get('server', '—')}")
                self._update_stat(self.lbl_ip, "VPN IP", details.get('ip', '—'))
                self._update_stat(self.lbl_server, "Server", details.get('server', '—'))
                self._update_stat(self.lbl_protocol, "Protocol", details.get('protocol', 'WireGuard'))

        elif state == "connecting":
            self.btn_stack.setCurrentIndex(1)
            self.lbl_title.setText("Connecting...")
            self.lbl_subtitle.setText("Establishing secure connection")
            self.lbl_lock.setText("🟡  Connecting")
            self.lbl_lock.setStyleSheet("color: #9a8a6b; font-size: 15px; font-weight: 700;")

        else:
            self.btn_stack.setCurrentIndex(0)
            self.lbl_lock.setText("🔴  Unprotected")
            self.lbl_lock.setStyleSheet("color: #9a6b6b; font-size: 15px; font-weight: 700;")

    def update_auth_state(self, is_logged_in, username=""):
        if is_logged_in:
            self.lbl_lock.setText("🟡  Logged in")
            self.lbl_lock.setStyleSheet("color: #9a8a6b; font-size: 15px; font-weight: 700;")
            self.lbl_title.setText("Ready to Connect")
            self.lbl_subtitle.setText("Choose a server to establish secure connection")
            self.btn_connect.setEnabled(True)
        else:
            self.lbl_lock.setText("🔴  Unprotected")
            self.lbl_lock.setStyleSheet("color: #9a6b6b; font-size: 15px; font-weight: 700;")
            self.lbl_title.setText("Not Connected")
            self.lbl_subtitle.setText("Sign in to use Proton VPN")
            self.btn_connect.setEnabled(False)
            self.btn_stack.setCurrentIndex(0)
            self.shield.set_state("disconnected")

        self._update_stat(self.lbl_ip, "VPN IP", "— . — . — . —")
        self._update_stat(self.lbl_server, "Server", "—")
        self._update_stat(self.lbl_protocol, "Protocol", "—")

    def get_selected_country_code(self):
        return self._current_country_code

    def get_connection_state(self):
        return self._connection_state
