"""Modern animasyonlu kalkan widget'ı - Kilit ikonlu"""

import os
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath, QPixmap
)


class ShieldWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self._pulse_radius = 0
        self._pulse_alpha = 0
        self._ring_angle = 0
        self._state = "disconnected"
        self._glow_intensity = 0.0

        # İkon yolları
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                 "ui", "icons")
        self.disconnected_icon_path = os.path.join(icons_dir, "disconnected_lock.png")
        self.connected_icon_path = os.path.join(icons_dir, "connected_lock.png")
        self._lock_pixmap = None
        self._load_lock_icon("disconnected")

        # Pulse animasyonu
        self._pulse_anim = QPropertyAnimation(self, b"pulse_radius")
        self._pulse_anim.setDuration(2000)
        self._pulse_anim.setStartValue(0)
        self._pulse_anim.setEndValue(95)
        self._pulse_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._pulse_anim.setLoopCount(-1)

        # Glow animasyonu
        self._glow_anim = QPropertyAnimation(self, b"glow_intensity")
        self._glow_anim.setDuration(1500)
        self._glow_anim.setStartValue(0.3)
        self._glow_anim.setEndValue(1.0)
        self._glow_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._glow_anim.setLoopCount(-1)

        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick_spin)

    def _load_lock_icon(self, state):
        """Kilit ikonunu yükle"""
        icon_path = self.connected_icon_path if state == "connected" else self.disconnected_icon_path

        if icon_path and os.path.exists(icon_path):
            self._lock_pixmap = QPixmap(icon_path)
        else:
            self._lock_pixmap = None

    def _tick_spin(self):
        self._ring_angle = (self._ring_angle + 6) % 360
        self.update()

    def get_pulse_radius(self):
        return self._pulse_radius

    def set_pulse_radius(self, v):
        self._pulse_radius = v
        self._pulse_alpha = max(0, 200 - int(v * 2.0))
        self.update()

    pulse_radius = Property(int, get_pulse_radius, set_pulse_radius)

    def get_glow_intensity(self):
        return self._glow_intensity

    def set_glow_intensity(self, v):
        self._glow_intensity = v
        self.update()

    glow_intensity = Property(float, get_glow_intensity, set_glow_intensity)

    def set_state(self, state: str):
        self._state = state
        self._load_lock_icon(state)

        self._pulse_anim.stop()
        self._glow_anim.stop()
        self._spin_timer.stop()

        if state == "connected":
            self._pulse_anim.start()
            self._glow_anim.start()
        elif state == "connecting":
            self._spin_timer.start(16)
            self._glow_intensity = 0.6

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() // 2, self.height() // 2

        # Arka plan glow (connected durumunda)
        if self._state == "connected" and self._pulse_radius > 0:
            glow = QRadialGradient(cx, cy, self._pulse_radius + 20)
            glow_color = QColor(16, 185, 129) if self._state == "connected" else QColor(100, 120, 140)
            glow_color.setAlpha(int(self._pulse_alpha * self._glow_intensity))
            glow.setColorAt(0.5, glow_color)
            glow.setColorAt(0.8, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), int(self._pulse_alpha * 0.5)))
            glow.setColorAt(1.0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.NoPen)
            p.drawEllipse(
                cx - self._pulse_radius - 10, cy - self._pulse_radius - 10,
                (self._pulse_radius + 10) * 2, (self._pulse_radius + 10) * 2
            )

        # Connecting animasyonu - modern neon halka
        if self._state == "connecting":
            # Dış halka
            pen = QPen(QColor(99, 102, 241), 3)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawArc(cx-80, cy-80, 160, 160, self._ring_angle * 16, 120 * 16)

            # İç halka
            pen2 = QPen(QColor(16, 185, 129), 2.5)
            pen2.setCapStyle(Qt.RoundCap)
            p.setPen(pen2)
            p.drawArc(cx-70, cy-70, 140, 140, (self._ring_angle + 180) * 16, 90 * 16)

            # Neon glow efekti
            glow_pen = QPen(QColor(99, 102, 241, 80), 6)
            glow_pen.setCapStyle(Qt.RoundCap)
            p.setPen(glow_pen)
            p.drawArc(cx-80, cy-80, 160, 160, self._ring_angle * 16, 120 * 16)

        # Ana kalkan arka planı - gradient
        colors = {
            "disconnected": (QColor(45, 48, 65), QColor(60, 63, 85)),
            "connecting": (QColor(40, 45, 75), QColor(60, 65, 110)),
            "connected": (QColor(10, 50, 35), QColor(20, 80, 60)),
        }
        c1, c2 = colors[self._state]

        # Radial gradient ile derinlik efekti
        grad = QRadialGradient(cx - 5, cy - 10, 75)
        grad.setColorAt(0, c2.lighter(110))
        grad.setColorAt(0.7, c1)
        grad.setColorAt(1, c1.darker(120))
        p.setBrush(QBrush(grad))

        # Kenar glow
        if self._state == "connected":
            border_color = QColor(16, 185, 129, int(80 * self._glow_intensity))
        else:
            border_color = QColor(255, 255, 255, 25)
        p.setPen(QPen(border_color, 2))
        p.drawEllipse(cx - 72, cy - 72, 144, 144)

        # Kalkan rengi
        shield_color = {
            "disconnected": QColor(120, 130, 150),
            "connecting": QColor(99, 102, 241),
            "connected": QColor(16, 185, 129),
        }[self._state]

        # Kalkan çizimi
        path = QPainterPath()
        sw, sh = 56, 65
        sx, sy = cx - sw // 2, cy - sh // 2 - 4
        path.moveTo(sx + sw / 2, sy)
        path.lineTo(sx + sw, sy + sh * 0.28)
        path.quadTo(sx + sw, sy + sh * 0.72, sx + sw / 2, sy + sh)
        path.quadTo(sx, sy + sh * 0.72, sx, sy + sh * 0.28)
        path.closeSubpath()

        # Kalkan gradient
        shield_grad = QLinearGradient(sx, sy, sx + sw, sy + sh)
        if self._state == "connected":
            shield_grad.setColorAt(0, shield_color.lighter(150))
            shield_grad.setColorAt(0.5, shield_color)
            shield_grad.setColorAt(1, shield_color.darker(120))
        else:
            shield_grad.setColorAt(0, shield_color.lighter(130))
            shield_grad.setColorAt(1, shield_color)

        p.setBrush(QBrush(shield_grad))
        p.setPen(Qt.NoPen)
        p.drawPath(path)

        # Kalkan kenar çizgisi
        if self._state == "connected":
            glow_pen = QPen(QColor(16, 185, 129, int(150 * self._glow_intensity)), 1.5)
            p.setPen(glow_pen)
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)

        # Kilit ikonunu kalkanın içinde göster
        if self._lock_pixmap and not self._lock_pixmap.isNull():
            icon_size = 40
            icon_x = cx - icon_size // 2
            icon_y = cy - icon_size // 2 - 5

            # İkonu ölçekle ve çiz
            scaled_pixmap = self._lock_pixmap.scaled(
                icon_size, icon_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            p.drawPixmap(icon_x, icon_y, scaled_pixmap)
        else:
            # Fallback: Eski stil iç ikonlar
            if self._state == "connected":
                # Checkmark
                pen = QPen(QColor(255, 255, 255, 255), 4.5)
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                p.setPen(pen)
                p.drawLine(cx - 14, cy + 2, cx - 4, cy + 14)
                p.drawLine(cx - 4, cy + 14, cx + 16, cy - 10)

                # Checkmark glow
                glow_pen = QPen(QColor(16, 185, 129, 120), 8)
                glow_pen.setCapStyle(Qt.RoundCap)
                p.setPen(glow_pen)
                p.drawLine(cx - 14, cy + 2, cx - 4, cy + 14)
                p.drawLine(cx - 4, cy + 14, cx + 16, cy - 10)

            elif self._state == "disconnected":
                # X işareti
                p.setPen(QPen(QColor(255, 255, 255, 180), 3.5))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(cx - 10, cy - 14, 20, 16)
                p.setBrush(QColor(255, 255, 255, 180))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(cx - 14, cy - 4, 28, 20, 5, 5)

        p.end()
