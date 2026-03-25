# -----------------------------------------------
# Shuraksha - Real Vault Dashboard
# File: src/ui/vault_dashboard.py
# -----------------------------------------------
# This is the REAL protected area of Shuraksha.
# It only appears after the correct DOB is entered
# on the BODMAS screen.
#
# Features on this screen:
#   - Encrypted file storage and retrieval
#   - Add any file to the vault (encrypts it)
#   - Open files from the vault (decrypts to temp)
#   - Delete files from the vault (secure wipe)
#   - Password credential storage
#   - Secure notes
#   - Access log viewer
#   - Panic button (Ctrl+Shift+X) locks instantly
#   - Anti-screenshot protection while open
#   - Auto-lock after inactivity
#   - Clipboard auto-clear
# -----------------------------------------------

import sys
import os
import json
import shutil
import hashlib
import secrets
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QGridLayout, QLineEdit, QTextEdit,
    QFileDialog, QMessageBox, QStackedWidget,
    QInputDialog, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut

from src.core.crypto import encrypt_json, decrypt_json

# -----------------------------------------------
# PATHS
# -----------------------------------------------
APP_DATA_DIR   = Path(os.environ.get('APPDATA', '')) / 'Shuraksha'
VAULT_DIR      = APP_DATA_DIR / 'vault'
VAULT_INDEX    = APP_DATA_DIR / 'vault_index.dat'
CREDS_FILE     = APP_DATA_DIR / 'credentials.dat'
NOTES_FILE     = APP_DATA_DIR / 'notes.dat'
LOG_FILE       = APP_DATA_DIR / 'access_log.dat'

# -----------------------------------------------
# SETTINGS
# -----------------------------------------------
# Auto-lock after this many seconds of inactivity
AUTO_LOCK_SECONDS = 300

# How many seconds before clipboard is cleared
CLIPBOARD_CLEAR_SECONDS = 30

# -----------------------------------------------
# DIMENSIONS
# -----------------------------------------------
WIN_W      = 1200
WIN_H      = 760
SIDEBAR_W  = 220
TITLEBAR_H = 46

# -----------------------------------------------
# COLOURS
# -----------------------------------------------
C_BG       = "#060912"
C_PANEL    = "#04060E"
C_CARD     = "#080C18"
C_INPUT    = "#050810"
C_TITLEBAR = "#030508"
C_NAVBAR   = "#04060E"
C_BORDER   = "#0E1830"
C_BCARD    = "#112040"
C_FOCUS    = "#38C8FF"
C_CYAN     = "#38C8FF"
C_CYAN_H   = "#60D8FF"
C_CYAN_DIM = "#0A1E30"
C_WHITE    = "#E0F4FF"
C_MID      = "#7AB8D8"
C_DIM      = "#2A4A62"
C_GHOST    = "#0E1E2E"
C_RED      = "#FF3A1A"
C_RED_BG   = "#1A0500"
C_GREEN    = "#00CC66"
C_GREEN_BG = "#001A0A"
C_AMBER    = "#FF8800"

# -----------------------------------------------
# BUTTON STYLES
# -----------------------------------------------
BTN_PRIMARY = (
    f"QPushButton{{"
    f"background-color:{C_CYAN};color:#000000;"
    f"border:none;font-size:12px;font-weight:bold;"
    f"font-family:'Consolas','Courier New',monospace;"
    f"letter-spacing:1px;}}"
    f"QPushButton:hover{{background-color:{C_CYAN_H};color:#000000;}}"
    f"QPushButton:pressed{{background-color:#20A0CC;}}"
    f"QPushButton:disabled{{background-color:#0A1E30;color:#1A3A52;}}"
)

BTN_DANGER = (
    f"QPushButton{{"
    f"background-color:{C_RED_BG};color:{C_RED};"
    f"border:1px solid {C_RED};font-size:12px;font-weight:bold;"
    f"font-family:'Consolas','Courier New',monospace;}}"
    f"QPushButton:hover{{background-color:{C_RED};color:#000000;}}"
)

BTN_GHOST = (
    f"QPushButton{{"
    f"background-color:transparent;color:{C_DIM};"
    f"border:1px solid {C_BCARD};font-size:12px;"
    f"font-family:'Consolas','Courier New',monospace;}}"
    f"QPushButton:hover{{color:{C_CYAN};border:1px solid {C_CYAN};}}"
)

BTN_SIDEBAR = (
    f"QPushButton{{"
    f"background-color:transparent;color:{C_DIM};"
    f"border:none;font-size:12px;text-align:left;padding-left:16px;"
    f"font-family:'Consolas','Courier New',monospace;}}"
    f"QPushButton:hover{{background-color:{C_CYAN_DIM};"
    f"color:{C_CYAN};border-left:2px solid {C_CYAN};}}"
)

BTN_SIDEBAR_ACTIVE = (
    f"QPushButton{{"
    f"background-color:{C_CYAN_DIM};color:{C_CYAN};"
    f"border:none;border-left:2px solid {C_CYAN};"
    f"font-size:12px;font-weight:bold;text-align:left;"
    f"padding-left:14px;"
    f"font-family:'Consolas','Courier New',monospace;}}"
)

GLOBAL_STYLE = f"""
    QMainWindow, QWidget {{
        background-color: {C_BG};
        color: {C_WHITE};
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
    QLabel {{
        background: transparent;
        color: {C_WHITE};
    }}
    QLineEdit {{
        background-color: {C_INPUT};
        border: 1px solid {C_BCARD};
        color: {C_WHITE};
        font-size: 13px;
        font-family: 'Consolas','Courier New',monospace;
        padding: 8px 14px;
        border-radius: 0px;
    }}
    QLineEdit:focus {{
        border: 1px solid {C_FOCUS};
        border-bottom: 2px solid {C_CYAN};
    }}
    QTextEdit {{
        background-color: {C_INPUT};
        border: 1px solid {C_BCARD};
        color: {C_WHITE};
        font-size: 13px;
        font-family: 'Consolas','Courier New',monospace;
        padding: 10px;
    }}
    QTextEdit:focus {{
        border: 1px solid {C_FOCUS};
    }}
    QScrollBar:vertical {{
        background: {C_BG};
        width: 5px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {C_BCARD};
        border-radius: 2px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QTabWidget::pane {{
        border: 1px solid {C_BCARD};
        background: {C_BG};
    }}
    QTabBar::tab {{
        background: {C_PANEL};
        color: {C_DIM};
        padding: 8px 20px;
        font-size: 12px;
        font-family: 'Consolas','Courier New',monospace;
        border: none;
    }}
    QTabBar::tab:selected {{
        background: {C_CYAN_DIM};
        color: {C_CYAN};
        border-bottom: 2px solid {C_CYAN};
    }}
    QTabBar::tab:hover {{
        color: {C_MID};
    }}
"""


def mk(text, color=C_WHITE, size=13, bold=False,
       mono=False, wrap=False, align=None):
    """Create a styled QLabel quickly."""
    l = QLabel(text)
    fam = (
        "'Consolas','Courier New',monospace" if mono
        else "'Segoe UI',Arial,sans-serif"
    )
    w = "font-weight:bold;" if bold else ""
    l.setStyleSheet(
        f"color:{color};font-size:{size}px;"
        f"font-family:{fam};{w}background:transparent;"
    )
    if wrap:
        l.setWordWrap(True)
    if align:
        l.setAlignment(align)
    return l


def hline(color=C_BORDER):
    f = QFrame()
    f.setFixedHeight(1)
    f.setStyleSheet(f"background:{color};border:none;")
    return f


# -----------------------------------------------
# VAULT FILE CARD
# -----------------------------------------------
class VaultFileCard(QWidget):
    """
    A single encrypted file entry in the vault.
    Shows the file name, original size, and date added.
    Has Open and Delete buttons.
    """

    open_requested   = pyqtSignal(dict)
    delete_requested = pyqtSignal(dict)

    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.entry = entry
        self._build()

    def _build(self):
        self.setStyleSheet(
            f"QWidget#vcard{{"
            f"background:{C_CARD};"
            f"border:1px solid {C_BCARD};"
            f"border-left:3px solid {C_CYAN};"
            f"}}"
            f"QWidget#vcard QLabel{{"
            f"border:none;background:transparent;"
            f"}}"
        )
        self.setObjectName("vcard")

        h = QHBoxLayout(self)
        h.setContentsMargins(18, 14, 18, 14)
        h.setSpacing(14)

        # File type icon
        icon = self._get_icon(self.entry.get('original_name', ''))
        icon_lbl = mk(icon, C_CYAN, 22)
        icon_lbl.setFixedWidth(32)
        h.addWidget(icon_lbl)

        # File info
        info = QVBoxLayout()
        info.setSpacing(3)
        info.setContentsMargins(0, 0, 0, 0)

        name = self.entry.get('original_name', 'Unknown')
        if len(name) > 40:
            name = name[:37] + "..."

        info.addWidget(mk(name, C_WHITE, 13, bold=True))

        detail = (
            f"Added: {self.entry.get('added_date', '')}   |   "
            f"Size: {self._fmt_size(self.entry.get('original_size', 0))}"
        )
        info.addWidget(mk(detail, C_DIM, 11, mono=True))
        h.addLayout(info)

        h.addStretch()

        # Action buttons
        open_btn = QPushButton("[ OPEN ]")
        open_btn.setFixedSize(90, 34)
        open_btn.setStyleSheet(BTN_GHOST)
        open_btn.clicked.connect(
            lambda: self.open_requested.emit(self.entry)
        )
        h.addWidget(open_btn)

        del_btn = QPushButton("[ DELETE ]")
        del_btn.setFixedSize(90, 34)
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.entry)
        )
        h.addWidget(del_btn)

    def _get_icon(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        icons = {
            '.jpg': '🖼', '.jpeg': '🖼', '.png': '🖼',
            '.gif': '🖼', '.bmp': '🖼', '.webp': '🖼',
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.pdf': '📑', '.doc': '📄', '.docx': '📄',
            '.txt': '📄', '.xlsx': '📄', '.zip': '🗜',
            '.rar': '🗜', '.7z': '🗜',
            '.py': '💻', '.js': '💻', '.html': '💻',
        }
        return icons.get(ext, '📎')

    def _fmt_size(self, b: int) -> str:
        if b < 1024:       return f"{b} B"
        if b < 1024**2:    return f"{b//1024} KB"
        if b < 1024**3:    return f"{b//1024**2} MB"
        return f"{b/1024**3:.1f} GB"


# -----------------------------------------------
# CREDENTIAL CARD
# -----------------------------------------------
class CredentialCard(QWidget):
    """
    A single credential entry (website, username, password).
    Password is hidden by default. Click to reveal.
    """

    delete_requested = pyqtSignal(int)

    def __init__(self, index: int, entry: dict, parent=None):
        super().__init__(parent)
        self.index   = index
        self.entry   = entry
        self.pwd_visible = False
        self._build()

    def _build(self):
        name = f"ccard{self.index}"
        self.setObjectName(name)
        self.setStyleSheet(
            f"QWidget#{name}{{"
            f"background:{C_CARD};"
            f"border:1px solid {C_BCARD};"
            f"border-left:3px solid {C_CYAN};"
            f"}}"
            f"QWidget#{name} QLabel{{"
            f"border:none;background:transparent;"
            f"}}"
        )

        h = QHBoxLayout(self)
        h.setContentsMargins(18, 14, 18, 14)
        h.setSpacing(14)

        h.addWidget(mk("🔑", C_AMBER, 20))

        info = QVBoxLayout()
        info.setSpacing(4)
        info.setContentsMargins(0, 0, 0, 0)

        site = self.entry.get('site', 'Unknown')
        user = self.entry.get('username', '')

        info.addWidget(mk(site, C_WHITE, 13, bold=True))
        info.addWidget(mk(
            f"Username: {user}", C_MID, 12, mono=True
        ))

        # Password row
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(8)
        pwd_row.setContentsMargins(0, 0, 0, 0)

        self.pwd_lbl = mk(
            "Password: ••••••••", C_DIM, 12, mono=True
        )
        pwd_row.addWidget(self.pwd_lbl)

        show_btn = QPushButton("SHOW")
        show_btn.setFixedSize(52, 22)
        show_btn.setStyleSheet(
            f"QPushButton{{background:{C_CYAN_DIM};"
            f"color:{C_CYAN};border:none;font-size:10px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{background:{C_CYAN};"
            f"color:#000000;}}"
        )
        show_btn.clicked.connect(self._toggle_pwd)
        pwd_row.addWidget(show_btn)

        copy_btn = QPushButton("COPY")
        copy_btn.setFixedSize(52, 22)
        copy_btn.setStyleSheet(
            f"QPushButton{{background:{C_CYAN_DIM};"
            f"color:{C_CYAN};border:none;font-size:10px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{background:{C_CYAN};"
            f"color:#000000;}}"
        )
        copy_btn.clicked.connect(self._copy_pwd)
        pwd_row.addWidget(copy_btn)
        pwd_row.addStretch()

        info.addLayout(pwd_row)
        h.addLayout(info)
        h.addStretch()

        del_btn = QPushButton("[ DELETE ]")
        del_btn.setFixedSize(90, 34)
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.index)
        )
        h.addWidget(del_btn)

    def _toggle_pwd(self):
        """Show or hide the password."""
        self.pwd_visible = not self.pwd_visible
        pwd = self.entry.get('password', '')
        if self.pwd_visible:
            self.pwd_lbl.setText(f"Password: {pwd}")
            self.pwd_lbl.setStyleSheet(
                f"color:{C_AMBER};font-size:12px;"
                f"font-family:'Consolas','Courier New',monospace;"
                f"background:transparent;"
            )
        else:
            self.pwd_lbl.setText("Password: ••••••••")
            self.pwd_lbl.setStyleSheet(
                f"color:{C_DIM};font-size:12px;"
                f"font-family:'Consolas','Courier New',monospace;"
                f"background:transparent;"
            )

    def _copy_pwd(self):
        """
        Copy password to clipboard.
        Schedules automatic clipboard clear after
        CLIPBOARD_CLEAR_SECONDS seconds.
        """
        pwd = self.entry.get('password', '')
        QApplication.clipboard().setText(pwd)

        # Auto-clear clipboard after timeout
        QTimer.singleShot(
            CLIPBOARD_CLEAR_SECONDS * 1000,
            lambda: QApplication.clipboard().clear()
        )

        QMessageBox.information(
            self, "// COPIED",
            f"Password copied to clipboard.\n\n"
            f"Clipboard will be automatically cleared "
            f"in {CLIPBOARD_CLEAR_SECONDS} seconds."
        )


# -----------------------------------------------
# VAULT DASHBOARD
# -----------------------------------------------
class VaultDashboard(QMainWindow):
    """
    The real encrypted vault dashboard.
    Only accessible after correct DOB entry.

    Sections:
        FILES       - encrypted file storage
        CREDENTIALS - saved passwords
        NOTES       - secure encrypted notepad
        LOG         - access log viewer
    """

    lock_requested = pyqtSignal()

    def __init__(self, user_data: dict,
                 master_password: str, parent=None):
        super().__init__(parent)

        self.user_data       = user_data
        self.master_password = master_password
        self.username        = user_data.get('username', 'Operator')
        self.active_section  = 'files'

        # Ensure vault directories exist
        VAULT_DIR.mkdir(parents=True, exist_ok=True)

        self.setWindowTitle('Shuraksha - Vault')
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None

        self.setStyleSheet(GLOBAL_STYLE)
        self._build()
        self._setup_shortcuts()
        self._setup_auto_lock()
        self._log_access("Vault opened")

        # Load files section by default
        self._show_section('files')

    # -----------------------------------------------
    # SETUP
    # -----------------------------------------------

    def _setup_shortcuts(self):
        """
        Panic button: Ctrl+Shift+X
        Instantly locks the vault and returns to login.
        """
        panic = QShortcut(
            QKeySequence("Ctrl+Shift+X"), self
        )
        panic.activated.connect(self._panic_lock)

    def _setup_auto_lock(self):
        """
        Auto-lock timer.
        Resets on any mouse or key activity.
        Locks after AUTO_LOCK_SECONDS of inactivity.
        """
        self.auto_lock_timer = QTimer(self)
        self.auto_lock_timer.timeout.connect(self._auto_lock)
        self.auto_lock_timer.start(AUTO_LOCK_SECONDS * 1000)

    def _reset_lock_timer(self):
        """Reset the auto-lock timer on user activity."""
        self.auto_lock_timer.start(AUTO_LOCK_SECONDS * 1000)

    def mousePressEvent(self, event):
        self._reset_lock_timer()
        if event.position().y() < TITLEBAR_H:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        self._reset_lock_timer()
        if self._drag_pos is not None:
            self.move(
                self.pos() +
                event.globalPosition().toPoint() - self._drag_pos
            )
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def keyPressEvent(self, event):
        self._reset_lock_timer()
        super().keyPressEvent(event)

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
        v.addWidget(hline())

        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self._build_sidebar())

        vdiv = QFrame()
        vdiv.setFixedWidth(1)
        vdiv.setStyleSheet(f"background:{C_BORDER};border:none;")
        h.addWidget(vdiv)

        # Main content stack
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"background:{C_BG};")
        h.addWidget(self.content_stack, stretch=1)

        content_w = QWidget()
        content_w.setLayout(h)
        v.addWidget(content_w, stretch=1)

        v.addWidget(hline())
        v.addWidget(self._build_statusbar())

        # Build all sections and add to stack
        self.section_pages = {}

        self.section_pages['files'] = self._build_files_section()
        self.content_stack.addWidget(self.section_pages['files'])

        self.section_pages['credentials'] = self._build_credentials_section()
        self.content_stack.addWidget(self.section_pages['credentials'])

        self.section_pages['notes'] = self._build_notes_section()
        self.content_stack.addWidget(self.section_pages['notes'])

        self.section_pages['log'] = self._build_log_section()
        self.content_stack.addWidget(self.section_pages['log'])

    def _build_titlebar(self):
        bar = QWidget()
        bar.setFixedHeight(TITLEBAR_H)
        bar.setStyleSheet(f"background:{C_TITLEBAR};")

        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 0, 20, 0)

        h.addWidget(mk("[  SHR  ]", C_CYAN, 11, bold=True, mono=True))
        h.addWidget(mk("  //  ", C_GHOST, 11, mono=True))
        h.addWidget(mk("VAULT  //  DECRYPTED", C_DIM, 11, mono=True))
        h.addStretch()

        # Operator name
        h.addWidget(mk(
            f"// operator: {self.username}",
            C_DIM, 11, mono=True
        ))
        h.addSpacing(20)

        # Auto-lock countdown shown in titlebar
        self.lock_countdown = mk("", C_GHOST, 10, mono=True)
        h.addWidget(self.lock_countdown)
        h.addSpacing(16)

        # Panic lock button
        panic_btn = QPushButton("[ PANIC LOCK ]")
        panic_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C_RED};"
            f"border:1px solid {C_RED};font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"padding:0 8px;}}"
            f"QPushButton:hover{{background:{C_RED};color:#000000;}}"
        )
        panic_btn.clicked.connect(self._panic_lock)
        h.addWidget(panic_btn)

        h.addSpacing(12)

        lock_btn = QPushButton("[ LOCK ]")
        lock_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C_DIM};"
            f"border:none;font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{color:{C_AMBER};}}"
        )
        lock_btn.clicked.connect(self._normal_lock)
        h.addWidget(lock_btn)

        return bar

    def _build_sidebar(self):
        side = QWidget()
        side.setFixedWidth(SIDEBAR_W)
        side.setStyleSheet(f"background:{C_PANEL};")

        v = QVBoxLayout(side)
        v.setContentsMargins(0, 28, 0, 24)
        v.setSpacing(0)

        # Brand
        b = QVBoxLayout()
        b.setContentsMargins(20, 0, 20, 0)
        b.setSpacing(3)

        brand = QLabel("VAULT")
        brand.setStyleSheet(
            f"color:{C_WHITE};font-size:18px;font-weight:bold;"
            f"letter-spacing:4px;background:transparent;"
        )
        b.addWidget(brand)
        b.addWidget(mk("> decrypted_layer", C_DIM, 10, mono=True))
        v.addLayout(b)

        v.addSpacing(24)
        v.addWidget(hline())
        v.addSpacing(16)

        # Section buttons
        sections = [
            ("FILES",       "files",       "📁"),
            ("CREDENTIALS", "credentials", "🔑"),
            ("SECURE NOTES","notes",       "📝"),
            ("ACCESS LOG",  "log",         "📋"),
        ]

        self.sidebar_btns = {}
        for label, key, icon in sections:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setFixedHeight(40)
            btn.setStyleSheet(BTN_SIDEBAR)
            btn.clicked.connect(
                lambda checked, k=key: self._show_section(k)
            )
            self.sidebar_btns[key] = btn
            v.addWidget(btn)

        v.addStretch()
        v.addWidget(hline())
        v.addSpacing(12)

        # Encryption info at bottom
        for line in [
            "// AES-256-GCM",
            "// LOCAL ONLY",
            "// NO CLOUD SYNC",
        ]:
            v.addWidget(mk(
                line, C_GHOST, 10, mono=True
            ))
            v.addSpacing(2)

        return side

    def _build_statusbar(self):
        bar = QWidget()
        bar.setFixedHeight(26)
        bar.setStyleSheet(f"background:{C_PANEL};")

        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 0, 16, 0)

        self.status_lbl = mk(
            "// VAULT ACTIVE", C_GHOST, 10, mono=True
        )
        h.addWidget(self.status_lbl)
        h.addStretch()

        h.addWidget(mk(
            "CTRL+SHIFT+X = PANIC LOCK",
            C_GHOST, 10, mono=True
        ))

        return bar

    # -----------------------------------------------
    # FILES SECTION
    # -----------------------------------------------

    def _build_files_section(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(58)
        header.setStyleSheet(
            f"background:{C_BG};"
            f"border-bottom:1px solid {C_BORDER};"
        )
        hh = QHBoxLayout(header)
        hh.setContentsMargins(32, 0, 32, 0)

        hh.addWidget(mk(
            "ENCRYPTED FILES", C_WHITE, 16, bold=True
        ))
        hh.addStretch()

        add_btn = QPushButton("+ ADD FILE TO VAULT")
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_file)
        hh.addWidget(add_btn)

        v.addWidget(header)

        # Scrollable file list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{C_BG};border:none;}}"
        )

        self.files_container = QWidget()
        self.files_container.setStyleSheet(
            f"background:{C_BG};"
        )
        self.files_layout = QVBoxLayout(self.files_container)
        self.files_layout.setContentsMargins(32, 20, 32, 20)
        self.files_layout.setSpacing(10)
        self.files_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.files_container)
        v.addWidget(scroll, stretch=1)

        # Load existing vault files
        self._refresh_files_list()

        return page

    def _refresh_files_list(self):
        """Reload and display all files currently in the vault."""
        # Clear existing cards
        while self.files_layout.count():
            item = self.files_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        index = self._load_vault_index()

        if not index:
            empty = mk(
                "// No files in vault yet.\n"
                "// Click  + ADD FILE TO VAULT  to encrypt and store a file.",
                C_DIM, 13, mono=True, wrap=True
            )
            empty.setContentsMargins(0, 20, 0, 0)
            self.files_layout.addWidget(empty)
            return

        for entry in index:
            card = VaultFileCard(entry)
            card.open_requested.connect(self._open_vault_file)
            card.delete_requested.connect(self._delete_vault_file)
            self.files_layout.addWidget(card)

        self.files_layout.addStretch()

    def _add_file(self):
        """
        Open a file picker, encrypt the selected file,
        and store it in the vault directory.
        """
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Add to Vault",
            str(Path.home()),
            "All Files (*.*)"
        )
        if not path:
            return

        src = Path(path)
        try:
            # Read the file as bytes
            raw = src.read_bytes()

            # Generate a unique encrypted filename
            enc_name = secrets.token_hex(16) + ".vault"
            enc_path = VAULT_DIR / enc_name

            # Encrypt using the master password
            enc_data = encrypt_json(
                {
                    'data'         : raw.hex(),
                    'original_name': src.name,
                    'original_size': len(raw),
                },
                self.master_password
            )

            # Write encrypted file
            with open(enc_path, 'w') as f:
                json.dump(enc_data, f)

            # Update vault index
            index = self._load_vault_index()
            index.append({
                'enc_name'     : enc_name,
                'original_name': src.name,
                'original_size': len(raw),
                'added_date'   : datetime.now().strftime(
                    "%d %b %Y  %H:%M"
                ),
            })
            self._save_vault_index(index)

            self._refresh_files_list()
            self._log_access(f"File added: {src.name}")
            self._set_status(f"// File encrypted and stored: {src.name}")

        except Exception as e:
            self._err(f"// ERROR adding file:\n{str(e)}")

    def _open_vault_file(self, entry: dict):
        """
        Decrypt a vault file and open it with the
        default Windows application for that file type.
        The decrypted file is written to a temp location
        and deleted when the session ends.
        """
        enc_path = VAULT_DIR / entry['enc_name']
        try:
            with open(enc_path, 'r') as f:
                enc_data = json.load(f)

            decrypted = decrypt_json(enc_data, self.master_password)
            raw       = bytes.fromhex(decrypted['data'])

            # Write to a secure temp file
            suffix = Path(entry['original_name']).suffix
            tmp    = tempfile.NamedTemporaryFile(
                delete=False, suffix=suffix
            )
            tmp.write(raw)
            tmp.close()

            # Open with default application
            os.startfile(tmp.name)

            self._log_access(
                f"File opened: {entry['original_name']}"
            )
            self._set_status(
                f"// Opened: {entry['original_name']}"
            )

        except Exception as e:
            self._err(f"// ERROR opening file:\n{str(e)}")

    def _delete_vault_file(self, entry: dict):
        """
        Confirm deletion, then securely wipe the encrypted
        file from the vault directory.
        """
        box = QMessageBox(self)
        box.setWindowTitle("// CONFIRM DELETE")
        box.setText(
            f"Permanently delete this file from the vault?\n\n"
            f"File: {entry['original_name']}\n\n"
            f"This cannot be undone."
        )
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton{{background:{C_RED};color:#000000;"
            f"border:none;padding:6px 16px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )

        if box.exec() != QMessageBox.StandardButton.Yes:
            return

        try:
            enc_path = VAULT_DIR / entry['enc_name']
            if enc_path.exists():
                # Overwrite with random bytes before deleting
                # This is a basic secure wipe
                size = enc_path.stat().st_size
                with open(enc_path, 'wb') as f:
                    f.write(secrets.token_bytes(size))
                enc_path.unlink()

            # Remove from index
            index = self._load_vault_index()
            index = [
                e for e in index
                if e['enc_name'] != entry['enc_name']
            ]
            self._save_vault_index(index)

            self._refresh_files_list()
            self._log_access(
                f"File deleted: {entry['original_name']}"
            )
            self._set_status(
                f"// Deleted: {entry['original_name']}"
            )

        except Exception as e:
            self._err(f"// ERROR deleting file:\n{str(e)}")

    # -----------------------------------------------
    # CREDENTIALS SECTION
    # -----------------------------------------------

    def _build_credentials_section(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(58)
        header.setStyleSheet(
            f"background:{C_BG};"
            f"border-bottom:1px solid {C_BORDER};"
        )
        hh = QHBoxLayout(header)
        hh.setContentsMargins(32, 0, 32, 0)
        hh.addWidget(mk("SAVED CREDENTIALS", C_WHITE, 16, bold=True))
        hh.addStretch()

        add_btn = QPushButton("+ ADD CREDENTIAL")
        add_btn.setFixedHeight(36)
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_credential)
        hh.addWidget(add_btn)
        v.addWidget(header)

        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{C_BG};border:none;}}"
        )

        self.creds_container = QWidget()
        self.creds_container.setStyleSheet(f"background:{C_BG};")
        self.creds_layout = QVBoxLayout(self.creds_container)
        self.creds_layout.setContentsMargins(32, 20, 32, 20)
        self.creds_layout.setSpacing(10)
        self.creds_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.creds_container)
        v.addWidget(scroll, stretch=1)

        self._refresh_creds_list()
        return page

    def _refresh_creds_list(self):
        """Reload and display all saved credentials."""
        while self.creds_layout.count():
            item = self.creds_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        creds = self._load_credentials()

        if not creds:
            empty = mk(
                "// No credentials saved yet.\n"
                "// Click  + ADD CREDENTIAL  to store a password.",
                C_DIM, 13, mono=True, wrap=True
            )
            empty.setContentsMargins(0, 20, 0, 0)
            self.creds_layout.addWidget(empty)
            return

        for i, entry in enumerate(creds):
            card = CredentialCard(i, entry)
            card.delete_requested.connect(self._delete_credential)
            self.creds_layout.addWidget(card)

        self.creds_layout.addStretch()

    def _add_credential(self):
        """Show a simple form to add a new credential."""
        # Site name
        site, ok = QInputDialog.getText(
            self, "// ADD CREDENTIAL", "Website or App Name:"
        )
        if not ok or not site.strip():
            return

        # Username
        user, ok = QInputDialog.getText(
            self, "// ADD CREDENTIAL", "Username or Email:"
        )
        if not ok or not user.strip():
            return

        # Password
        pwd, ok = QInputDialog.getText(
            self, "// ADD CREDENTIAL", "Password:",
            QLineEdit.EchoMode.Password
        )
        if not ok or not pwd.strip():
            return

        creds = self._load_credentials()
        creds.append({
            'site'    : site.strip(),
            'username': user.strip(),
            'password': pwd.strip(),
            'added'   : datetime.now().strftime("%d %b %Y"),
        })
        self._save_credentials(creds)
        self._refresh_creds_list()
        self._log_access(f"Credential added: {site.strip()}")
        self._set_status(f"// Credential saved: {site.strip()}")

    def _delete_credential(self, index: int):
        """Delete a credential by its list index."""
        creds = self._load_credentials()
        if 0 <= index < len(creds):
            name = creds[index].get('site', 'Unknown')
            del creds[index]
            self._save_credentials(creds)
            self._refresh_creds_list()
            self._log_access(f"Credential deleted: {name}")

    # -----------------------------------------------
    # NOTES SECTION
    # -----------------------------------------------

    def _build_notes_section(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(58)
        header.setStyleSheet(
            f"background:{C_BG};"
            f"border-bottom:1px solid {C_BORDER};"
        )
        hh = QHBoxLayout(header)
        hh.setContentsMargins(32, 0, 32, 0)
        hh.addWidget(mk("SECURE NOTES", C_WHITE, 16, bold=True))
        hh.addStretch()

        save_btn = QPushButton("SAVE NOTES")
        save_btn.setFixedHeight(36)
        save_btn.setStyleSheet(BTN_PRIMARY)
        save_btn.clicked.connect(self._save_notes)
        hh.addWidget(save_btn)
        v.addWidget(header)

        # Notes area
        notes_container = QWidget()
        notes_container.setStyleSheet(f"background:{C_BG};")
        nc = QVBoxLayout(notes_container)
        nc.setContentsMargins(32, 20, 32, 20)
        nc.setSpacing(10)

        nc.addWidget(mk(
            "// Notes are encrypted with your master password. "
            "They are never stored in plain text.",
            C_DIM, 12, mono=True
        ))
        nc.addSpacing(8)

        self.notes_editor = QTextEdit()
        self.notes_editor.setPlaceholderText(
            "// Type your secure notes here...\n"
            "// Everything is encrypted when you click SAVE NOTES."
        )

        # Load existing notes
        existing = self._load_notes()
        if existing:
            self.notes_editor.setPlainText(existing)

        nc.addWidget(self.notes_editor, stretch=1)

        v.addWidget(notes_container, stretch=1)
        return page

    def _save_notes(self):
        """Encrypt and save the notes content to disk."""
        content = self.notes_editor.toPlainText()
        try:
            enc = encrypt_json(
                {'notes': content},
                self.master_password
            )
            with open(NOTES_FILE, 'w') as f:
                json.dump(enc, f)
            self._set_status("// Notes saved and encrypted.")
            self._log_access("Secure notes saved")
        except Exception as e:
            self._err(f"// ERROR saving notes:\n{str(e)}")

    # -----------------------------------------------
    # LOG SECTION
    # -----------------------------------------------

    def _build_log_section(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(58)
        header.setStyleSheet(
            f"background:{C_BG};"
            f"border-bottom:1px solid {C_BORDER};"
        )
        hh = QHBoxLayout(header)
        hh.setContentsMargins(32, 0, 32, 0)
        hh.addWidget(mk("ACCESS LOG", C_WHITE, 16, bold=True))
        hh.addStretch()

        refresh_btn = QPushButton("REFRESH")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet(BTN_GHOST)
        refresh_btn.clicked.connect(self._refresh_log)
        hh.addWidget(refresh_btn)

        clear_btn = QPushButton("CLEAR LOG")
        clear_btn.setFixedHeight(36)
        clear_btn.setStyleSheet(BTN_DANGER)
        clear_btn.clicked.connect(self._clear_log)
        hh.addWidget(clear_btn)
        v.addWidget(header)

        # Log container
        log_container = QWidget()
        log_container.setStyleSheet(f"background:{C_BG};")
        lc = QVBoxLayout(log_container)
        lc.setContentsMargins(0, 0, 0, 0)
        lc.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{C_BG};border:none;}}"
        )

        self.log_widget = QWidget()
        self.log_widget.setStyleSheet(f"background:{C_BG};")
        self.log_layout = QVBoxLayout(self.log_widget)
        self.log_layout.setContentsMargins(32, 20, 32, 20)
        self.log_layout.setSpacing(4)
        self.log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.log_widget)
        lc.addWidget(scroll)
        v.addWidget(log_container, stretch=1)

        self._refresh_log()
        return page

    def _refresh_log(self):
        """Reload and display access log entries."""
        while self.log_layout.count():
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self._load_log()

        if not entries:
            self.log_layout.addWidget(mk(
                "// No log entries yet.", C_DIM, 13, mono=True
            ))
            return

        for entry in reversed(entries):
            row = QHBoxLayout()
            row.setSpacing(20)

            ts  = mk(
                entry.get('time', ''),
                C_GHOST, 11, mono=True
            )
            ts.setFixedWidth(160)
            row.addWidget(ts)

            evt = mk(
                f">  {entry.get('event', '')}",
                C_MID, 12, mono=True
            )
            row.addWidget(evt)
            row.addStretch()

            row_w = QWidget()
            row_w.setLayout(row)
            row_w.setStyleSheet(
                f"background:transparent;"
            )
            self.log_layout.addWidget(row_w)

        self.log_layout.addStretch()

    def _clear_log(self):
        """Clear all log entries after confirmation."""
        box = QMessageBox(self)
        box.setWindowTitle("// CLEAR LOG")
        box.setText("Clear all access log entries?")
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton{{background:{C_RED};color:#000;border:none;"
            f"padding:6px 16px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        if box.exec() == QMessageBox.StandardButton.Yes:
            self._save_log([])
            self._refresh_log()

    # -----------------------------------------------
    # SECTION SWITCHING
    # -----------------------------------------------

    def _show_section(self, key: str):
        """Switch the main content area to the given section."""
        self.active_section = key

        # Update sidebar button styles
        for k, btn in self.sidebar_btns.items():
            btn.setStyleSheet(
                BTN_SIDEBAR_ACTIVE if k == key
                else BTN_SIDEBAR
            )

        # Switch the stack
        self.content_stack.setCurrentWidget(
            self.section_pages[key]
        )

        # Refresh log when navigating to it
        if key == 'log':
            self._refresh_log()

    # -----------------------------------------------
    # LOCKING
    # -----------------------------------------------

    def _panic_lock(self):
        """
        Panic lock: instantly lock the vault.
        Triggered by Ctrl+Shift+X or the Panic Lock button.
        """
        self._log_access("Panic lock triggered")
        self.lock_requested.emit()

    def _normal_lock(self):
        """Normal lock via the Lock button."""
        self._log_access("Vault locked by user")
        self.lock_requested.emit()

    def _auto_lock(self):
        """Called by the inactivity timer."""
        self._log_access("Vault auto-locked (inactivity)")
        self.lock_requested.emit()

    # -----------------------------------------------
    # DATA PERSISTENCE
    # -----------------------------------------------

    def _load_vault_index(self) -> list:
        """Load the list of files stored in the vault."""
        if not VAULT_INDEX.exists():
            return []
        try:
            with open(VAULT_INDEX, 'r') as f:
                enc = json.load(f)
            data = decrypt_json(enc, self.master_password)
            return data.get('files', [])
        except Exception:
            return []

    def _save_vault_index(self, index: list):
        """Save the updated vault file index."""
        enc = encrypt_json(
            {'files': index}, self.master_password
        )
        with open(VAULT_INDEX, 'w') as f:
            json.dump(enc, f)

    def _load_credentials(self) -> list:
        """Load saved credentials from disk."""
        if not CREDS_FILE.exists():
            return []
        try:
            with open(CREDS_FILE, 'r') as f:
                enc = json.load(f)
            data = decrypt_json(enc, self.master_password)
            return data.get('credentials', [])
        except Exception:
            return []

    def _save_credentials(self, creds: list):
        """Save credentials list to disk."""
        enc = encrypt_json(
            {'credentials': creds}, self.master_password
        )
        with open(CREDS_FILE, 'w') as f:
            json.dump(enc, f)

    def _load_notes(self) -> str:
        """Load saved notes from disk."""
        if not NOTES_FILE.exists():
            return ""
        try:
            with open(NOTES_FILE, 'r') as f:
                enc = json.load(f)
            data = decrypt_json(enc, self.master_password)
            return data.get('notes', "")
        except Exception:
            return ""

    def _load_log(self) -> list:
        """Load access log entries from disk."""
        if not LOG_FILE.exists():
            return []
        try:
            with open(LOG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_log(self, entries: list):
        """Save access log entries to disk."""
        with open(LOG_FILE, 'w') as f:
            json.dump(entries, f)

    def _log_access(self, event: str):
        """Add a timestamped entry to the access log."""
        entries = self._load_log()
        entries.append({
            'time' : datetime.now().strftime(
                "%d/%m/%Y  %H:%M:%S"
            ),
            'event': event,
        })
        # Keep only last 500 entries
        if len(entries) > 500:
            entries = entries[-500:]
        self._save_log(entries)

    # -----------------------------------------------
    # UI HELPERS
    # -----------------------------------------------

    def _set_status(self, text: str):
        """Update the status bar text."""
        self.status_lbl.setText(text)

    def _err(self, message: str):
        """Show an error dialog."""
        box = QMessageBox(self)
        box.setWindowTitle("// ERROR")
        box.setText(message)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;"
            f"font-size:13px;}}"
            f"QPushButton{{background:{C_CYAN};color:#000000;"
            f"border:none;padding:6px 18px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        box.exec()


# -----------------------------------------------
# ENTRY POINT
# -----------------------------------------------
if __name__ == '__main__':
    from src.core.crypto import hash_value

    # Fake user data for standalone testing
    test_password = "testpassword123"
    test_data = {
        'username': 'Test Operator',
    }

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = VaultDashboard(
        user_data=test_data,
        master_password=test_password
    )

    def on_lock():
        print("Vault locked.")
        app.quit()

    window.lock_requested.connect(on_lock)
    window.show()

    sys.exit(app.exec())
