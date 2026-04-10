"""Dark gri tema - Sade stiller"""

class DarkTheme:
    """Proton VPN dark gri tema"""

    @staticmethod
    def get_stylesheet() -> str:
        return """
        /* Ana widget - Transparan arka plan */
        QWidget#root {
            background: transparent;
        }

        QStackedWidget#stackedWidget {
            background: transparent;
        }

        QWidget#contentContainer {
            background: transparent;
        }

        /* Message box stilleri */
        QMessageBox {
            background: #1a1c26;
            border-radius: 12px;
        }

        QMessageBox QLabel {
            color: #c0c8d0;
            font-family: 'Sora', sans-serif;
        }

        QMessageBox QPushButton {
            background: #5a7a8a;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
            font-family: 'Sora', sans-serif;
        }

        QMessageBox QPushButton:hover {
            background: #6a8a9a;
        }
        """
