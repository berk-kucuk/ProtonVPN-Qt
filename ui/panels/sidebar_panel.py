"""Sol panel - Ülke listesi ve arama - Blur efektli"""

import os
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QFrame, QToolButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPainterPath, QBrush, QPen, QLinearGradient, QPixmap

from ..components.blur_panel import BlurPanel
from utils.constants import CACHE_FILE
from utils.flags import country_flag


class SidebarPanel(BlurPanel):
    """Sol sidebar paneli - Blur efektli, arka plan görünür"""

    country_selected = Signal(str, str)  # name, code
    refresh_requested = Signal()
    filter_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent, blur_opacity=0.75, border_alpha=25)
        self.setObjectName("sidebarPanel")
        self.setFixedWidth(320)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._cache_file = os.path.expanduser(CACHE_FILE)
        self._all_countries = []  # (name, code) listesi
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(12)

        # Logo ve auth butonu
        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)

        # PNG Logo
        self.lbl_logo = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                 "ui", "icons", "Proton_VPN_Logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            scaled_logo = logo_pixmap.scaledToHeight(32, Qt.SmoothTransformation)
            self.lbl_logo.setPixmap(scaled_logo)
        else:
            self.lbl_logo.setText("PROTON <span style='color:#8a9eb0;'>VPN</span>")
            self.lbl_logo.setTextFormat(Qt.RichText)
            self.lbl_logo.setStyleSheet("""
                font-family: 'Sora', sans-serif;
                font-size: 18px;
                font-weight: 800;
                color: #e0e0e0;
                letter-spacing: 1.5px;
            """)
        self.lbl_logo.setToolTip("Proton VPN")

        self.btn_signin = QToolButton()
        self.btn_signin.setText("Sign In")
        self.btn_signin.setObjectName("authBtn")
        self.btn_signin.setToolTip("Sign in / Sign out")
        self.btn_signin.setStyleSheet("""
            QToolButton#authBtn {
                background: rgba(100, 120, 140, 0.2);
                color: #a0b0c0;
                border: 1.5px solid rgba(100, 120, 140, 0.3);
                border-radius: 20px;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 14px;
                font-family: 'Sora', sans-serif;
            }
            QToolButton#authBtn:hover {
                background: rgba(100, 120, 140, 0.35);
                border-color: #8a9eb0;
                color: #c0d0e0;
            }
        """)

        logo_row.addWidget(self.lbl_logo)
        logo_row.addStretch()
        logo_row.addWidget(self.btn_signin)
        layout.addLayout(logo_row)
        layout.addSpacing(8)

        # Arama kartı - transparan
        search_card = QFrame()
        search_card.setObjectName("searchCard")
        search_card.setStyleSheet("""
            QFrame#searchCard {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
        """)
        search_layout = QHBoxLayout(search_card)
        search_layout.setContentsMargins(14, 8, 10, 8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search countries…")
        self.search.setObjectName("searchBox")
        self.search.setStyleSheet("""
            QLineEdit#searchBox {
                background: transparent;
                color: #d0d8e0;
                border: none;
                padding: 8px 4px;
                font-family: 'Sora', sans-serif;
                font-size: 13px;
            }
            QLineEdit#searchBox:focus {
                color: #e8f0f8;
            }
            QLineEdit#searchBox::placeholder {
                color: #7a8a98;
            }
        """)
        self.search.textChanged.connect(self._on_filter)

        self.btn_refresh = QToolButton()
        self.btn_refresh.setText("↻")
        self.btn_refresh.setObjectName("iconBtn")
        self.btn_refresh.setToolTip("Refresh all data")
        self.btn_refresh.setStyleSheet("""
            QToolButton#iconBtn {
                background: rgba(255, 255, 255, 0.06);
                color: #9aaab8;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                padding: 6px 10px;
            }
            QToolButton#iconBtn:hover {
                background: rgba(100, 120, 140, 0.25);
                color: #c0d0e0;
                border-color: rgba(100, 120, 140, 0.4);
            }
        """)
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)

        search_layout.addWidget(self.search)
        search_layout.addWidget(self.btn_refresh)
        layout.addWidget(search_card)

        # Promo banner
        promo = QFrame()
        promo.setObjectName("promoCard")
        promo.setStyleSheet("""
            QFrame#promoCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(80, 100, 120, 0.15),
                    stop:1 rgba(60, 80, 100, 0.15));
                border: 1px solid rgba(80, 100, 120, 0.2);
                border-radius: 12px;
            }
        """)
        pl = QVBoxLayout(promo)
        pl.setContentsMargins(16, 12, 16, 12)
        promo_label = QLabel("🌍  120+ countries")
        promo_label.setStyleSheet("""
            color: #aab8c8;
            font-size: 11px;
            font-family: 'Sora', sans-serif;
            font-weight: 500;
        """)
        pl.addWidget(promo_label)
        layout.addWidget(promo)

        # Ülke sayısı
        self.lbl_count = QLabel("COUNTRIES")
        self.lbl_count.setObjectName("sectionHeader")
        self.lbl_count.setStyleSheet("""
            QLabel#sectionHeader {
                color: #7a8a9a;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 2px;
                font-family: 'JetBrains Mono', monospace;
                margin-top: 8px;
            }
        """)
        layout.addWidget(self.lbl_count)

        # Ülke listesi - transparan arka plan
        self.country_list = QListWidget()
        self.country_list.setObjectName("countryList")
        self.country_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.country_list.setStyleSheet("""
            QListWidget#countryList {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget#countryList::item {
                color: #c0ccd8;
                font-family: 'Sora', sans-serif;
                font-size: 13px;
                padding: 10px 14px;
                margin: 2px 0px;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.04);
            }
            QListWidget#countryList::item:hover {
                background: rgba(100, 120, 140, 0.2);
                color: #e0e8f0;
            }
            QListWidget#countryList::item:selected {
                background: rgba(100, 120, 140, 0.35);
                color: #f0f4f8;
                font-weight: 600;
                border-left: 3px solid #8a9eb0;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                border-radius: 3px;
                margin: 4px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.12);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(140, 160, 180, 0.4);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        self.country_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.country_list)

    def _on_filter(self, text):
        """Arama filtresi"""
        self.filter_changed.emit(text)
        for i in range(1, self.country_list.count()):
            item = self.country_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _on_item_clicked(self, item):
        """Ülke seçildi"""
        data = item.data(Qt.UserRole)
        self.country_selected.emit(data["name"], data["code"])

    def update_countries(self, raw_output):
        """CLI çıktısından ülke listesini güncelle"""
        clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', raw_output)
        valid = []

        for line in clean.split('\n'):
            line = line.strip()
            if not line or "outdated" in line.lower() or line.startswith("Country") or line.startswith("-"):
                continue
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 2:
                valid.append((parts[0].strip(), parts[1].strip()))

        if valid:
            self._all_countries = valid
            self._populate_list()
            self._save_cache()

    def load_from_cache(self):
        """Cache'den ülke listesini yükle"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                valid = []
                for line in lines:
                    parts = line.strip().split('|')
                    if len(parts) == 2:
                        valid.append((parts[0], parts[1]))

                if valid:
                    self._all_countries = valid
                    self._populate_list()
                    return True
        except Exception as e:
            print(f"Cache load error: {e}")

        return False

    def _save_cache(self):
        """Ülke listesini cache'le"""
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                for name, code in self._all_countries:
                    f.write(f"{name}|{code}\n")
        except Exception as e:
            print(f"Cache save error: {e}")

    def _populate_list(self):
        """Listeyi doldur"""
        self.country_list.clear()
        self._add_fastest_item()

        for name, code in self._all_countries:
            self._add_country_item(name, code)

        self.lbl_count.setText(f"COUNTRIES  •  {len(self._all_countries)}")

    def _add_fastest_item(self):
        """En hızlı sunucu öğesini ekle"""
        item = QListWidgetItem("⚡   Fastest Server")
        item.setData(Qt.UserRole, {"name": "Fastest server", "code": "fastest"})
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.country_list.addItem(item)

    def _add_country_item(self, name, code):
        """Ülke öğesini ekle"""
        flag = country_flag(code)
        text = f"{flag}   {name}" if flag else name
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, {"name": name, "code": code})
        self.country_list.addItem(item)

    def set_loading(self, loading=True):
        """Loading durumunu göster"""
        if loading:
            self.lbl_count.setText("COUNTRIES  •  ↻ fetching…")
            self.country_list.clear()

    def get_auth_button(self):
        """Auth butonunu döndür"""
        return self.btn_signin

    def get_refresh_button(self):
        """Refresh butonunu döndür"""
        return self.btn_refresh
