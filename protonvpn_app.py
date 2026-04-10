"""Proton VPN Ana Uygulama Penceresi - Animasyonlu arka plan"""

import os
import platform
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QMessageBox, QVBoxLayout, QGridLayout
)
from PySide6.QtCore import QTimer, QProcess, Qt
from PySide6.QtGui import QIcon

from core.vpn_manager import VpnManager
from ui.panels import SidebarPanel, CenterPanel, ToolbarPanel
from ui.dialogs import SignInDialog
from ui.styles import DarkTheme
from ui.components import AnimatedBackground
from utils.terminal import linux_terminal_command
from utils.protonvpn_features import detect_features


class ProtonVpnApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proton VPN")
        self.setMinimumSize(1100, 700)
        self.resize(1160, 740)

        # Uygulama ikonunu ayarla
        self._set_app_icon()

        # State
        self._is_logged_in = False
        self._username = ""

        # Core
        self.vpn_manager = VpnManager()
        self._connect_signals()

        # UI
        self._build_ui()
        self._apply_styles()

        # Başlangıç kontrolleri
        QTimer.singleShot(150, self.vpn_manager.check_auth)
        QTimer.singleShot(500, self._load_countries)

    def _set_app_icon(self):
        """Uygulama ikonunu ayarla"""
        icon_path = os.path.join(os.path.dirname(__file__),
                                "ui", "icons", "proton-vpn-icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _connect_signals(self):
        """VpnManager sinyallerini bağla"""
        self.vpn_manager.auth_status_changed.connect(self._on_auth_changed)
        self.vpn_manager.connection_changed.connect(self._on_connection_changed)
        self.vpn_manager.command_finished.connect(self._on_command_finished)
        self.vpn_manager.error_occurred.connect(self._on_error)
        self.vpn_manager.countries_loaded.connect(self._on_countries_loaded)

    def _build_ui(self):
        """UI oluştur - Animasyonlu arka plan ile"""
        # Root widget
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        # Root layout: aynı hücreye 2 katman (deterministik stacking)
        root_layout = QGridLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Katman: Animasyonlu arka plan
        self.animated_bg = AnimatedBackground()
        # Mouse event'leri üst katmana geçsin
        self.animated_bg.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        root_layout.addWidget(self.animated_bg, 0, 0)

        # 2. Katman: İçerik widget'ı (transparan arka plan ile)
        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_container.setStyleSheet("background: transparent;")

        # İçerik layout'u
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(16)

        # Paneller
        self.sidebar = SidebarPanel()
        self.center = CenterPanel()

        features = detect_features(self.vpn_manager._cli.executable if getattr(self.vpn_manager, "_cli", None) else None)
        self.toolbar = ToolbarPanel(supported_settings=set(features.config_set_commands))

        # Panel sinyallerini bağla
        self.sidebar.country_selected.connect(self.center.update_country_selection)
        self.sidebar.refresh_requested.connect(self._refresh_all)
        self.sidebar.get_auth_button().clicked.connect(self._toggle_auth)

        self.center.connect_clicked.connect(self._do_connect)
        self.center.disconnect_clicked.connect(self._do_disconnect)

        self.toolbar.info_clicked.connect(self._run_info)
        self.toolbar.config_clicked.connect(self._run_config)
        self.toolbar.settings_section_requested.connect(self._open_settings_section)

        # Panelleri ekle
        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.center, 1)  # Stretch factor 1
        content_layout.addWidget(self.toolbar)

        root_layout.addWidget(content_container, 0, 0)
        content_container.raise_()

    def _apply_styles(self):
        """Stilleri uygula"""
        self.setStyleSheet(DarkTheme.get_stylesheet())

    def _load_countries(self):
        """Ülke listesini yükle"""
        if not self.sidebar.load_from_cache():
            self.sidebar.set_loading(True)
            self.vpn_manager.fetch_countries()

    def _on_countries_loaded(self, raw_output: str):
        self.sidebar.update_countries(raw_output)

    def _refresh_all(self):
        """Tüm verileri yenile"""
        self.vpn_manager.check_auth()
        self.sidebar.set_loading(True)
        self.vpn_manager.fetch_countries()
        if self._is_logged_in:
            QTimer.singleShot(600, self.vpn_manager.check_status)

    def _on_auth_changed(self, is_logged_in, username):
        """Auth durumu değişti"""
        self._is_logged_in = is_logged_in
        self._username = username

        btn = self.sidebar.get_auth_button()
        if is_logged_in:
            display = username[:15] + "…" if len(username) > 15 else username
            btn.setText(f"👤 {display}")
            btn.setToolTip(f"Signed in as {username}")
            QTimer.singleShot(200, self.vpn_manager.check_status)
        else:
            btn.setText("Sign In")
            btn.setToolTip("Sign in to Proton VPN")

        self.center.update_auth_state(is_logged_in, username)

    def _on_connection_changed(self, state, details):
        """Bağlantı durumu değişti"""
        self.center.update_connection_state(state, details)
        if hasattr(self, "animated_bg"):
            # Arka plan ışıklarını VPN durumuna göre renklendir
            self.animated_bg.set_vpn_state(state)

    def _on_command_finished(self, command, success, output):
        """Komut tamamlandı"""
        if command == "signout" and success:
            QMessageBox.information(self, "Signed Out", "Successfully signed out.")
        elif command == "info" and success:
            QMessageBox.information(self, "Account Info", output.strip())
        elif command == "config" and success:
            QMessageBox.information(self, "Configuration", output.strip())
        elif command == "connect":
            if success:
                # Bağlantı başarılı, status kontrolü yap
                print("[DEBUG] Connect successful, checking status...")
                QTimer.singleShot(1000, self.vpn_manager.check_status)
                QTimer.singleShot(3000, self.vpn_manager.check_status)  # Yedek kontrol
            else:
                self.center.update_connection_state("disconnected")
                msg = output.strip() or "Could not establish VPN connection."
                QMessageBox.warning(self, "Connection Failed", msg)
        elif command == "disconnect":
            # Disconnect sonrası status kontrolü
            QTimer.singleShot(500, self.vpn_manager.check_status)

    def _do_connect(self):
        """Bağlan"""
        if not self._is_logged_in:
            QMessageBox.warning(self, "Not Signed In", "Please sign in first.")
            return

        country_code = self.center.get_selected_country_code()
        self.center.update_connection_state("connecting")
        self.vpn_manager.connect_vpn(country_code)

    def _do_disconnect(self):
        """Bağlantıyı kes"""
        # UI'ı güncelle - connecting durumundan disconnect'e geç
        self.center.update_connection_state("disconnected")
        self.vpn_manager.disconnect_vpn()

    def _toggle_auth(self):
        """Auth toggle"""
        if self._is_logged_in:
            reply = QMessageBox.question(
                self, "Sign Out",
                f"Sign out from Proton VPN?\n\nUser: {self._username}",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.vpn_manager.signout()
        else:
            dlg = SignInDialog(self)
            if dlg.exec() == SignInDialog.Accepted:
                system = platform.system()
                if system == "Linux":
                    cmd = linux_terminal_command()
                    if cmd:
                        exe, prefix = cmd
                        QProcess.startDetached(exe, prefix + ["protonvpn", "signin"])
                    else:
                        QMessageBox.warning(self, "Terminal Not Found",
                                            "Could not find a terminal emulator.\n"
                                            "Please run manually:\nprotonvpn signin")
                elif system == "Darwin":
                    QProcess.startDetached("open", ["-a", "Terminal", "protonvpn", "signin"])
                elif system == "Windows":
                    QProcess.startDetached("cmd", ["/K", "protonvpn", "signin"])

                QMessageBox.information(
                    self, "Sign In Started",
                    "Terminal opened. Please complete sign in, then click Refresh (↻)."
                )

    def _run_info(self):
        """Bilgi göster"""
        if not self._is_logged_in:
            QMessageBox.warning(self, "Not Signed In", "Please sign in first.")
            return
        self.vpn_manager.get_info()

    def _run_config(self):
        """Ayarlar penceresini aç"""
        from ui.dialogs import SettingsDialog

        dlg = SettingsDialog(self, initial_tab=0)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _open_settings_tab(self, idx: int):
        from ui.dialogs import SettingsDialog

        dlg = SettingsDialog(self, initial_tab=idx)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _open_settings_section(self, section: str):
        from ui.dialogs import SettingsDialog

        section_to_tab = {
            "netshield": 2,
            "kill-switch": 1,
            "custom-dns": 3,
            "port-forwarding": 0,
        }
        dlg = SettingsDialog(self, initial_tab=section_to_tab.get(section, 0))
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _on_settings_changed(self):
        QMessageBox.information(self, "Settings Updated",
                            "VPN settings have been updated.\n"
                            "Reconnect to apply all changes.")

    def _on_error(self, message: str):
        # Tek noktadan kullanıcıya anlaşılır hata göster
        QMessageBox.warning(self, "ProtonVPN Error", message)

    def closeEvent(self, event):
        """Pencere kapanırken animasyonu durdur"""
        if hasattr(self, 'animated_bg'):
            self.animated_bg.stop_animation()
        event.accept()
