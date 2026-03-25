# -----------------------------------------------
# Shuraksha - Fake Light Mode Dashboard (Decoy)
# File: src/ui/fake_dashboard.py
# -----------------------------------------------

import sys
import os
import string
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QScrollArea, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

# -----------------------------------------------
# DIMENSIONS
# -----------------------------------------------
WIN_W      = 1100
WIN_H      = 720
SIDEBAR_W  = 210
TITLEBAR_H = 46
NAVBAR_H   = 48

# -----------------------------------------------
# LIGHT MODE COLOURS
# -----------------------------------------------
L_BG       = "#F5F5F7"
L_SIDEBAR  = "#EBEBED"
L_TITLEBAR = "#E8E8EA"
L_NAVBAR   = "#EEEEEF"
L_CARD     = "#FFFFFF"
L_CARD_H   = "#E8F0FE"
L_SELECTED = "#D2E3FC"
L_BORDER   = "#DADADA"
L_BORDER2  = "#C8C8CA"
L_TEXT     = "#1A1A1A"
L_TEXT2    = "#555555"
L_TEXT3    = "#888888"
L_ACCENT   = "#1A73E8"
L_ACCENT_H = "#1557B0"
L_RED      = "#D32F2F"
L_BAR_BG   = "#E0E0E0"

# -----------------------------------------------
# FILE ICONS
# -----------------------------------------------
ICON_FOLDER  = "📁"
ICON_IMAGE   = "🖼"
ICON_VIDEO   = "🎬"
ICON_AUDIO   = "🎵"
ICON_DOC     = "📄"
ICON_PDF     = "📑"
ICON_ZIP     = "🗜"
ICON_CODE    = "💻"
ICON_UNKNOWN = "📎"

EXT_ICONS = {
    '.jpg': ICON_IMAGE,  '.jpeg': ICON_IMAGE,
    '.png':ICON_IMAGE,  '.gif':ICON_IMAGE,
    '.bmp':ICON_IMAGE,  '.webp':ICON_IMAGE,
    '.mp4':ICON_VIDEO,  '.avi':ICON_VIDEO,
    '.mkv':ICON_VIDEO,  '.mov':ICON_VIDEO,
    '.mp3':ICON_AUDIO,  '.wav':ICON_AUDIO,
    '.flac':ICON_AUDIO, '.aac':ICON_AUDIO,
    '.pdf':ICON_PDF,
    '.doc':ICON_DOC,    '.docx':ICON_DOC,
    '.txt':ICON_DOC,    '.xlsx':ICON_DOC,
    '.zip':ICON_ZIP,    '.rar':ICON_ZIP,
    '.7z':ICON_ZIP,
    '.py':ICON_CODE,    '.js':ICON_CODE,
    '.html':ICON_CODE,  '.css':ICON_CODE,
}


def get_icon(path: Path) -> str:
    if path.is_dir():
        return ICON_FOLDER
    return EXT_ICONS.get(path.suffix.lower(), ICON_UNKNOWN)


def fmt_size(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024 ** 2:
        return f"{b // 1024} KB"
    elif b < 1024 ** 3:
        return f"{b // 1024 ** 2} MB"
    else:
        return f"{b / 1024 ** 3:.1f} GB"


def fmt_time(path: Path) -> str:
    try:
        dt   = datetime.fromtimestamp(path.stat().st_mtime)
        diff = datetime.now() - dt
        if diff.seconds < 60:    return "Just now"
        if diff.seconds < 3600:  return f"{diff.seconds // 60} min ago"
        if diff.days == 0:       return f"{diff.seconds // 3600} hr ago"
        if diff.days == 1:       return "Yesterday"
        if diff.days < 7:        return f"{diff.days} days ago"
        return dt.strftime("%d %b %Y")
    except Exception:
        return ""


def get_drive_usage(path: Path):
    """
    Return (used_bytes, total_bytes) for the drive
    containing the given path. Returns (0, 0) on error.
    """
    try:
        usage = shutil.disk_usage(str(path))
        return usage.used, usage.total
    except Exception:
        return 0, 0


# -----------------------------------------------
# THEME TOGGLE
# -----------------------------------------------
class ThemeToggle(QWidget):
    """
    Looks like a normal light/dark mode slider.
    Switching to dark emits dark_mode_activated which
    triggers the BODMAS screen.
    """

    dark_mode_activated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self.setFixedSize(120, 32)
        self._build()

    def _build(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)

        self.sun_lbl = QLabel("☀")
        self.sun_lbl.setStyleSheet(
            f"color:{L_ACCENT};font-size:14px;background:transparent;"
        )
        h.addWidget(self.sun_lbl)

        self.track = QPushButton()
        self.track.setFixedSize(44, 24)
        self.track.clicked.connect(self._toggle)
        h.addWidget(self.track)

        self.moon_lbl = QLabel("☾")
        self.moon_lbl.setStyleSheet(
            f"color:{L_TEXT3};font-size:14px;background:transparent;"
        )
        h.addWidget(self.moon_lbl)

        # Set initial style after all widgets are created
        self._apply_style()

    def _apply_style(self):
        if self.is_dark:
            self.track.setStyleSheet(
                "QPushButton{"
                "  background-color:#1A73E8;"
                "  border-radius:12px;border:none;"
                "  color:#ffffff;font-size:12px;"
                "  text-align:right;padding-right:4px;"
                "}"
            )
            self.track.setText("●  ")
            self.sun_lbl.setStyleSheet(
                f"color:{L_TEXT3};font-size:14px;background:transparent;"
            )
            self.moon_lbl.setStyleSheet(
                f"color:{L_ACCENT};font-size:14px;background:transparent;"
            )
        else:
            self.track.setStyleSheet(
                "QPushButton{"
                f"  background-color:{L_BORDER};"
                "  border-radius:12px;border:none;"
                "  color:#555555;font-size:12px;"
                "  text-align:left;padding-left:4px;"
                "}"
            )
            self.track.setText("  ●")
            self.sun_lbl.setStyleSheet(
                f"color:{L_ACCENT};font-size:14px;background:transparent;"
            )
            self.moon_lbl.setStyleSheet(
                f"color:{L_TEXT3};font-size:14px;background:transparent;"
            )

    def _toggle(self):
        self.is_dark = not self.is_dark
        self._apply_style()
        if self.is_dark:
            self.dark_mode_activated.emit()


# -----------------------------------------------
# FILE CARD
# -----------------------------------------------
class FileCard(QWidget):
    """
    A single file or folder card in the grid.
    No border by default. Shows border only on hover or selection.
    """

    clicked        = pyqtSignal(Path)
    double_clicked = pyqtSignal(Path)

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.path     = path
        self.selected = False
        self.setFixedSize(160, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()
        self._set_style(False)

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 14, 10, 10)
        v.setSpacing(6)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel(get_icon(self.path))
        icon_lbl.setStyleSheet(
            "font-size:32px;background:transparent;"
        )
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(icon_lbl)

        name = self.path.name
        if len(name) > 18:
            name = name[:15] + "..."
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"color:{L_TEXT};font-size:12px;font-weight:500;"
            f"background:transparent;"
        )
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setWordWrap(True)
        v.addWidget(name_lbl)

        try:
            if self.path.is_file():
                detail = fmt_size(self.path.stat().st_size)
            else:
                items  = sum(1 for _ in self.path.iterdir())
                detail = f"{items} item{'s' if items != 1 else ''}"
        except Exception:
            detail = ""

        detail_lbl = QLabel(detail)
        detail_lbl.setStyleSheet(
            f"color:{L_TEXT3};font-size:10px;background:transparent;"
        )
        detail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(detail_lbl)

    def _set_style(self, selected: bool):
        if selected:
            self.setStyleSheet(
                "QWidget{"
                f"  background-color:{L_SELECTED};"
                f"  border:1px solid {L_ACCENT};"
                "  border-radius:8px;"
                "}"
            )
        else:
            self.setStyleSheet(
                "QWidget{"
                "  background-color:transparent;"
                "  border:none;"
                "  border-radius:8px;"
                "}"
            )

    def mousePressEvent(self, event):
        self.selected = not self.selected
        self._set_style(self.selected)
        self.clicked.emit(self.path)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.path)

    def enterEvent(self, event):
        if not self.selected:
            self.setStyleSheet(
                "QWidget{"
                f"  background-color:{L_CARD_H};"
                f"  border:1px solid {L_BORDER};"
                "  border-radius:8px;"
                "}"
            )

    def leaveEvent(self, event):
        self._set_style(self.selected)


# -----------------------------------------------
# SIDEBAR ITEM
# -----------------------------------------------
class SidebarItem(QPushButton):
    """A clickable item in the left sidebar."""

    def __init__(self, icon: str, label: str,
                 path: Path, parent=None):
        super().__init__(parent)
        self.nav_path = path

        h = QHBoxLayout(self)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(
            f"font-size:15px;background:transparent;color:{L_TEXT};"
        )
        h.addWidget(icon_lbl)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(
            f"color:{L_TEXT};font-size:13px;background:transparent;"
        )
        h.addWidget(name_lbl)
        h.addStretch()

        self.setFixedHeight(36)
        self.set_inactive()

    def set_active(self):
        self.setStyleSheet(
            "QPushButton{"
            f"  background-color:{L_SELECTED};"
            f"  border-radius:6px;border:none;"
            "}"
            "QPushButton QLabel{"
            f"  color:{L_ACCENT};"
            "}"
        )

    def set_inactive(self):
        self.setStyleSheet(
            "QPushButton{"
            "  background-color:transparent;"
            "  border:none;"
            "}"
            "QPushButton:hover{"
            f"  background-color:{L_CARD_H};"
            "  border-radius:6px;"
            "}"
        )


# -----------------------------------------------
# STORAGE BAR WIDGET
# Shows real disk usage for the current drive.
# Updates every time the user navigates.
# -----------------------------------------------
class StorageBar(QWidget):
    """
    Displays the real disk usage for the current drive.
    The bar fills proportionally to how full the drive is.
    The label shows used / total in GB.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 4, 12, 4)
        v.setSpacing(4)

        self.drive_lbl = QLabel("Local Disk")
        self.drive_lbl.setStyleSheet(
            f"color:{L_TEXT2};font-size:11px;background:transparent;"
        )
        v.addWidget(self.drive_lbl)

        # Bar background
        self.bar_bg = QFrame()
        self.bar_bg.setFixedHeight(5)
        self.bar_bg.setStyleSheet(
            f"background:{L_BAR_BG};border-radius:2px;"
        )
        v.addWidget(self.bar_bg)

        # Usage detail label
        self.detail_lbl = QLabel("")
        self.detail_lbl.setStyleSheet(
            f"color:{L_TEXT3};font-size:10px;background:transparent;"
        )
        v.addWidget(self.detail_lbl)

    def update_for_path(self, path: Path):
        """
        Recalculate and redraw the storage bar
        for the drive containing the given path.
        Called every time the user navigates to a new location.
        """
        used, total = get_drive_usage(path)

        if total == 0:
            self.drive_lbl.setText("Storage unavailable")
            self.detail_lbl.setText("")
            return

        # Figure out the drive root letter for display
        try:
            drive_root = Path(path.anchor)
            drive_name = str(drive_root).replace("\\", "")
        except Exception:
            drive_name = "Drive"

        self.drive_lbl.setText(f"Drive  {drive_name}")

        # Calculate fill percentage
        pct  = min(used / total, 1.0)
        bar_w = max(2, int((self.bar_bg.width() or 160) * pct))

        # Colour changes: green under 70%, amber under 90%, red above
        if pct < 0.70:
            colour = L_ACCENT
        elif pct < 0.90:
            colour = "#F57C00"
        else:
            colour = L_RED

        # Remove old fill if any, then create new fill
        for child in self.bar_bg.findChildren(QFrame):
            child.deleteLater()

        fill = QFrame(self.bar_bg)
        fill.setFixedHeight(5)
        fill.setFixedWidth(bar_w)
        fill.setStyleSheet(
            f"background:{colour};border-radius:2px;"
        )
        fill.show()

        self.detail_lbl.setText(
            f"{fmt_size(used)} of {fmt_size(total)} used"
        )

    def resizeEvent(self, event):
        """Refresh the bar width when the widget is resized."""
        super().resizeEvent(event)


# -----------------------------------------------
# MAIN FAKE DASHBOARD
# -----------------------------------------------
class FakeDashboard(QMainWindow):
    """
    The fake light mode file manager.
    Looks and behaves like a real file manager.
    The only hidden element is the theme toggle
    in the top right which triggers the vault layer.
    """

    dark_mode_triggered = pyqtSignal()
    logout_requested    = pyqtSignal()

    def __init__(self, username: str = "User", parent=None):
        super().__init__(parent)

        self.username    = username
        self.current_path = Path.home()
        self.history     = [self.current_path]
        self.history_pos = 0
        self.all_cards   = []
        self.sort_mode   = 'name'

        self.setWindowTitle("Files")
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None

        self.setStyleSheet(self._global_style())
        self._build()
        self._load_directory(self.current_path)

    def _global_style(self):
        return f"""
            QMainWindow, QWidget {{
                background-color: {L_BG};
                color: {L_TEXT};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                background: transparent;
                color: {L_TEXT};
            }}
            QLineEdit {{
                background-color: {L_CARD};
                border: 1px solid {L_BORDER};
                border-radius: 20px;
                padding: 6px 16px;
                color: {L_TEXT};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {L_ACCENT};
            }}
            QScrollBar:vertical {{
                background: {L_BG};
                width: 6px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {L_BORDER2};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                height: 0px;
            }}
        """

    # -----------------------------------------------
    # LAYOUT
    # -----------------------------------------------

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)

        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        v.addWidget(self._build_titlebar())
        v.addWidget(self._build_navbar())

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{L_BORDER};")
        v.addWidget(div)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        content.addWidget(self._build_sidebar())

        vdiv = QFrame()
        vdiv.setFixedWidth(1)
        vdiv.setStyleSheet(f"background:{L_BORDER};")
        content.addWidget(vdiv)

        content.addWidget(self._build_main_area())

        cw = QWidget()
        cw.setLayout(content)
        v.addWidget(cw, stretch=1)

        v.addWidget(self._build_statusbar())

    def _build_titlebar(self):
        bar = QWidget()
        bar.setFixedHeight(TITLEBAR_H)
        bar.setStyleSheet(f"background:{L_TITLEBAR};")

        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(0)

        app_name = QLabel("Files")
        app_name.setStyleSheet(
            f"color:{L_TEXT};font-size:14px;font-weight:600;"
            f"background:transparent;"
        )
        h.addWidget(app_name)
        h.addStretch()

        greet = QLabel(f"Hello, {self.username}")
        greet.setStyleSheet(
            f"color:{L_TEXT3};font-size:12px;background:transparent;"
        )
        h.addWidget(greet)
        h.addSpacing(20)

        # THE HIDDEN TRIGGER
        self.theme_toggle = ThemeToggle()
        self.theme_toggle.dark_mode_activated.connect(
            self.dark_mode_triggered.emit
        )
        h.addWidget(self.theme_toggle)
        h.addSpacing(20)

        min_btn = QPushButton("─")
        min_btn.setFixedSize(32, 32)
        min_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;"
            f"color:{L_TEXT3};font-size:14px;}}"
            f"QPushButton:hover{{background:{L_BORDER};"
            f"border-radius:4px;}}"
        )
        min_btn.clicked.connect(self.showMinimized)
        h.addWidget(min_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;"
            f"color:{L_TEXT3};font-size:12px;}}"
            f"QPushButton:hover{{background:{L_RED};"
            f"color:white;border-radius:4px;}}"
        )
        close_btn.clicked.connect(QApplication.quit)
        h.addWidget(close_btn)

        return bar

    def _build_navbar(self):
        nav = QWidget()
        nav.setFixedHeight(NAVBAR_H)
        nav.setStyleSheet(f"background:{L_NAVBAR};")

        h = QHBoxLayout(nav)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(8)

        btn_style = (
            f"QPushButton{{background:{L_CARD};"
            f"border:1px solid {L_BORDER};"
            f"border-radius:16px;"
            f"color:{L_TEXT};"
            f"font-size:18px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{L_CARD_H};}}"
            f"QPushButton:disabled{{color:{L_TEXT3};}}"
        )

        self.back_btn = QPushButton("‹")
        self.back_btn.setFixedSize(32, 32)
        self.back_btn.setStyleSheet(btn_style)
        self.back_btn.clicked.connect(self._go_back)
        h.addWidget(self.back_btn)

        self.fwd_btn = QPushButton("›")
        self.fwd_btn.setFixedSize(32, 32)
        self.fwd_btn.setStyleSheet(btn_style)
        self.fwd_btn.clicked.connect(self._go_forward)
        h.addWidget(self.fwd_btn)

        up_btn = QPushButton("↑")
        up_btn.setFixedSize(32, 32)
        up_btn.setStyleSheet(btn_style)
        up_btn.clicked.connect(self._go_up)
        h.addWidget(up_btn)

        h.addSpacing(4)

        self.path_lbl = QLabel(str(self.current_path))
        self.path_lbl.setStyleSheet(
            f"color:{L_TEXT2};font-size:12px;background:transparent;"
        )
        self.path_lbl.setMaximumWidth(480)
        h.addWidget(self.path_lbl)

        h.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search files...")
        self.search_bar.setFixedSize(220, 32)
        self.search_bar.textChanged.connect(self._filter_files)
        h.addWidget(self.search_bar)

        return nav

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(SIDEBAR_W)
        sidebar.setStyleSheet(f"background:{L_SIDEBAR};")

        v = QVBoxLayout(sidebar)
        v.setContentsMargins(8, 16, 8, 8)
        v.setSpacing(2)

        v.addWidget(self._section_lbl("QUICK ACCESS"))

        home = Path.home()
        locations = [
            ("🏠", "Home",      home),
            ("🖥",  "Desktop",   home / "Desktop"),
            ("📥", "Downloads", home / "Downloads"),
            ("📄", "Documents", home / "Documents"),
            ("🖼",  "Pictures",  home / "Pictures"),
            ("🎬", "Videos",    home / "Videos"),
            ("🎵", "Music",     home / "Music"),
        ]

        self.sidebar_items = []
        for icon, name, path in locations:
            if path.exists():
                item = SidebarItem(icon, name, path)
                item.clicked.connect(
                    lambda checked, p=path: self._navigate_to(p)
                )
                self.sidebar_items.append((item, path))
                v.addWidget(item)

        v.addSpacing(8)
        v.addWidget(self._section_lbl("DEVICES"))

        for letter in string.ascii_uppercase:
            drive = Path(f"{letter}:\\")
            if drive.exists():
                item = SidebarItem("💾", f"Drive ({letter}:)", drive)
                item.clicked.connect(
                    lambda checked, p=drive: self._navigate_to(p)
                )
                self.sidebar_items.append((item, drive))
                v.addWidget(item)

        v.addStretch()

        # Storage section - updates dynamically per drive
        v.addWidget(self._section_lbl("STORAGE"))
        self.storage_bar = StorageBar()
        v.addWidget(self.storage_bar)

        return sidebar

    def _section_lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(
            f"color:{L_TEXT3};font-size:10px;font-weight:600;"
            f"letter-spacing:1px;padding-left:12px;padding-top:6px;"
            f"background:transparent;"
        )
        return l

    def _build_main_area(self):
        container = QWidget()
        container.setStyleSheet(f"background:{L_BG};")

        v = QVBoxLayout(container)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        v.addWidget(self._build_toolbar())

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet(
            f"QScrollArea{{background:{L_BG};border:none;}}"
        )

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet(f"background:{L_BG};")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(20, 16, 20, 16)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )

        self.scroll.setWidget(self.grid_widget)
        v.addWidget(self.scroll, stretch=1)

        return container

    def _build_toolbar(self):
        toolbar = QWidget()
        toolbar.setFixedHeight(42)
        toolbar.setStyleSheet(
            f"background:{L_BG};"
            f"border-bottom:1px solid {L_BORDER};"
        )

        h = QHBoxLayout(toolbar)
        h.setContentsMargins(20, 0, 20, 0)
        h.setSpacing(10)

        self.location_title = QLabel("Home")
        self.location_title.setStyleSheet(
            f"color:{L_TEXT};font-size:14px;font-weight:600;"
            f"background:transparent;"
        )
        h.addWidget(self.location_title)

        h.addStretch()

        self.item_count_lbl = QLabel("")
        self.item_count_lbl.setStyleSheet(
            f"color:{L_TEXT3};font-size:12px;background:transparent;"
        )
        h.addWidget(self.item_count_lbl)

        sort_btn_style = (
            f"QPushButton{{background:{L_CARD};"
            f"border:1px solid {L_BORDER};"
            f"border-radius:4px;color:{L_TEXT2};"
            f"font-size:12px;padding:0 10px;}}"
            f"QPushButton:hover{{"
            f"border:1px solid {L_ACCENT};"
            f"color:{L_ACCENT};}}"
            f"QPushButton:checked{{"
            f"background:{L_SELECTED};"
            f"border:1px solid {L_ACCENT};"
            f"color:{L_ACCENT};}}"
        )

        for label, mode in [("Name", "name"),
                             ("Date", "date"),
                             ("Size", "size")]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setStyleSheet(sort_btn_style)
            btn.clicked.connect(
                lambda checked, m=mode: self._sort_and_reload(m)
            )
            h.addWidget(btn)

        return toolbar

    def _build_statusbar(self):
        status = QWidget()
        status.setFixedHeight(28)
        status.setStyleSheet(
            f"background:{L_NAVBAR};"
            f"border-top:1px solid {L_BORDER};"
        )

        h = QHBoxLayout(status)
        h.setContentsMargins(16, 0, 16, 0)

        self.status_lbl = QLabel("Ready")
        self.status_lbl.setStyleSheet(
            f"color:{L_TEXT3};font-size:11px;background:transparent;"
        )
        h.addWidget(self.status_lbl)
        h.addStretch()

        self.path_status = QLabel("")
        self.path_status.setStyleSheet(
            f"color:{L_TEXT3};font-size:11px;background:transparent;"
        )
        h.addWidget(self.path_status)

        return status

    # -----------------------------------------------
    # FILE LOADING
    # -----------------------------------------------

    def _load_directory(self, path: Path):
        """
        Load directory contents, sort them, build cards,
        and update all UI labels and the storage bar.
        """
        self.current_path = path

        self.path_lbl.setText(str(path))
        self.path_status.setText(str(path))
        self.location_title.setText(path.name or str(path))
        self.search_bar.clear()

        # Update storage bar for the current drive
        self.storage_bar.update_for_path(path)

        # Highlight active sidebar item
        for item, item_path in self.sidebar_items:
            if item_path == path:
                item.set_active()
            else:
                item.set_inactive()

        self._clear_grid()

        try:
            items = list(path.iterdir())
        except PermissionError:
            self.status_lbl.setText("Access denied to this folder.")
            return
        except Exception as e:
            self.status_lbl.setText(f"Cannot open: {e}")
            return

        folders, files = self._sort_items(
            [i for i in items if i.is_dir()],
            [i for i in items if i.is_file()],
            self.sort_mode
        )
        sorted_items = (folders + files)[:200]

        cols = max(1, (WIN_W - SIDEBAR_W - 60) // 172)
        self.all_cards = []

        for i, item in enumerate(sorted_items):
            try:
                card = FileCard(item)
                card.clicked.connect(self._on_card_click)
                card.double_clicked.connect(self._on_card_double_click)
                self.all_cards.append(card)
                self.grid_layout.addWidget(
                    card, i // cols, i % cols
                )
            except Exception:
                continue

        count = len(sorted_items)
        nf    = len(folders)
        nfi   = len(files)
        self.item_count_lbl.setText(
            f"{count} item{'s' if count != 1 else ''}"
        )
        self.status_lbl.setText(
            f"{nf} folder{'s' if nf != 1 else ''},"
            f"  {nfi} file{'s' if nfi != 1 else ''}"
        )

        self.back_btn.setEnabled(self.history_pos > 0)
        self.fwd_btn.setEnabled(
            self.history_pos < len(self.history) - 1
        )

    def _sort_items(self, folders, files, mode):
        """Sort folders and files by the given mode."""
        if mode == 'name':
            folders.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
        elif mode == 'date':
            try:
                folders.sort(
                    key=lambda x: x.stat().st_mtime, reverse=True
                )
                files.sort(
                    key=lambda x: x.stat().st_mtime, reverse=True
                )
            except Exception:
                pass
        elif mode == 'size':
            folders.sort(key=lambda x: x.name.lower())
            try:
                files.sort(
                    key=lambda x: x.stat().st_size, reverse=True
                )
            except Exception:
                pass
        return folders, files

    def _sort_and_reload(self, mode: str):
        """Change the sort mode and reload the current directory."""
        self.sort_mode = mode
        self._load_directory(self.current_path)
        self.status_lbl.setText(f"Sorted by {mode}.")

    def _clear_grid(self):
        """Remove all file cards from the grid."""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.all_cards = []

    def _filter_files(self, query: str):
        """Show only cards whose file name contains the search query."""
        q = query.lower().strip()
        for card in self.all_cards:
            card.setVisible(not q or q in card.path.name.lower())

    # -----------------------------------------------
    # NAVIGATION
    # -----------------------------------------------

    def _navigate_to(self, path: Path):
        if not path.is_dir():
            return
        self.history = self.history[:self.history_pos + 1]
        self.history.append(path)
        self.history_pos = len(self.history) - 1
        self._load_directory(path)

    def _go_back(self):
        if self.history_pos > 0:
            self.history_pos -= 1
            self._load_directory(self.history[self.history_pos])

    def _go_forward(self):
        if self.history_pos < len(self.history) - 1:
            self.history_pos += 1
            self._load_directory(self.history[self.history_pos])

    def _go_up(self):
        parent = self.current_path.parent
        if parent != self.current_path:
            self._navigate_to(parent)

    def _on_card_click(self, path: Path):
        info = ""
        try:
            if path.is_file():
                info = f"  |  {fmt_size(path.stat().st_size)}"
        except Exception:
            pass
        self.status_lbl.setText(f"Selected:  {path.name}{info}")

    def _on_card_double_click(self, path: Path):
        if path.is_dir():
            self._navigate_to(path)
        else:
            self.status_lbl.setText(f"Opening:  {path.name}")

    # -----------------------------------------------
    # WINDOW DRAG
    # -----------------------------------------------

    def mousePressEvent(self, event):
        if event.position().y() < TITLEBAR_H:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(
                self.pos() +
                event.globalPosition().toPoint() - self._drag_pos
            )
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# -----------------------------------------------
# ENTRY POINT
# -----------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = FakeDashboard(username="Test User")
    window.show()
    sys.exit(app.exec())
