"""Sağ panel - Araç butonları - Blur efektli"""

import os

from PySide6.QtWidgets import QVBoxLayout, QToolButton, QSizePolicy
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

from ..components.blur_panel import BlurPanel


class ToolbarPanel(BlurPanel):
    """Sağ toolbar paneli - Blur efektli"""

    info_clicked = Signal()
    config_clicked = Signal()
    settings_section_requested = Signal(str)  # section key

    def __init__(self, parent=None, supported_settings: set[str] | None = None):
        super().__init__(parent, blur_opacity=0.75, border_alpha=25)
        self.setObjectName("toolbarPanel")
        self.setFixedWidth(90)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._supported_settings = supported_settings or set()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 24, 8, 24)
        layout.setSpacing(10)

        icon_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")

        def add_btn(key: str, label: str, icon_file: str):
            tb = QToolButton()
            tb.setText(label)
            tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            tb.setObjectName("toolBtn")
            tb.setFixedSize(72, 68)
            tb.setIcon(QIcon(os.path.join(icon_dir, icon_file)))
            # PySide6: boundedTo -> QSize (toSize() yok). Sabit ikon boyutu daha tutarlı.
            tb.setIconSize(QSize(22, 22))

            tb.setStyleSheet("""
                QToolButton#toolBtn {
                    background: rgba(255, 255, 255, 0.045);
                    color: #b8c2cc;
                    border: 1.5px solid rgba(255, 255, 255, 0.07);
                    border-radius: 14px;
                    font-size: 9px;
                    font-weight: 600;
                    font-family: 'Sora', sans-serif;
                    padding: 8px 4px;
                }
                QToolButton#toolBtn:hover {
                    background: rgba(255, 255, 255, 0.07);
                    color: #e2e8f0;
                    border: 1.5px solid rgba(255, 255, 255, 0.12);
                }
            """)

            if key == "info":
                tb.clicked.connect(self.info_clicked.emit)
            elif key == "settings":
                tb.clicked.connect(self.config_clicked.emit)
            else:
                tb.clicked.connect(lambda _=False, k=key: self.settings_section_requested.emit(k))

            layout.addWidget(tb)

        # CLI desteklemiyorsa bu butonları göstermeyelim
        if "netshield" in self._supported_settings:
            add_btn("netshield", "NetShield", "toolbar_shield.svg")
        if "kill-switch" in self._supported_settings:
            add_btn("kill-switch", "Kill Switch", "toolbar_bolt.svg")
        if "port-forwarding" in self._supported_settings:
            add_btn("port-forwarding", "Port Fwd", "toolbar_port.svg")
        if "custom-dns" in self._supported_settings:
            add_btn("custom-dns", "DNS", "toolbar_dns.svg")

        add_btn("info", "Info", "toolbar_info.svg")
        add_btn("settings", "Settings", "toolbar_settings.svg")

        layout.addStretch()
