"""VPN Ayarları Dialog Penceresi"""

import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QGroupBox,
    QTabWidget, QWidget, QFrame, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QProcess, QTimer

from utils.protonvpn_cli import ProtonVpnCli
from utils.protonvpn_features import detect_features
from utils.terminal import linux_terminal_command


class SettingsDialog(QDialog):
    """ProtonVPN Ayarları Dialog'u"""

    settings_changed = Signal()

    def __init__(self, parent=None, initial_tab: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Proton VPN - Settings")
        self.setMinimumSize(600, 500)
        self.resize(650, 550)

        self._current_settings = {}
        self._cli = ProtonVpnCli.detect()
        self._features = detect_features(self._cli.executable if self._cli else None)
        self._process = QProcess(self)
        self._process.readyReadStandardOutput.connect(self._on_config_output)
        self._process.finished.connect(self._on_config_loaded)

        self._setup_ui()
        self._apply_styles()

        try:
            self.tab_widget.setCurrentIndex(max(0, min(int(initial_tab), self.tab_widget.count() - 1)))
        except Exception:
            self.tab_widget.setCurrentIndex(0)

        QTimer.singleShot(100, self._load_current_settings)

    def _setup_ui(self):
        """UI'ı oluştur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Başlık
        title = QLabel("⚙️  VPN Configuration")
        title.setStyleSheet("""
            font-family: 'Sora', sans-serif;
            font-size: 22px;
            font-weight: 800;
            color: #d0d8e0;
        """)
        layout.addWidget(title)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background: rgba(25, 28, 40, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.05);
                color: #8a9aa8;
                font-family: 'Sora', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: rgba(100, 120, 140, 0.3);
                color: #d0d8e0;
            }
            QTabBar::tab:hover:!selected {
                background: rgba(100, 120, 140, 0.15);
            }
        """)

        # CLI desteklemiyorsa sekme ekleme
        self._tab_by_section: dict[str, int] = {}

        if self._features.supports_setting("vpn-accelerator") or self._features.supports_setting("port-forwarding"):
            self.general_tab = self._create_general_tab()
            self._tab_by_section["general"] = self.tab_widget.addTab(self.general_tab, "General")

        if self._features.supports_setting("kill-switch"):
            self.killswitch_tab = self._create_killswitch_tab()
            self._tab_by_section["kill-switch"] = self.tab_widget.addTab(self.killswitch_tab, "Kill Switch")

        if self._features.supports_setting("netshield"):
            self.netshield_tab = self._create_netshield_tab()
            self._tab_by_section["netshield"] = self.tab_widget.addTab(self.netshield_tab, "NetShield")

        if self._features.supports_setting("custom-dns"):
            self.dns_tab = self._create_dns_tab()
            self._tab_by_section["custom-dns"] = self.tab_widget.addTab(self.dns_tab, "DNS")

        if (
            self._features.supports_setting("ipv6")
            or self._features.supports_setting("moderate-nat")
            or self._features.supports_setting("anonymous-crash-reports")
        ):
            self.advanced_tab = self._create_advanced_tab()
            self._tab_by_section["advanced"] = self.tab_widget.addTab(self.advanced_tab, "Advanced")

        layout.addWidget(self.tab_widget)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("cancelBtn")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setObjectName("applyBtn")
        self.btn_apply.clicked.connect(self._apply_settings)

        self.btn_save = QPushButton("Save & Close")
        self.btn_save.setObjectName("saveBtn")
        self.btn_save.clicked.connect(self._save_settings)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _create_general_tab(self):
        """Genel ayarlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        if self._features.supports_setting("vpn-accelerator"):
            vpn_group = QGroupBox("VPN Accelerator")
            vpn_group.setStyleSheet(self._group_style())
            vpn_layout = QVBoxLayout(vpn_group)

            self.cmb_vpn_accelerator = QComboBox()
            self.cmb_vpn_accelerator.addItems(["On", "Off"])
            self.cmb_vpn_accelerator.setStyleSheet(self._combobox_style())
            vpn_layout.addWidget(self.cmb_vpn_accelerator)

            info_label = QLabel("Improves connection speeds by optimizing routing.")
            info_label.setStyleSheet("color: rgba(210,220,230,0.75); font-size: 11px; padding: 10px;")
            info_label.setWordWrap(True)
            vpn_layout.addWidget(info_label)

            layout.addWidget(vpn_group)

        if self._features.supports_setting("port-forwarding"):
            port_group = QGroupBox("Port Forwarding")
            port_group.setStyleSheet(self._group_style())
            port_layout = QVBoxLayout(port_group)

            self.chk_port_forward = QCheckBox("Enable port forwarding")
            self.chk_port_forward.setStyleSheet(self._checkbox_style())
            port_layout.addWidget(self.chk_port_forward)

            layout.addWidget(port_group)
        layout.addStretch()

        return widget

    def _create_killswitch_tab(self):
        """Kill Switch ayarları sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        ks_group = QGroupBox("Kill Switch Settings")
        ks_group.setStyleSheet(self._group_style())
        ks_layout = QVBoxLayout(ks_group)

        self.cmb_killswitch = QComboBox()
        self.cmb_killswitch.addItems(["Off", "Standard", "Permanent"])
        self.cmb_killswitch.setStyleSheet(self._combobox_style())
        ks_layout.addWidget(self.cmb_killswitch)

        info_label = QLabel(
            "⚠️  Kill Switch blocks all internet traffic if VPN disconnects.\n"
            "• Standard: Blocks traffic when VPN disconnects unexpectedly\n"
            "• Permanent: Always blocks traffic without VPN connection"
        )
        info_label.setStyleSheet("color: #8a9aa8; font-size: 11px; padding: 10px;")
        info_label.setWordWrap(True)
        ks_layout.addWidget(info_label)

        layout.addWidget(ks_group)
        layout.addStretch()

        return widget

    def _create_netshield_tab(self):
        """NetShield ayarları sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        ns_group = QGroupBox("NetShield - Ad-blocker")
        ns_group.setStyleSheet(self._group_style())
        ns_layout = QVBoxLayout(ns_group)

        self.cmb_netshield = QComboBox()
        self.cmb_netshield.addItems([
            "Off",
            "Block malware only",
            "Block malware, ads & trackers"
        ])
        self.cmb_netshield.setStyleSheet(self._combobox_style())
        ns_layout.addWidget(self.cmb_netshield)

        info_label = QLabel(
            "🛡️  NetShield protects you from online threats:\n"
            "• Level 1: Block malware and phishing sites\n"
            "• Level 2: Block malware, ads, and trackers"
        )
        info_label.setStyleSheet("color: #8a9aa8; font-size: 11px; padding: 10px;")
        info_label.setWordWrap(True)
        ns_layout.addWidget(info_label)

        layout.addWidget(ns_group)
        layout.addStretch()

        return widget

    def _create_dns_tab(self):
        """DNS ayarları sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        dns_group = QGroupBox("Custom DNS Settings")
        dns_group.setStyleSheet(self._group_style())
        dns_layout = QVBoxLayout(dns_group)

        self.chk_custom_dns = QCheckBox("Use Custom DNS Servers")
        self.chk_custom_dns.setStyleSheet(self._checkbox_style())
        dns_layout.addWidget(self.chk_custom_dns)

        dns_input_layout = QHBoxLayout()
        dns_input_layout.addWidget(QLabel("Primary DNS:"))
        self.txt_primary_dns = QLineEdit()
        self.txt_primary_dns.setPlaceholderText("1.1.1.1")
        self.txt_primary_dns.setStyleSheet(self._input_style())
        dns_input_layout.addWidget(self.txt_primary_dns)
        dns_layout.addLayout(dns_input_layout)

        dns_input_layout2 = QHBoxLayout()
        dns_input_layout2.addWidget(QLabel("Secondary DNS:"))
        self.txt_secondary_dns = QLineEdit()
        self.txt_secondary_dns.setPlaceholderText("8.8.8.8")
        self.txt_secondary_dns.setStyleSheet(self._input_style())
        dns_input_layout2.addWidget(self.txt_secondary_dns)
        dns_layout.addLayout(dns_input_layout2)

        info_label = QLabel(
            "🌐 Popular DNS providers:\n"
            "• Cloudflare: 1.1.1.1, 1.0.0.1\n"
            "• Google: 8.8.8.8, 8.8.4.4\n"
            "• Quad9: 9.9.9.9, 149.112.112.112"
        )
        info_label.setStyleSheet("color: #8a9aa8; font-size: 11px; padding: 10px;")
        info_label.setWordWrap(True)
        dns_layout.addWidget(info_label)

        layout.addWidget(dns_group)
        layout.addStretch()

        return widget

    def _create_advanced_tab(self):
        """Gelişmiş ayarlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        if self._features.supports_setting("ipv6"):
            ipv6_group = QGroupBox("IPv6 Support")
            ipv6_group.setStyleSheet(self._group_style())
            ipv6_layout = QVBoxLayout(ipv6_group)

            self.cmb_ipv6 = QComboBox()
            self.cmb_ipv6.addItems(["On", "Off"])
            self.cmb_ipv6.setStyleSheet(self._combobox_style())
            ipv6_layout.addWidget(self.cmb_ipv6)

            layout.addWidget(ipv6_group)

        if self._features.supports_setting("moderate-nat"):
            nat_group = QGroupBox("NAT Type")
            nat_group.setStyleSheet(self._group_style())
            nat_layout = QVBoxLayout(nat_group)

            self.chk_moderate_nat = QCheckBox("Enable Moderate NAT")
            self.chk_moderate_nat.setStyleSheet(self._checkbox_style())
            nat_layout.addWidget(self.chk_moderate_nat)

            layout.addWidget(nat_group)

        if self._features.supports_setting("anonymous-crash-reports"):
            crash_group = QGroupBox("Anonymous Crash Reports")
            crash_group.setStyleSheet(self._group_style())
            crash_layout = QVBoxLayout(crash_group)

            self.chk_crash_reports = QCheckBox("Send anonymous crash reports")
            self.chk_crash_reports.setStyleSheet(self._checkbox_style())
            crash_layout.addWidget(self.chk_crash_reports)

            layout.addWidget(crash_group)
        layout.addStretch()

        return widget

    def _ensure_cli(self) -> bool:
        if self._cli:
            return True
        self._cli = ProtonVpnCli.detect()
        if not self._cli:
            QMessageBox.warning(
                self,
                "ProtonVPN CLI Not Found",
                "ProtonVPN CLI was not found on PATH.\n\n"
                "Please install ProtonVPN CLI and ensure `protonvpn` works in a terminal."
            )
            return False
        return True

    def _on_config_output(self):
        """Config çıktısını oku"""
        data = self._process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self._parse_config(data)

    def _on_config_loaded(self, code, status):
        """Config yüklendi"""
        pass

    def _parse_config(self, data):
        """Config çıktısını parse et"""
        print(f"[DEBUG] Config data:\n{data}")

        data_lower = data.lower()

        # Kill Switch
        if hasattr(self, "cmb_killswitch"):
            if "kill-switch: permanent" in data_lower:
                self.cmb_killswitch.setCurrentText("Permanent")
            elif "kill-switch: standard" in data_lower or "kill-switch: on" in data_lower:
                self.cmb_killswitch.setCurrentText("Standard")
            else:
                self.cmb_killswitch.setCurrentText("Off")

        # NetShield
        if hasattr(self, "cmb_netshield"):
            if "netshield: malware-ads-trackers" in data_lower:
                self.cmb_netshield.setCurrentText("Block malware, ads & trackers")
            elif "netshield: malware" in data_lower:
                self.cmb_netshield.setCurrentText("Block malware only")
            else:
                self.cmb_netshield.setCurrentText("Off")

        # VPN Accelerator
        if hasattr(self, "cmb_vpn_accelerator"):
            if "vpn-accelerator: off" in data_lower:
                self.cmb_vpn_accelerator.setCurrentText("Off")
            else:
                self.cmb_vpn_accelerator.setCurrentText("On")

        # IPv6
        if hasattr(self, "cmb_ipv6"):
            if "ipv6: off" in data_lower:
                self.cmb_ipv6.setCurrentText("Off")
            else:
                self.cmb_ipv6.setCurrentText("On")

        # Port Forwarding
        if hasattr(self, "chk_port_forward"):
            self.chk_port_forward.setChecked("port-forwarding: on" in data_lower)

        # Moderate NAT
        if hasattr(self, "chk_moderate_nat"):
            self.chk_moderate_nat.setChecked("moderate-nat: on" in data_lower)

        # Anonymous Crash Reports
        if hasattr(self, "chk_crash_reports"):
            self.chk_crash_reports.setChecked("anonymous-crash-reports: on" in data_lower)

        # Custom DNS
        if hasattr(self, "chk_custom_dns") and hasattr(self, "txt_primary_dns") and hasattr(self, "txt_secondary_dns"):
            dns_match = re.search(r'custom-dns:\s*(.+)', data, re.I)
            if dns_match:
                dns_servers = dns_match.group(1).strip()
                if dns_servers and dns_servers.lower() not in ['none', 'disabled', 'off']:
                    self.chk_custom_dns.setChecked(True)
                    servers = dns_servers.split(',')
                    if len(servers) > 0:
                        self.txt_primary_dns.setText(servers[0].strip())
                    if len(servers) > 1:
                        self.txt_secondary_dns.setText(servers[1].strip())
                else:
                    self.chk_custom_dns.setChecked(False)

    def _save_settings(self):
        """Ayarları kaydet"""
        if self._apply_settings():
            self.accept()

    def _apply_settings(self):
        """Ayarları uygula"""
        # Bazı ProtonVPN CLI sürümlerinde "info" çıktısı güvenilir olmayabiliyor.
        # Bu yüzden burada erken auth-check yerine doğrudan komutları çalıştırıp,
        # "authentication required" gelirse kullanıcıyı sign-in'e yönlendiriyoruz.

        if not self._ensure_cli():
            return False

        commands = []

        # Kill Switch
        if hasattr(self, "cmb_killswitch"):
            ks_value = self.cmb_killswitch.currentText()
            if ks_value == "Permanent":
                commands.append(["protonvpn", "config", "set", "kill-switch", "permanent"])
            elif ks_value == "Standard":
                commands.append(["protonvpn", "config", "set", "kill-switch", "standard"])
            else:
                commands.append(["protonvpn", "config", "set", "kill-switch", "off"])

        # NetShield
        if hasattr(self, "cmb_netshield"):
            ns_value = self.cmb_netshield.currentText()
            if ns_value == "Block malware, ads & trackers":
                commands.append(["protonvpn", "config", "set", "netshield", "malware-ads-trackers"])
            elif ns_value == "Block malware only":
                commands.append(["protonvpn", "config", "set", "netshield", "malware"])
            else:
                commands.append(["protonvpn", "config", "set", "netshield", "off"])

        # VPN Accelerator
        if hasattr(self, "cmb_vpn_accelerator"):
            if self.cmb_vpn_accelerator.currentText() == "Off":
                commands.append(["protonvpn", "config", "set", "vpn-accelerator", "off"])
            else:
                commands.append(["protonvpn", "config", "set", "vpn-accelerator", "on"])

        # IPv6
        if hasattr(self, "cmb_ipv6"):
            if self.cmb_ipv6.currentText() == "Off":
                commands.append(["protonvpn", "config", "set", "ipv6", "off"])
            else:
                commands.append(["protonvpn", "config", "set", "ipv6", "on"])

        # Port Forwarding
        if hasattr(self, "chk_port_forward"):
            if self.chk_port_forward.isChecked():
                commands.append(["protonvpn", "config", "set", "port-forwarding", "on"])
            else:
                commands.append(["protonvpn", "config", "set", "port-forwarding", "off"])

        # Moderate NAT
        if hasattr(self, "chk_moderate_nat"):
            if self.chk_moderate_nat.isChecked():
                commands.append(["protonvpn", "config", "set", "moderate-nat", "on"])
            else:
                commands.append(["protonvpn", "config", "set", "moderate-nat", "off"])

        # Anonymous Crash Reports
        if hasattr(self, "chk_crash_reports"):
            if self.chk_crash_reports.isChecked():
                commands.append(["protonvpn", "config", "set", "anonymous-crash-reports", "on"])
            else:
                commands.append(["protonvpn", "config", "set", "anonymous-crash-reports", "off"])

        # Custom DNS
        if hasattr(self, "chk_custom_dns") and hasattr(self, "txt_primary_dns") and hasattr(self, "txt_secondary_dns"):
            if self.chk_custom_dns.isChecked():
                primary = self.txt_primary_dns.text().strip()
                secondary = self.txt_secondary_dns.text().strip()
                if primary:
                    dns_servers = primary
                    if secondary:
                        dns_servers += f",{secondary}"
                    commands.append(["protonvpn", "config", "set", "custom-dns", dns_servers])
            else:
                commands.append(["protonvpn", "config", "set", "custom-dns", "off"])

        # Komutları çalıştır
        success = True
        failed_commands = []

        for cmd in commands:
            print(f"[DEBUG] Running: {' '.join(cmd)}")
            process = QProcess()
            exe = self._cli.executable if cmd[0] == "protonvpn" else cmd[0]
            process.start(exe, cmd[1:])
            process.waitForFinished(5000)

            if process.exitCode() != 0:
                error = process.readAllStandardError().data().decode('utf-8', errors='replace')
                stdout = process.readAllStandardOutput().data().decode('utf-8', errors='replace')

                # Auth hatası kontrolü
                if "authentication required" in error.lower() or "sign in" in error.lower():
                    QMessageBox.warning(
                        self,
                        "Authentication Required",
                        "Please sign in first to change settings.\n\n"
                        "Click the 'Sign In' button in the main window."
                    )
                    # İsterse terminal aç
                    reply = QMessageBox.question(
                        self,
                        "Open Terminal",
                        "Open a terminal to run `protonvpn signin` now?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        import platform
                        system = platform.system()
                        if system == "Linux":
                            cmd2 = linux_terminal_command()
                            if cmd2:
                                exe2, prefix2 = cmd2
                                QProcess.startDetached(exe2, prefix2 + ["protonvpn", "signin"])
                        elif system == "Darwin":
                            QProcess.startDetached("open", ["-a", "Terminal", "protonvpn", "signin"])
                        elif system == "Windows":
                            QProcess.startDetached("cmd", ["/K", "protonvpn", "signin"])
                    return False

                print(f"[ERROR] Command failed: {' '.join(cmd)}")
                failed_commands.append(' '.join(cmd[1:4]))
                success = False
            else:
                print(f"[DEBUG] Command succeeded: {' '.join(cmd)}")

        if success:
            self.settings_changed.emit()
            QMessageBox.information(self, "Settings", "All settings applied successfully!")
        elif len(failed_commands) < len(commands):
            self.settings_changed.emit()
            QMessageBox.warning(
                self, "Partial Success",
                f"Some settings were applied successfully.\n"
                f"Failed: {', '.join(failed_commands)}"
            )
        else:
            QMessageBox.warning(
                self, "Settings Failed",
                f"Could not apply settings.\nFailed: {', '.join(failed_commands)}"
            )

        return success

    def _check_auth_status(self):
        """Auth durumunu kontrol et"""
        if not self._ensure_cli():
            return False
        process = QProcess()
        process.start(self._cli.executable, ["info"])
        process.waitForFinished(3000)

        if process.exitCode() == 0:
            data = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            # Account: 'username' veya Account: username formatını ara
            match = re.search(r'Account:\s*[\'"]?([^\s\'\"]+?)[\'\"]?(?:\s|$|\n)', data, re.I)
            if match:
                username = match.group(1).strip()
                if username and username.lower() != 'none':
                    return True

        return False

    def _load_current_settings(self):
        """Mevcut ayarları CLI'dan yükle"""
        if not self._ensure_cli():
            return

        # Auth yoksa bile (config list bazı sürümlerde çalışabilir), dene; hata olursa sessizce bırak.
        self._process.start(self._cli.executable, ["config", "list"])

    def _apply_styles(self):
        """Stilleri uygula"""
        self.setStyleSheet("""
            QDialog {
                background: rgba(16, 18, 24, 0.92);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }
            QLabel {
                color: #c4ccd6;
                font-family: 'Sora', sans-serif;
                font-size: 12px;
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #d6dee8;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px 24px;
                font-family: 'Sora', sans-serif;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.14);
            }
            QPushButton#saveBtn {
                background: rgba(255, 255, 255, 0.14);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.16);
            }
            QPushButton#saveBtn:hover {
                background: rgba(255, 255, 255, 0.18);
            }
            QPushButton#applyBtn {
                background: rgba(255, 255, 255, 0.14);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.16);
            }
            QPushButton#applyBtn:hover {
                background: rgba(255, 255, 255, 0.18);
            }
        """)

    def _group_style(self):
        return """
            QGroupBox {
                color: #c0ccd8;
                font-family: 'Sora', sans-serif;
                font-size: 13px;
                font-weight: bold;
                border: 1.5px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
        """

    def _checkbox_style(self):
        return """
            QCheckBox {
                color: #b0bcc8;
                font-family: 'Sora', sans-serif;
                font-size: 12px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 1.5px solid rgba(255, 255, 255, 0.2);
                background: rgba(255, 255, 255, 0.05);
            }
            QCheckBox::indicator:checked {
                background: #5a8a7a;
                border-color: #6a9a8a;
            }
        """

    def _combobox_style(self):
        return """
            QComboBox {
                background: rgba(255, 255, 255, 0.06);
                color: #c0ccd8;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px 12px;
                font-family: 'Sora', sans-serif;
                font-size: 12px;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: rgba(100, 120, 140, 0.4);
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #8a9aa8;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: #1a1c2a;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                selection-background-color: rgba(100, 120, 140, 0.3);
                color: #c0ccd8;
            }
        """

    def _input_style(self):
        return """
            QLineEdit {
                background: rgba(255, 255, 255, 0.06);
                color: #c0ccd8;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px 12px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #5a8a7a;
            }
        """
