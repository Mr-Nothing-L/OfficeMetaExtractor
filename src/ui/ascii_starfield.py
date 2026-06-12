"""Background starfield hosting two orbiting, self-rotating ASCII planets."""

import math
import os
import random
from typing import List, Tuple

from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from .ascii_earth import AsciiPlanet


class AsciiStarfield(QWidget):
    """A transparent container that hosts a starfield and two ASCII planets.

    The planets travel along elliptical orbits while also rotating on their
    own axes.  Each planet widget is always kept square so the rendered sphere
    remains a perfect circle.  The widget is transparent to mouse events so
    that controls layered on top remain fully interactive.

    Animation is automatically paused when the widget is hidden or its
    top-level window is minimized, and when a reduced-motion preference is
    detected.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        self._star_seed = 2024
        self._stars: List[Tuple[float, float, int]] = []

        # Two distinct planets with different sizes, colors, speeds and seeds.
        # Each planet follows its own elliptical orbit while rotating on its
        # own axis.  Orbit parameters are fractions of the available half-width
        # / half-height (after padding) so the animation uses the full window.
        self._planets = [
            {
                "widget": AsciiPlanet(
                    parent=self,
                    radius=0.44,
                    color=(232, 192, 72),      # bright gold
                    speed=0.04,
                    pattern_seed=7,
                    alpha=135,
                    interval_ms=100,
                ),
                "size": 0.32,
                "orbit_a": 0.50,     # horizontal orbit extent
                "orbit_b": 0.40,     # vertical orbit extent
                "orbit_speed": 0.0028,
                "orbit_phase": 0.0,
                "angle": 0.0,
            },
            {
                "widget": AsciiPlanet(
                    parent=self,
                    radius=0.46,
                    color=(78, 168, 183),      # muted teal
                    speed=-0.055,
                    pattern_seed=23,
                    alpha=120,
                    interval_ms=110,
                ),
                "size": 0.78,
                "orbit_a": 0.45,
                "orbit_b": 0.35,
                "orbit_speed": -0.0020,
                "orbit_phase": math.pi,
                "angle": 0.0,
            },
        ]

        self._orbit_timer = QTimer(self)
        self._orbit_timer.timeout.connect(self._advance_orbits)
        self._orbit_timer.start(16)  # ~60 fps

        self._visibility_timer = QTimer(self)
        self._visibility_timer.timeout.connect(self._update_animation_state)
        self._visibility_timer.start(500)

        self._update_animation_state()
        self._regenerate_stars()
        self._layout_planets()

    # ------------------------------------------------------------------
    # Public control
    # ------------------------------------------------------------------
    def pause(self):
        """Pause all planetary rotation and orbit animations."""
        self._orbit_timer.stop()
        for p in self._planets:
            p["widget"].pause()

    def resume(self):
        """Resume animations unless reduced motion is preferred."""
        if self._prefer_reduced_motion():
            return
        if not self._orbit_timer.isActive():
            self._orbit_timer.start(16)
        for p in self._planets:
            p["widget"].resume()

    def is_animating(self) -> bool:
        """Return True if any planet's rotation timer is running."""
        return any(p["widget"].is_animating() for p in self._planets)

    # ------------------------------------------------------------------
    # Lifecycle overrides
    # ------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self._update_animation_state()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._update_animation_state()

    def changeEvent(self, event):
        super().changeEvent(event)
        # React to window minimize/restore state changes.
        if event.type() in (105, 99):  # WindowStateChange / ActivationChange
            self._update_animation_state()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._regenerate_stars()
        self._layout_planets()

    def paintEvent(self, event):
        """Draw a sparse field of small stars behind the planets."""
        if not self._stars:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        for x, y, alpha in self._stars:
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1))
            painter.drawPoint(QPointF(x, y))
        painter.end()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _regenerate_stars(self):
        """Regenerate a deterministic, sparse starfield for the current size."""
        rect = self.rect()
        w, h = rect.width(), rect.height()
        if w <= 10 or h <= 10:
            self._stars = []
            return

        area = w * h
        count = max(60, min(180, area // 14000))

        rng = random.Random(self._star_seed)
        stars = []
        for _ in range(count):
            x = rng.uniform(0.0, w)
            y = rng.uniform(0.0, h)
            alpha = rng.randint(30, 115)
            stars.append((x, y, alpha))
        self._stars = stars

    def _prefer_reduced_motion(self) -> bool:
        """Detect a user/system preference for reduced motion."""
        env_vars = (
            "OFFICE_META_REDUCED_MOTION",
            "QT_QPA_DISABLE_ANIMATIONS",
            "ACCESSIBILITY_REDUCED_MOTION",
            "GTK_MODULES",
        )
        for name in env_vars:
            value = os.environ.get(name, "").lower()
            if value in ("1", "true", "yes"):
                return True
        return False

    def _top_level_is_minimized(self) -> bool:
        """Check whether the top-level window is currently minimized."""
        window = self.window()
        if window is None:
            return False
        return bool(window.windowState() & Qt.WindowMinimized)

    def _should_animate(self) -> bool:
        return self.isVisible() and not self._top_level_is_minimized()

    def _update_animation_state(self):
        if self._prefer_reduced_motion() or not self._should_animate():
            self.pause()
        else:
            self.resume()

    def _layout_planets(self):
        """Position each planet along its orbit with a square widget geometry.

        The orbit centre is the widget centre and the orbit radii are derived
        from the full window dimensions (minus padding and the planet's own
        half-size) so planets can travel close to the edges without being cut
        off.  Each widget is always given a square geometry; ``AsciiPlanet``
        renders on a square character grid with a custom ``paintEvent`` so the
        on-screen planet stays a perfect circle.
        """
        rect = self.rect()
        if rect.width() <= 1 or rect.height() <= 1:
            return

        cx = rect.width() / 2.0
        cy = rect.height() / 2.0
        min_dim = min(rect.width(), rect.height())
        padding = max(16, int(min_dim * 0.02))

        for p in self._planets:
            widget = p["widget"]

            size = int(min_dim * p["size"])
            size = min(size, int(min_dim * 0.85))
            size = max(80, size)
            half = size / 2.0

            # Compute the largest ellipse that keeps the entire widget inside
            # the window, then scale it by the planet's orbit factors.
            max_a = max(0.0, cx - half - padding)
            max_b = max(0.0, cy - half - padding)

            a = max_a * p["orbit_a"]
            b = max_b * p["orbit_b"]
            theta = p["angle"] + p["orbit_phase"]

            px = cx + a * math.cos(theta)
            py = cy + b * math.sin(theta)

            widget.setGeometry(
                int(px - half),
                int(py - half),
                size,
                size,
            )

    def _advance_orbits(self):
        """Advance each planet's orbital angle and re-layout."""
        for p in self._planets:
            p["angle"] = (p["angle"] + p["orbit_speed"]) % (2 * math.pi)
        self._layout_planets()
