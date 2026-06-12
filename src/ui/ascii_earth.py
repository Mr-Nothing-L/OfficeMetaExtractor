"""ASCII rotating planet widget (PyQt5)."""

import math
from typing import List, Tuple, Union

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QFontDatabase, QFontMetrics, QColor, QPainter
from PyQt5.QtWidgets import QWidget


ColorType = Union[Tuple[int, int, int], str]


def _color_to_rgb(color: ColorType) -> Tuple[int, int, int]:
    """Convert a color tuple or hex string to an (r, g, b) tuple."""
    if isinstance(color, (tuple, list)):
        return tuple(color[:3])  # type: ignore[return-value]
    c = color.lstrip("#")
    if len(c) == 3:
        r, g, b = [int(ch * 2, 16) for ch in c]
    elif len(c) == 6:
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    else:
        r, g, b = 201, 162, 39
    return r, g, b


def _color_to_rgba(color: ColorType, alpha: int) -> str:
    """Convert a color tuple or hex string to an rgba(...) string."""
    if isinstance(color, (tuple, list)):
        r, g, b = color[:3]
    else:
        c = color.lstrip("#")
        if len(c) == 3:
            r, g, b = [int(ch * 2, 16) for ch in c]
        elif len(c) == 6:
            r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        else:
            r, g, b = 201, 162, 39
    return f"rgba({r}, {g}, {b}, {max(0, min(255, alpha))})"


class AsciiPlanet(QWidget):
    """A self-contained ASCII-art rotating planet widget.

    The planet is rendered as a shaded ASCII sphere using a procedural
    surface pattern.  It is designed to sit behind other widgets: it ignores
    mouse events and paints a transparent background.

    Parameters control the apparent size, color, rotation speed, surface
    pattern and transparency.  CPU use is kept low by capping the render
    grid at 160 columns x 80 rows and using a modest timer interval.

    The planet is drawn in a custom ``paintEvent`` on a square character
    grid so the on-screen shape is always a perfect circle, regardless of
    the font's natural cell aspect ratio.
    """

    DEFAULT_MAX_COLS = 160
    DEFAULT_MAX_ROWS = 80

    def __init__(
        self,
        parent=None,
        radius: float = 0.35,
        color: ColorType = (201, 162, 39),
        speed: float = 0.06,
        pattern_seed: int = 0,
        alpha: int = 65,
        interval_ms: int = 100,
    ):
        super().__init__(parent)
        self._radius = max(0.05, min(0.95, radius))
        self._color = color
        self._alpha = max(0, min(255, alpha))
        self.angle = 0.0
        self.speed = speed
        self.pattern_seed = pattern_seed
        self._interval_ms = max(16, interval_ms)

        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # Cached render output: list of strings and the square grid size.
        self._grid: List[str] = []
        self._grid_size = 0

        # Logical resolution of the surface map.
        self.render_w = 120
        self.render_h = 120
        self._surface_mask: List[List[bool]] = self._generate_surface_mask()
        self._apply_style()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(self._interval_ms)

    # ------------------------------------------------------------------
    # Public configuration
    # ------------------------------------------------------------------
    def set_alpha(self, alpha: int):
        """Set text alpha (0-255) for watermark effect."""
        self._alpha = max(0, min(255, alpha))
        self._apply_style()

    def set_color(self, color: ColorType):
        """Set planet color as an (r, g, b) tuple or hex string."""
        self._color = color
        self._apply_style()

    def set_speed(self, speed: float):
        """Set rotation speed (radians per tick)."""
        self.speed = speed

    def set_radius(self, radius: float):
        """Set apparent radius as a fraction of the smaller widget dimension."""
        self._radius = max(0.05, min(0.95, radius))
        self._tick()

    def set_pattern_seed(self, seed: int):
        """Regenerate the surface pattern with a new seed."""
        self.pattern_seed = seed
        self._surface_mask = self._generate_surface_mask()
        self._tick()

    def set_interval(self, ms: int):
        """Set the refresh interval in milliseconds."""
        self._interval_ms = max(16, ms)
        was_active = self._timer.isActive()
        self._timer.stop()
        self._timer.setInterval(self._interval_ms)
        if was_active:
            self._timer.start()

    def pause(self):
        """Pause the animation."""
        self._timer.stop()

    def resume(self):
        """Resume the animation."""
        if not self._timer.isActive():
            self._timer.start(self._interval_ms)

    def is_animating(self) -> bool:
        """Return True if the planet's rotation timer is running."""
        return self._timer.isActive()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _apply_style(self):
        r, g, b = _color_to_rgb(self._color)
        self._paint_color = QColor(r, g, b, self._alpha)
        self.setStyleSheet("background-color: transparent;")

    def _hash(self, x: float, y: float, salt: float) -> float:
        """Cheap deterministic hash in [-1, 1]."""
        v = math.sin(x * 12.9898 + y * 78.233 + salt * 43.12) * 43758.5453
        return v - math.floor(v)

    def _generate_surface_mask(self) -> List[List[bool]]:
        """Create a procedural planet surface mask from pattern_seed."""
        seed = self.pattern_seed
        mask = []
        for y in range(self.render_h):
            row = []
            lat_eq = (y / (self.render_h - 1)) * math.pi - math.pi / 2
            for x in range(self.render_w):
                lon = (x / (self.render_w - 1)) * 2 * math.pi

                # Offset phases by the seed so each planet looks distinct.
                val = (
                    math.sin(lon * 2 + seed * 0.5) * math.cos(lat_eq * 2)
                    + math.sin(lon * 3 + 1.0 + seed) * math.cos(lat_eq * 3) * 0.5
                    + math.sin(lon * 5 + seed * 1.3) * math.cos(lat_eq * 5) * 0.3
                    + math.cos(lat_eq * 6 + seed * 0.7) * 0.2
                    + (self._hash(lon, lat_eq, seed) - 0.5) * 0.25
                )
                row.append(val > 0.25)
            mask.append(row)
        return mask

    def _tick(self):
        self.angle = (self.angle + self.speed) % (2 * math.pi)
        self._render()
        self.update()

    def _render(self):
        """Render the ASCII sphere into a square character grid.

        The grid is stored in ``self._grid`` and drawn by ``paintEvent``
        using square cells.  This keeps the on-screen planet perfectly
        circular even when the chosen monospace font has non-square cells.
        """
        widget_w = max(1, self.width())
        widget_h = max(1, self.height())

        fm = QFontMetrics(self.font())
        cell_w = max(1.0, fm.averageCharWidth())
        cell_h = max(1.0, fm.height())

        # Use a square logical cell size so cols and rows map to equal
        # physical distances in paintEvent.
        cell = max(cell_w, cell_h)

        max_grid_w = int(widget_w / cell)
        max_grid_h = int(widget_h / cell)
        grid = min(max_grid_w, max_grid_h)
        grid = max(12, min(self.DEFAULT_MAX_COLS, grid))
        grid -= grid % 2

        cols = rows = grid
        cx = cy = (grid - 1) / 2.0
        R = grid * self._radius

        shade_chars = " ·░▒▓█"
        lines: List[str] = []

        for row in range(rows):
            line = []
            dy = row - cy

            for col in range(cols):
                dx = col - cx
                d2 = dx * dx + dy * dy

                if d2 > R * R:
                    # Sparse stars outside the sphere.
                    if (row * 37 + col * 17 + self.pattern_seed) % 61 == 0 and ((row + col) % 7) == 0:
                        line.append(".")
                    else:
                        line.append(" ")
                    continue

                dz = math.sqrt(1.0 - d2 / (R * R))
                nx, ny, nz = dx / R, dy / R, dz

                # Lighting from upper-left front.
                lx, ly, lz = -0.5, -0.4, 1.0
                llen = math.sqrt(lx * lx + ly * ly + lz * lz)
                lx, ly, lz = lx / llen, ly / llen, lz / llen
                lit = nx * lx + ny * ly + nz * lz

                if abs(nx) < 1e-6 and abs(nz) < 1e-6:
                    is_land = False
                else:
                    u = math.atan2(nx, nz) + self.angle
                    v = math.asin(max(-1.0, min(1.0, ny)))
                    mx = int(((u % (2 * math.pi)) / (2 * math.pi)) * self.render_w) % self.render_w
                    my = int(((v + math.pi / 2) / math.pi) * self.render_h) % self.render_h
                    is_land = self._surface_mask[my][mx]

                base = 0.5 if is_land else 0.1
                intensity = base + lit * 0.5
                intensity = max(0.0, min(0.99, intensity))
                idx = int(intensity * (len(shade_chars) - 1))
                line.append(shade_chars[idx])

            lines.append("".join(line))

        self._grid = lines
        self._grid_size = grid

    def resizeEvent(self, event):
        """Pick a font size so each character fits in a square cell."""
        super().resizeEvent(event)
        widget_size = max(1, min(self.width(), self.height()))
        # Aim for a moderate grid density; the exact size is recalculated
        # in _render() based on the resulting font metrics.
        target_px = max(5, min(22, int(widget_size / 60.0)))

        if "Courier New" in QFontDatabase().families():
            font = QFont("Courier New")
        else:
            font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setBold(True)
        font.setPixelSize(target_px)
        self.setFont(font)
        self._tick()

    def paintEvent(self, event):
        """Draw the cached ASCII grid with square cells.

        Each logical cell is rendered as a square of the same on-screen
        size, which guarantees the sphere is a perfect circle regardless
        of the font's natural aspect ratio.
        """
        if not self._grid or self._grid_size <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(self._paint_color)
        painter.setFont(self.font())

        grid = self._grid_size
        widget_w = self.width()
        widget_h = self.height()
        cell_size = min(widget_w, widget_h) / grid

        # Center the square grid in the (already square) widget.
        offset_x = (widget_w - grid * cell_size) / 2.0
        offset_y = (widget_h - grid * cell_size) / 2.0

        # Align cells to integer pixels to keep the grid crisp.
        cell_size_i = int(cell_size)
        offset_x_i = int(offset_x)
        offset_y_i = int(offset_y)

        flags = Qt.AlignCenter
        for row, line in enumerate(self._grid):
            y = offset_y_i + row * cell_size_i
            for col, ch in enumerate(line):
                if ch == " ":
                    continue
                x = offset_x_i + col * cell_size_i
                painter.drawText(x, y, cell_size_i, cell_size_i, flags, ch)

        painter.end()


class AsciiEarth(AsciiPlanet):
    """Backward-compatible alias for the original gold ASCII earth widget."""

    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            radius=0.45,
            color=(255, 215, 0),
            speed=0.08,
            pattern_seed=0,
            alpha=65,
            interval_ms=60,
        )
