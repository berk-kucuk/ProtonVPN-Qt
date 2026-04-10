"""ProtonVPN CLI yöneticisi - Tüm VPN işlemleri"""

import re
import json
import urllib.request
import urllib.error
from PySide6.QtCore import QProcess, QObject, Signal, QTimer

from utils.protonvpn_cli import ProtonVpnCli

class VpnManager(QObject):
    """ProtonVPN CLI ile iletişimi yönetir"""

    # Sinyaller
    auth_status_changed = Signal(bool, str)  # is_logged_in, username
    connection_changed = Signal(str, dict)   # state, details
    command_finished = Signal(str, bool, str)  # command, success, output
    error_occurred = Signal(str)
    countries_loaded = Signal(str)  # raw_output

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cli = ProtonVpnCli.detect()

        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self._proc.finished.connect(self._on_finished)
        self._proc.errorOccurred.connect(self._on_process_error)

        self._country_proc = QProcess(self)
        self._country_proc.readyReadStandardOutput.connect(self._on_country_output)
        self._country_proc.readyReadStandardError.connect(self._on_country_output)
        self._country_proc.finished.connect(self._on_country_finished)
        self._country_proc.errorOccurred.connect(self._on_country_error)

        self._current_command = None
        self._buffer = ""
        self._country_buffer = ""

    def check_auth(self):
        """Oturum durumunu kontrol et"""
        print("[DEBUG] Checking auth via 'protonvpn info'...")
        self._run_command("auth_check", ["info"])

    def check_status(self):
        """Bağlantı durumunu kontrol et"""
        self._run_command("status", ["status"])

    def get_info(self):
        """Hesap bilgilerini getir"""
        self._run_command("info", ["info"])

    def connect_vpn(self, country_code=None):
        """VPN bağlantısı başlat"""
        args = ["connect"]
        if country_code and country_code != "fastest":
            args.extend(["--country", country_code])
        self._run_command("connect", args)

    def disconnect_vpn(self):
        """VPN bağlantısını kes - çalışan process'i durdur"""
        # Eğer connect işlemi devam ediyorsa durdur
        if self._proc.state() == QProcess.Running and self._current_command == "connect":
            print("[DEBUG] Terminating ongoing connect process...")
            self._proc.terminate()
            if not self._proc.waitForFinished(2000):
                self._proc.kill()
                self._proc.waitForFinished(1000)

        # Disconnect komutunu çalıştır
        self._run_command("disconnect", ["disconnect"])

    def signout(self):
        """Çıkış yap"""
        self._run_command("signout", ["signout"])

    def fetch_countries(self):
        """Ülke listesini getir"""
        if not self._ensure_cli():
            return
        self._country_buffer = ""
        self._country_proc.start(self._cli.executable, ["countries", "list"])

    def get_config_list(self):
        """Konfigürasyon listesini getir"""
        self._run_command("config", ["config", "list"])

    def _run_command(self, command_name, args):
        """Komut çalıştır"""
        if not self._ensure_cli():
            self.command_finished.emit(command_name, False, "ProtonVPN CLI not found on PATH.")
            return

        if self._proc.state() == QProcess.Running:
            # Aynı komut üst üste tetikleniyorsa (özellikle auth/status timer'ları),
            # çalışan prosesi öldürmek yerine yeni isteği yok saymak daha güvenli.
            if self._current_command == command_name:
                print(f"[DEBUG] Process busy, skipping duplicate command: {command_name}")
                return

            print(f"[DEBUG] Process busy, terminating previous command: {self._current_command}")
            self._proc.terminate()
            if not self._proc.waitForFinished(2000):
                self._proc.kill()
                self._proc.waitForFinished(1000)

        self._current_command = command_name
        self._buffer = ""
        print(f"[DEBUG] Starting command: {self._cli.executable} {' '.join(args)}")
        self._proc.start(self._cli.executable, args)

    def _on_stdout(self):
        data = self._proc.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self._buffer += data

    def _on_stderr(self):
        err = self._proc.readAllStandardError().data().decode('utf-8', errors='replace')
        self._buffer += err

    def _on_finished(self, code, status):
        success = code == 0
        print(f"[DEBUG] Command finished: {self._current_command}, success: {success}, code: {code}")

        if self._current_command == "auth_check":
            self._parse_auth_response(self._buffer, success)
        elif self._current_command == "status":
            self._parse_status_response(self._buffer)
        elif self._current_command == "info":
            self.command_finished.emit("info", success, self._buffer)
        elif self._current_command == "signout":
            if success:
                self.auth_status_changed.emit(False, "")
            self.command_finished.emit("signout", success, self._buffer)
        elif self._current_command == "connect":
            self.command_finished.emit("connect", success, self._buffer)
            # Bağlantı sonrası durumu kontrol et
            if success:
                from PySide6.QtCore import QTimer
                QTimer.singleShot(500, self.check_status)
        elif self._current_command == "disconnect":
            self.command_finished.emit("disconnect", success, self._buffer)
            # Bağlantı kesme sonrası durumu kontrol et
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, self.check_status)
        elif self._current_command == "config":
            self.command_finished.emit("config", success, self._buffer)

    def _on_country_output(self):
        """Ülke listesi çıktısını işle"""
        data = self._country_proc.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self._country_buffer += data
        err = self._country_proc.readAllStandardError().data().decode('utf-8', errors='replace')
        if err:
            self._country_buffer += err

    def _on_country_finished(self, code, status):
        success = code == 0
        if success and self._country_buffer.strip():
            self.countries_loaded.emit(self._country_buffer)
        else:
            self.error_occurred.emit(self._country_buffer.strip() or "Failed to load countries.")

    def _on_country_error(self, err):
        self.error_occurred.emit(f"Country list process error: {err}")

    def _on_process_error(self, err):
        # QProcess error enum -> emit readable message
        msg = f"Process error ({self._current_command}): {err}"
        if not self._cli:
            msg = "ProtonVPN CLI not found. Install ProtonVPN CLI and ensure it's on PATH."
        self.error_occurred.emit(msg)

    def _ensure_cli(self) -> bool:
        if self._cli:
            return True
        self._cli = ProtonVpnCli.detect()
        if not self._cli:
            self.error_occurred.emit("ProtonVPN CLI not found. Install it and ensure `protonvpn` is available on PATH.")
            return False
        return True

    def get_country_buffer(self):
        """Ülke listesi buffer'ını döndür"""
        return self._country_buffer

    def is_busy(self):
        """Process meşgul mü?"""
        return self._proc.state() == QProcess.Running

    def get_current_command(self):
        """Şu anki komutu döndür"""
        return self._current_command

    def _parse_auth_response(self, data, success):
        """Auth yanıtını parse et"""
        print(f"[DEBUG] Auth check - Exit code: {success}")
        print(f"[DEBUG] Auth check - Full data:")
        print(f"[DEBUG] ========== START ==========")
        print(data)
        print(f"[DEBUG] =========== END ===========")

        username = None

        # Tüm olası formatları dene.
        # Not: Bazı durumlarda proses terminate edildiği için exit code != 0 gelebilir,
        # ama output yine de geçerli olabilir; bu yüzden success'e bağlı kalmayalım.
        # Format 1: "Account: 'berkkucuk'" veya "Account: berkkucuk"
        match = re.search(r'Account:\s*[\'"]?([^\s\'\"]+?)[\'\"]?(?:\s|$|\n)', data, re.I)
        if match:
            username = match.group(1).strip()
            if username.lower() == 'none':
                username = None
            else:
                print(f"[DEBUG] Found username via Account: {username}")

        # Format 2: "Username: berkkucuk"
        if not username:
            match = re.search(r'Username:\s*[\'"]?([^\s\'\"]+?)[\'\"]?(?:\s|$|\n)', data, re.I)
            if match:
                username = match.group(1).strip()
                if username.lower() == 'none':
                    username = None
                else:
                    print(f"[DEBUG] Found username via Username: {username}")

        # Format 3: "User: berkkucuk"
        if not username:
            match = re.search(r'User:\s*[\'"]?([^\s\'\"]+?)[\'\"]?(?:\s|$|\n)', data, re.I)
            if match:
                username = match.group(1).strip()
                if username.lower() == 'none':
                    username = None
                else:
                    print(f"[DEBUG] Found username via User: {username}")

        # Format 4: "You are logged in as: berkkucuk"
        if not username:
            match = re.search(r'logged\s*in\s*as:\s*[\'"]?([^\s\'\"]+?)[\'\"]?(?:\s|$|\n)', data, re.I)
            if match:
                username = match.group(1).strip()
                if username.lower() == 'none':
                    username = None
                else:
                    print(f"[DEBUG] Found username via logged in as: {username}")

        # Format 5: Satırda email formatında bir şey ara (@ işareti içeren)
        if not username:
            match = re.search(r'[\'"]?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[\'"]?', data)
            if match:
                username = match.group(1).strip()
                print(f"[DEBUG] Found username via email format: {username}")

        # Format 6: generic
        if not username:
            match = re.search(r'(?:Account|User|Username):\s*[\'"]?([^\s\'\"]+?)[\'\"]?(?:\s|$|\n)', data, re.I)
            if match:
                username = match.group(1).strip()
                if username.lower() != 'none':
                    print(f"[DEBUG] Found username via generic search: {username}")

        # Eğer hala bulunamadıysa, CLI'dan tekrar dene
        if not username:
            print("[DEBUG] Username not found in output, trying alternative method...")
            # Belki farklı bir komutla kontrol et
            self._check_auth_alternative()
            return

        if username:
            self.auth_status_changed.emit(True, username)
            print(f"[DEBUG] Logged in as: {username}")
        else:
            self.auth_status_changed.emit(False, "")
            print("[DEBUG] Not logged in")

    def _check_auth_alternative(self):
        """Alternatif auth kontrolü - protonvpn status ile"""
        print("[DEBUG] Trying alternative auth check via status...")

        if not self._ensure_cli():
            self.auth_status_changed.emit(False, "")
            return

        process = QProcess()
        process.start(self._cli.executable, ["status"])
        process.waitForFinished(3000)

        if process.exitCode() == 0:
            data = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            print(f"[DEBUG] Status output: {data[:300]}")

            # Status çıktısında "Logged in" veya benzeri bir şey ara
            if "connected" in data.lower() or "disconnected" in data.lower():
                # Eğer status komutu çalışıyorsa, login olunmuş demektir
                # Kullanıcı adını başka bir yerden almaya çalış
                username = self._get_username_from_other_sources()
                if username:
                    self.auth_status_changed.emit(True, username)
                    print(f"[DEBUG] Logged in as (via status): {username}")
                    return

        # Hiçbir şekilde bulunamadı
        self.auth_status_changed.emit(False, "")
        print("[DEBUG] Not logged in (alternative check)")

    def _get_username_from_other_sources(self):
        """Diğer kaynaklardan kullanıcı adını al"""
        import os
        import json

        # ProtonVPN config dosyasından okumayı dene
        config_paths = [
            os.path.expanduser("~/.config/protonvpn/user.json"),
            os.path.expanduser("~/.cache/protonvpn/session.json"),
            os.path.expanduser("~/.protonvpn/session.json")
        ]

        for path in config_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                        if 'username' in data:
                            return data['username']
                        if 'user' in data:
                            return data['user']
                        if 'email' in data:
                            return data['email']
                except:
                    pass

        return None

    def _parse_status_response(self, data):
        """Status yanıtını parse et"""
        print(f"[DEBUG] Status check - Raw data:")
        print(f"[DEBUG] ========== START ==========")
        print(data)
        print(f"[DEBUG] =========== END ===========")

        data_lower = data.lower()
        details = {}

        if "disconnected" in data_lower or "no active vpn" in data_lower or "not connected" in data_lower:
            print("[DEBUG] Status: DISCONNECTED")
            self.connection_changed.emit("disconnected", details)

        elif "connected" in data_lower:
            print("[DEBUG] Status: CONNECTED")

            # IP adresini ara - birden fazla format dene
            ip_m = None

            # Format 1: "IP: 185.159.158.18"
            ip_m = re.search(r'IP:\s*([\d\.]+)', data, re.I)

            # Format 2: "Server IP: 185.159.158.18"
            if not ip_m:
                ip_m = re.search(r'Server\s*IP:\s*([\d\.]+)', data, re.I)

            # Format 3: "VPN IP: 185.159.158.18"
            if not ip_m:
                ip_m = re.search(r'VPN\s*IP:\s*([\d\.]+)', data, re.I)

            # Format 4: "Connected to ... IP 185.159.158.18"
            if not ip_m:
                ip_m = re.search(r'connected.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', data, re.I)

            # Format 5: Satırda tek başına IP
            if not ip_m:
                ip_m = re.search(r'^[\s]*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[\s]*$', data, re.M)

            # Server adını ara
            srv_m = None

            # Format 1: "Server: CH#4"
            srv_m = re.search(r'Server:\s*([^\n\r]+)', data, re.I)

            # Format 2: "Connected to: CH#4"
            if not srv_m:
                srv_m = re.search(r'Connected\s*to:\s*([^\n\r]+)', data, re.I)

            # Format 3: "Country: Switzerland"
            if not srv_m:
                country_m = re.search(r'Country:\s*([^\n\r]+)', data, re.I)
                if country_m:
                    city_m = re.search(r'City:\s*([^\n\r]+)', data, re.I)
                    if city_m:
                        srv_m = re.search(r'Country:\s*([^\n\r]+).*City:\s*([^\n\r]+)', data, re.I)
                        if srv_m:
                            country = srv_m.group(1).strip()
                            city = srv_m.group(2).strip()
                            details['server'] = f"{country} - {city}"

            # Protokolü ara
            pro_m = None

            # Format 1: "Protocol: WireGuard"
            pro_m = re.search(r'Protocol:\s*([^\n\r]+)', data, re.I)

            # Format 2: "Using: WireGuard"
            if not pro_m:
                pro_m = re.search(r'Using:\s*([^\n\r]+)', data, re.I)

            # Format 3: "OpenVPN" veya "WireGuard" kelimelerini ara
            if not pro_m:
                if "wireguard" in data_lower:
                    details['protocol'] = "WireGuard"
                elif "openvpn" in data_lower:
                    details['protocol'] = "OpenVPN"

            # Detayları doldur
            if ip_m:
                details['ip'] = ip_m.group(1).strip()
                print(f"[DEBUG] Found IP: {details['ip']}")
            else:
                details['ip'] = "—"
                print("[DEBUG] IP not found in status output")

            if srv_m and 'server' not in details:
                details['server'] = srv_m.group(1).strip()
                print(f"[DEBUG] Found Server: {details['server']}")
            elif 'server' not in details:
                details['server'] = "—"
                print("[DEBUG] Server not found in status output")

            if pro_m and 'protocol' not in details:
                details['protocol'] = pro_m.group(1).strip()
                print(f"[DEBUG] Found Protocol: {details['protocol']}")
            elif 'protocol' not in details:
                details['protocol'] = "WireGuard"
                print("[DEBUG] Protocol not found, using default: WireGuard")

            # Eğer IP hala bulunamadıysa harici servisten dene
            if details.get('ip') == "—" or not details.get('ip'):
                print("[DEBUG] Trying to get IP from external service...")
                external_ip = self._get_ip_from_external_service()
                if external_ip:
                    details['ip'] = external_ip
                    print(f"[DEBUG] Got IP from external service: {external_ip}")
                else:
                    print("[DEBUG] Failed to get IP from external service")

            print(f"[DEBUG] Final connection details - IP: {details.get('ip')}, Server: {details.get('server')}, Protocol: {details.get('protocol')}")
            self.connection_changed.emit("connected", details)

        elif "connecting" in data_lower or "establishing" in data_lower:
            print("[DEBUG] Status: CONNECTING")
            self.connection_changed.emit("connecting", details)

        else:
            print("[DEBUG] Status: UNKNOWN - assuming disconnected")
            self.connection_changed.emit("disconnected", details)


    def _get_ip_from_external_service(self):
        """Harici servisten IP adresini al (yedek yöntem)"""
        import urllib.request
        import json

        services = [
            {
                "url": "https://api.ipify.org?format=json",
                "parser": lambda data: data.get('ip')
            },
            {
                "url": "https://ipapi.co/json/",
                "parser": lambda data: data.get('ip')
            },
            {
                "url": "https://ipinfo.io/json",
                "parser": lambda data: data.get('ip')
            },
            {
                "url": "https://api.my-ip.io/ip.json",
                "parser": lambda data: data.get('ip')
            },
            {
                "url": "https://ifconfig.me/ip",
                "parser": lambda data: data.strip() if isinstance(data, str) else None
            }
        ]

        for service in services:
            try:
                print(f"[DEBUG] Trying external IP service: {service['url']}")
                req = urllib.request.Request(
                    service['url'],
                    headers={'User-Agent': 'ProtonVPN-Qt/1.0'}
                )

                with urllib.request.urlopen(req, timeout=5) as response:
                    response_data = response.read().decode('utf-8')

                    # JSON parsing dene
                    try:
                        data = json.loads(response_data)
                        ip = service['parser'](data)
                    except json.JSONDecodeError:
                        # Plain text response
                        ip = service['parser'](response_data)

                    if ip and re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                        print(f"[DEBUG] Successfully got IP from {service['url']}: {ip}")
                        return ip

            except Exception as e:
                print(f"[DEBUG] Failed to get IP from {service['url']}: {str(e)}")
                continue

        print("[DEBUG] All external IP services failed")
        return None
