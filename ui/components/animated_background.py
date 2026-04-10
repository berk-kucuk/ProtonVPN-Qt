"""Hareketli arka plan - Animasyonlu ışık efektleri"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QRadialGradient, QPainterPath,
    QLinearGradient
)
import random
import math


class AnimatedBackground(QWidget):
    """Hareketli ışık animasyonlu arka plan"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("animatedBackground")

        self._state = "disconnected"  # disconnected | connected | connecting
        self._state_mix = 0.0  # 0 -> disconnected palette, 1 -> connected palette

        # Işık noktaları
        self._lights = []
        self._time = 0
        self._pulse_opacity = 0.5  # BU SATIR EKLENDİ

        # 4 farklı ışık noktası oluştur
        for i in range(4):
            self._lights.append({
                'x': random.uniform(0.1, 0.9),
                'y': random.uniform(0.1, 0.9),
                'speed_x': random.uniform(0.0005, 0.002),
                'speed_y': random.uniform(0.0003, 0.0015),
                'size': random.uniform(0.3, 0.6),
                # Nötr, koyu bir base (ışığın asıl rengi state'ten gelecek)
                'base_color': QColor(38, 40, 48, 26) if i % 2 == 0 else QColor(32, 34, 42, 22),
                'phase': random.uniform(0, 2 * math.pi)
            })

        # Animasyon timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_lights)
        self._timer.start(50)  # 20 FPS

        # Blur efekti için opacity animasyonu
        self._pulse_anim = QPropertyAnimation(self, b"pulse_opacity")
        self._pulse_anim.setDuration(8000)
        # Biraz daha belirgin ama hâlâ soluk bir nefes alma efekti
        self._pulse_anim.setStartValue(0.45)
        self._pulse_anim.setEndValue(0.9)
        self._pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.start()

        # State geçiş animasyonu
        self._state_anim = QPropertyAnimation(self, b"state_mix")
        self._state_anim.setDuration(900)
        self._state_anim.setEasingCurve(QEasingCurve.InOutCubic)

    def get_pulse_opacity(self):
        return self._pulse_opacity

    def set_pulse_opacity(self, value):
        self._pulse_opacity = value
        self.update()

    pulse_opacity = Property(float, get_pulse_opacity, set_pulse_opacity)

    def get_state_mix(self):
        return self._state_mix

    def set_state_mix(self, value):
        self._state_mix = float(value)
        self.update()

    state_mix = Property(float, get_state_mix, set_state_mix)

    def set_vpn_state(self, state: str):
        state = (state or "").lower().strip()
        if state not in ("connected", "disconnected", "connecting"):
            state = "disconnected"

        if state == self._state:
            return
        self._state = state

        target = 1.0 if state == "connected" else 0.0
        self._state_anim.stop()
        self._state_anim.setStartValue(self._state_mix)
        self._state_anim.setEndValue(target)
        self._state_anim.start()

    @staticmethod
    def _lerp(a: int, b: int, t: float) -> int:
        return int(a + (b - a) * t)

    def _palette_color(self) -> QColor:
        # Soluk paletler: disconnected -> kırmızımsı, connected -> yeşilimsi.
        # Çok parlak olmasın diye alpha düşük tutuluyor.
        # connecting durumunda kırmızı/yeşil arasında orta değer + pulse zaten hareket veriyor.
        t = self._state_mix
        # disconnected: muted red
        r0, g0, b0, a0 = (165, 68, 78, 64)
        # connected: muted green
        r1, g1, b1, a1 = (78, 165, 118, 64)
        return QColor(
            self._lerp(r0, r1, t),
            self._lerp(g0, g1, t),
            self._lerp(b0, b1, t),
            self._lerp(a0, a1, t),
        )

    def _update_lights(self):
        """Işık noktalarının pozisyonlarını güncelle"""
        self._time += 0.05

        for light in self._lights:
            # Sinüzoidal hareket
            light['x'] += light['speed_x'] * math.sin(self._time * 0.5 + light['phase'])
            light['y'] += light['speed_y'] * math.cos(self._time * 0.3 + light['phase'])

            # Ekran sınırlarında bounce
            if light['x'] < 0.05 or light['x'] > 0.95:
                light['speed_x'] *= -1
                light['x'] = max(0.05, min(0.95, light['x']))
            if light['y'] < 0.05 or light['y'] > 0.95:
                light['speed_y'] *= -1
                light['y'] = max(0.05, min(0.95, light['y']))

            # Boyut değişimi
            light['size'] = 0.3 + 0.3 * math.sin(self._time * 0.8 + light['phase'])

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        width = rect.width()
        height = rect.height()

        # Ana koyu arka plan - Dark gri
        base_grad = QLinearGradient(0, 0, width, height)
        base_grad.setColorAt(0, QColor(18, 20, 28))
        base_grad.setColorAt(0.3, QColor(15, 17, 24))
        base_grad.setColorAt(0.7, QColor(12, 14, 20))
        base_grad.setColorAt(1, QColor(10, 12, 18))
        p.fillRect(rect, QBrush(base_grad))

        # Hareketli ışık noktaları
        accent = self._palette_color()
        for light in self._lights:
            x = int(light['x'] * width)
            y = int(light['y'] * height)
            size = int(light['size'] * min(width, height))

            # Radial gradient ile yumuşak ışık
            gradient = QRadialGradient(x, y, size)
            base = light['base_color']
            # base ile accent'i karıştır (renk net olsun ama parlak olmasın)
            mix = 0.85
            color = QColor(
                self._lerp(base.red(), accent.red(), mix),
                self._lerp(base.green(), accent.green(), mix),
                self._lerp(base.blue(), accent.blue(), mix),
                self._lerp(base.alpha(), accent.alpha(), mix),
            )

            # Opacity'yi pulse animasyonu ile değiştir
            alpha = int(color.alpha() * self._pulse_opacity)
            gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), alpha))
            gradient.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), alpha // 2))
            gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))

            p.setBrush(QBrush(gradient))
            p.setPen(Qt.NoPen)
            p.drawEllipse(x - size, y - size, size * 2, size * 2)

        # Vignette efekti (kenarları koyulaştır)
        vignette = QRadialGradient(width // 2, height // 2, min(width, height) // 1.5)
        vignette.setColorAt(0, QColor(0, 0, 0, 0))
        vignette.setColorAt(0.7, QColor(0, 0, 0, 30))
        vignette.setColorAt(1, QColor(0, 0, 0, 80))
        p.setBrush(QBrush(vignette))
        p.setPen(Qt.NoPen)
        p.drawRect(rect)

        p.end()

    def stop_animation(self):
        """Animasyonu durdur"""
        self._timer.stop()
        self._pulse_anim.stop()

    def start_animation(self):
        """Animasyonu başlat"""
        self._timer.start()
        self._pulse_anim.start()
