"""Blur efektli cam panel - Arka plan animasyonu görünür"""

from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Qt, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath
)


class BlurPanel(QFrame):
    """Blur efektli transparan panel - arka plan görünür"""

    def __init__(self, parent=None, blur_opacity=0.65, border_alpha=22):
        super().__init__(parent)
        self._blur_opacity = blur_opacity
        self._border_alpha = border_alpha
        self._hover = False
        self._hover_progress = 0.0

        # Hover animasyonu
        self._hover_anim = QPropertyAnimation(self, b"hover_progress")
        self._hover_anim.setDuration(300)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_hover_progress(self):
        return self._hover_progress

    def set_hover_progress(self, value):
        self._hover_progress = value
        self.update()

    hover_progress = Property(float, get_hover_progress, set_hover_progress)

    def enterEvent(self, event):
        self._hover = True
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        radius = 18

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # Blur efektli koyu gri arka plan - transparan
        # Daha transparan koyu gri: arka plan animasyonu blur üzerinden görünsün
        bg_alpha = int(160 * self._blur_opacity)
        bg_color = QColor(18, 20, 26, bg_alpha)
        p.fillPath(path, QBrush(bg_color))

        # Üst kısım aydınlatma (cam efekti)
        top_grad = QLinearGradient(0, 0, 0, 80)
        top_grad.setColorAt(0, QColor(255, 255, 255, 18))
        top_grad.setColorAt(0.5, QColor(255, 255, 255, 6))
        top_grad.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, QBrush(top_grad))

        # Hover efekti - kenar parlaması
        if self._hover_progress > 0:
            hover_alpha = int(18 * self._hover_progress)
            hover_color = QColor(255, 255, 255, hover_alpha)
            p.fillPath(path, QBrush(hover_color))

        # Kenar çizgisi
        border_alpha = int(self._border_alpha + 20 * self._hover_progress)
        border_color = QColor(255, 255, 255, border_alpha)
        p.setPen(QPen(border_color, 1.2))
        p.drawPath(path)

        p.end()


class FrostedGlassPanel(QFrame):
    """Buzlu cam efekti - daha yumuşak blur"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("frostedPanel")
        self._hover = False
        self._hover_alpha = 0

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        radius = 14

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        # Buzlu cam efekti - çok transparan
        bg_grad = QLinearGradient(0, 0, rect.width(), rect.height())
        bg_grad.setColorAt(0, QColor(28, 30, 40, 160))
        bg_grad.setColorAt(0.5, QColor(24, 26, 36, 170))
        bg_grad.setColorAt(1, QColor(20, 22, 32, 160))
        p.fillPath(path, QBrush(bg_grad))

        # Işık yansıması
        shine = QLinearGradient(0, 0, 0, 70)
        shine.setColorAt(0, QColor(255, 255, 255, 20))
        shine.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, QBrush(shine))

        # Kenar
        p.setPen(QPen(QColor(255, 255, 255, 20), 1))
        p.drawPath(path)

        p.end()
