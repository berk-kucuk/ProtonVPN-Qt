"""Parlama efektli buton"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, Property
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont


class GlowButton(QPushButton):
    def __init__(self, text, accent="#10b981", parent=None):
        super().__init__(text, parent)
        self._accent = QColor(accent)
        self._glow   = 0.0
        self._anim   = QPropertyAnimation(self, b"glow_level")
        self._anim.setDuration(200)
        self.setMinimumHeight(46)
        self.setCursor(Qt.PointingHandCursor)

    def get_glow(self):
        return self._glow

    def set_glow(self, v):
        self._glow = v
        self.update()

    glow_level = Property(float, get_glow, set_glow)

    def enterEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._glow)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self._glow)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(e)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)

        g = QLinearGradient(0, 0, 0, self.height())
        a = self._accent
        g.setColorAt(0, a.lighter(int(115 + 25 * self._glow)))
        g.setColorAt(1, a.darker(int(130 - 10 * self._glow)))
        p.setBrush(QBrush(g))

        border_alpha = int(80 + 175 * self._glow)
        p.setPen(QPen(QColor(a.red(), a.green(), a.blue(), border_alpha), 1.5))
        p.drawRoundedRect(r, 10, 10)

        p.setPen(QColor(255, 255, 255, 245))
        font = QFont("JetBrains Mono", 11, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        p.setFont(font)
        p.drawText(r, Qt.AlignCenter, self.text())
        p.end()
