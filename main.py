#!/usr/bin/env python3
"""Proton VPN Qt GUI - Ana giriş noktası"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase

from protonvpn_app import ProtonVpnApp


def main():
    """Ana fonksiyon"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Fontları yükle (dosya yolu gerekir; aile adı ile yüklenemez).
    fonts_dir = os.path.join(os.path.dirname(__file__), "ui", "fonts")
    if os.path.isdir(fonts_dir):
        for fname in os.listdir(fonts_dir):
            if fname.lower().endswith((".ttf", ".otf")):
                QFontDatabase.addApplicationFont(os.path.join(fonts_dir, fname))

    # Ana pencereyi oluştur ve göster
    window = ProtonVpnApp()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
