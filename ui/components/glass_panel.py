"""Cam efekti panel"""

from PySide6.QtWidgets import QFrame
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QPainterPath


class GlassPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glassPanel")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 14, 14)

        p.fillPath(path, QColor(15, 17, 28, 200))

        top_g = QLinearGradient(0, 0, 0, 60)
        top_g.setColorAt(0, QColor(255, 255, 255, 18))
        top_g.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, QBrush(top_g))

        p.setPen(QPen(QColor(255, 255, 255, 22), 1))
        p.drawPath(path)
        p.end()
