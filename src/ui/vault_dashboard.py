# -----------------------------------------------
# Shuraksha - Real Vault Dashboard
# File: src/ui/vault_dashboard.py
# -----------------------------------------------

import sys
import os
import json
import shutil
import secrets
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit, QTextEdit,
    QFileDialog, QMessageBox, QStackedWidget,
    QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut

from src.core.crypto import encrypt_json, decrypt_json

# Import security module safely
# If it fails for any reason the app still works
try:
    from src.core.security import security
    SECURITY_AVAILABLE = True
except Exception:
    security           = None
    SECURITY_AVAILABLE = False

# -----------------------------------------------
# PATHS
# -----------------------------------------------
APP_DATA_DIR = Path(os.environ.get('APPDATA', '')) / 'Shuraksha'
VAULT_DIR    = APP_DATA_DIR / 'vault'
FILES_DIR    = VAULT_DIR / 'files'
META_FILE    = VAULT_DIR / 'meta.dat'
CREDS_FILE   = VAULT_DIR / 'creds.dat'
NOTES_FILE   = VAULT_DIR / 'notes.dat'
LOG_FILE     = VAULT_DIR / 'access.log'

# -----------------------------------------------
# SETTINGS
# -----------------------------------------------
AUTO_LOCK_SECONDS = 300

# -----------------------------------------------
# DIMENSIONS
# -----------------------------------------------
WIN_W      = 1100
WIN_H      = 720
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
    f"  background-color:{C_CYAN};"
    f"  color:#000000;"
    f"  border:none;"
    f"  font-size:13px;"
    f"  font-weight:bold;"
    f"  font-family:'Consolas','Courier New',monospace;"
    f"  letter-spacing:1px;"
    f"}}"
    f"QPushButton:hover{{"
    f"  background-color:{C_CYAN_H};"
    f"  color:#000000;"
    f"}}"
    f"QPushButton:pressed{{"
    f"  background-color:#20A0CC;"
    f"}}"
)

BTN_GHOST = (
    f"QPushButton{{"
    f"  background-color:transparent;"
    f"  color:{C_DIM};"
    f"  border:1px solid {C_BCARD};"
    f"  font-size:12px;"
    f"  font-family:'Consolas','Courier New',monospace;"
    f"}}"
    f"QPushButton:hover{{"
    f"  color:{C_CYAN};"
    f"  border:1px solid {C_CYAN};"
    f"}}"
)

BTN_DANGER = (
    f"QPushButton{{"
    f"  background-color:{C_RED_BG};"
    f"  color:{C_RED};"
    f"  border:1px solid {C_RED};"
    f"  font-size:12px;"
    f"  font-family:'Consolas','Courier New',monospace;"
    f"}}"
    f"QPushButton:hover{{"
    f"  background-color:{C_RED};"
    f"  color:#000000;"
    f"}}"
)

BTN_SUCCESS = (
    f"QPushButton{{"
    f"  background-color:{C_GREEN_BG};"
    f"  color:{C_GREEN};"
    f"  border:1px solid {C_GREEN};"
    f"  font-size:12px;"
    f"  font-family:'Consolas','Courier New',monospace;"
    f"}}"
    f"QPushButton:hover{{"
    f"  background-color:{C_GREEN};"
    f"  color:#000000;"
    f"}}"
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
        padding: 10px 14px;
        border-radius: 0px;
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
"""


# -----------------------------------------------
# HELPERS
# -----------------------------------------------
def mk(text, color=C_WHITE, size=13, bold=False,
       mono=False, wrap=False, align=None):
    """Create a styled QLabel quickly."""
    l = QLabel(text)
    family = (
        "'Consolas','Courier New',monospace"
        if mono else "'Segoe UI',Arial,sans-serif"
    )
    w = "font-weight:bold;" if bold else ""
    l.setStyleSheet(
        f"color:{color};font-size:{size}px;"
        f"font-family:{family};{w}background:transparent;"
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


def write_log(entry: str):
    """
    Append a timestamped entry to the access log file.
    This function is also called by security.py so it
    must not import anything from security.py to avoid
    circular imports.
    """
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}]  {entry}\n")
    except Exception:
        pass


# -----------------------------------------------
# VAULT MANAGER
# -----------------------------------------------
class VaultManager:
    """
    Handles all encrypted file operations.
    All files are encrypted with AES-256-GCM before
    being stored. No plaintext ever sits on disk.
    """

    def __init__(self, master_password: str):
        self.password = master_password
        FILES_DIR.mkdir(parents=True, exist_ok=True)

    def load_meta(self) -> list:
        """Load the file metadata index."""
        if not META_FILE.exists():
            return []
        try:
            with open(META_FILE, 'r') as f:
                enc = json.load(f)
            data = decrypt_json(enc, self.password)
            return data.get('files', [])
        except Exception:
            return []

    def save_meta(self, files: list):
        """Save the file metadata index."""
        try:
            enc = encrypt_json({'files': files}, self.password)
            with open(META_FILE, 'w') as f:
                json.dump(enc, f)
        except Exception as e:
            raise Exception(f"Failed to save metadata: {e}")

    def add_file(self, source_path: Path) -> dict:
        """Encrypt and store a file in the vault."""
        data     = source_path.read_bytes()
        vault_id = secrets.token_hex(16)

        enc = encrypt_json(
            {'data': data.hex(), 'name': source_path.name},
            self.password
        )

        dest = FILES_DIR / vault_id
        with open(dest, 'w') as f:
            json.dump(enc, f)

        meta = {
            'id'   : vault_id,
            'name' : source_path.name,
            'size' : len(data),
            'added': datetime.now().strftime("%d %b %Y  %H:%M"),
            'type' : source_path.suffix.lower() or 'file',
        }

        files = self.load_meta()
        files.append(meta)
        self.save_meta(files)

        write_log(f"FILE_ADDED  {source_path.name}")
        return meta

    def export_file(self, vault_id: str, dest_dir: Path) -> Path:
        """Decrypt and export a file."""
        vault_path = FILES_DIR / vault_id
        if not vault_path.exists():
            raise Exception("Vault file not found.")

        with open(vault_path, 'r') as f:
            enc = json.load(f)

        data_dict = decrypt_json(enc, self.password)
        raw       = bytes.fromhex(data_dict['data'])
        name      = data_dict['name']
        out_path  = dest_dir / name
        out_path.write_bytes(raw)

        write_log(f"FILE_EXPORTED  {name}")
        return out_path

    def delete_file(self, vault_id: str):
        """Securely delete a file with 3-pass overwrite."""
        vault_path = FILES_DIR / vault_id
        if vault_path.exists():
            size = vault_path.stat().st_size
            for _ in range(3):
                vault_path.write_bytes(secrets.token_bytes(size))
            vault_path.unlink()

        files = self.load_meta()
        files = [f for f in files if f['id'] != vault_id]
        self.save_meta(files)
        write_log(f"FILE_DELETED  {vault_id}")

    def load_creds(self) -> list:
        """Load saved credentials."""
        if not CREDS_FILE.exists():
            return []
        try:
            with open(CREDS_FILE, 'r') as f:
                enc = json.load(f)
            data = decrypt_json(enc, self.password)
            return data.get('creds', [])
        except Exception:
            return []

    def save_creds(self, creds: list):
        """Save credentials."""
        enc = encrypt_json({'creds': creds}, self.password)
        with open(CREDS_FILE, 'w') as f:
            json.dump(enc, f)

    def load_notes(self) -> str:
        """Load secure notes content."""
        if not NOTES_FILE.exists():
            return ""
        try:
            with open(NOTES_FILE, 'r') as f:
                enc = json.load(f)
            data = decrypt_json(enc, self.password)
            return data.get('content', "")
        except Exception:
            return ""

    def save_notes(self, content: str):
        """Save secure notes content."""
        enc = encrypt_json({'content': content}, self.password)
        with open(NOTES_FILE, 'w') as f:
            json.dump(enc, f)

    def load_log(self) -> str:
        """Load the raw access log text."""
        if not LOG_FILE.exists():
            return "// No access log entries yet."
        try:
            return LOG_FILE.read_text(encoding='utf-8')
        except Exception:
            return "// Could not read access log."


# -----------------------------------------------
# FILE ROW WIDGET
# -----------------------------------------------
class FileRow(QWidget):
    """A single row in the vault file list."""

    export_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, meta: dict, parent=None):
        super().__init__(parent)
        self.vault_id = meta['id']
        self._build(meta)

    def _build(self, meta: dict):
        self.setFixedHeight(56)
        self.setStyleSheet(
            f"QWidget{{"
            f"  background:{C_CARD};"
            f"  border-bottom:1px solid {C_BORDER};"
            f"}}"
        )

        h = QHBoxLayout(self)
        h.setContentsMargins(20, 0, 16, 0)
        h.setSpacing(16)

        icon_lbl = QLabel(self._get_icon(meta.get('type', '')))
        icon_lbl.setStyleSheet(
            "font-size:20px;background:transparent;"
        )
        icon_lbl.setFixedWidth(28)
        h.addWidget(icon_lbl)

        name_lbl = mk(meta['name'], C_WHITE, 13, bold=True)
        name_lbl.setMinimumWidth(200)
        h.addWidget(name_lbl)

        h.addStretch()

        size_lbl = mk(
            self._fmt_size(meta.get('size', 0)),
            C_DIM, 12, mono=True
        )
        size_lbl.setFixedWidth(80)
        size_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        h.addWidget(size_lbl)

        date_lbl = mk(meta.get('added', ''), C_DIM, 12, mono=True)
        date_lbl.setFixedWidth(160)
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        h.addWidget(date_lbl)

        exp_btn = QPushButton("EXPORT")
        exp_btn.setFixedSize(80, 32)
        exp_btn.setStyleSheet(BTN_GHOST)
        exp_btn.clicked.connect(
            lambda: self.export_requested.emit(self.vault_id)
        )
        h.addWidget(exp_btn)

        del_btn = QPushButton("DELETE")
        del_btn.setFixedSize(80, 32)
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.vault_id)
        )
        h.addWidget(del_btn)

    def _get_icon(self, ext: str) -> str:
        icons = {
            '.jpg': '🖼', '.jpeg': '🖼', '.png': '🖼',
            '.gif': '🖼', '.bmp': '🖼', '.webp': '🖼',
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬',
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
            '.pdf': '📑',
            '.doc': '📄', '.docx': '📄', '.txt': '📄',
            '.zip': '🗜', '.rar': '🗜',
            '.py':  '💻', '.js':  '💻',
        }
        return icons.get(ext, '📎')

    def _fmt_size(self, b: int) -> str:
        if b < 1024:     return f"{b} B"
        if b < 1024**2:  return f"{b//1024} KB"
        if b < 1024**3:  return f"{b//1024**2} MB"
        return f"{b/1024**3:.1f} GB"


# -----------------------------------------------
# CREDENTIAL ROW WIDGET
# -----------------------------------------------
class CredRow(QWidget):
    """A single row in the credentials list."""

    delete_requested = pyqtSignal(int)

    def __init__(self, cred: dict, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self._build(cred)

    def _build(self, cred: dict):
        self.setFixedHeight(52)
        self.setStyleSheet(
            f"QWidget{{"
            f"  background:{C_CARD};"
            f"  border-bottom:1px solid {C_BORDER};"
            f"}}"
        )

        h = QHBoxLayout(self)
        h.setContentsMargins(20, 0, 16, 0)
        h.setSpacing(16)

        site_lbl = mk(
            cred.get('site', ''), C_WHITE, 13, bold=True
        )
        site_lbl.setMinimumWidth(180)
        h.addWidget(site_lbl)

        user_lbl = mk(
            cred.get('username', ''), C_MID, 12, mono=True
        )
        user_lbl.setMinimumWidth(160)
        h.addWidget(user_lbl)

        pwd = cred.get('password', '')
        self.pwd_lbl = mk(
            "●" * min(len(pwd), 16), C_DIM, 12, mono=True
        )
        self.pwd_lbl.setMinimumWidth(140)
        h.addWidget(self.pwd_lbl)

        h.addStretch()

        self._pwd_visible = False
        self._pwd_text    = pwd

        self.show_btn = QPushButton("SHOW")
        self.show_btn.setFixedSize(70, 30)
        self.show_btn.setStyleSheet(BTN_GHOST)
        self.show_btn.clicked.connect(self._toggle_pwd)
        h.addWidget(self.show_btn)

        copy_btn = QPushButton("COPY")
        copy_btn.setFixedSize(70, 30)
        copy_btn.setStyleSheet(BTN_GHOST)
        copy_btn.clicked.connect(self._copy_pwd)
        h.addWidget(copy_btn)

        del_btn = QPushButton("DEL")
        del_btn.setFixedSize(60, 30)
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.index)
        )
        h.addWidget(del_btn)

    def _toggle_pwd(self):
        self._pwd_visible = not self._pwd_visible
        if self._pwd_visible:
            self.pwd_lbl.setText(self._pwd_text)
            self.pwd_lbl.setStyleSheet(
                f"color:{C_CYAN};font-size:12px;"
                f"font-family:'Consolas','Courier New',monospace;"
                f"background:transparent;"
            )
            self.show_btn.setText("HIDE")
        else:
            self.pwd_lbl.setText(
                "●" * min(len(self._pwd_text), 16)
            )
            self.pwd_lbl.setStyleSheet(
                f"color:{C_DIM};font-size:12px;"
                f"font-family:'Consolas','Courier New',monospace;"
                f"background:transparent;"
            )
            self.show_btn.setText("SHOW")

    def _copy_pwd(self):
        """Copy password and schedule clipboard clear."""
        QApplication.clipboard().setText(self._pwd_text)
        # Auto-clear clipboard after 30 seconds
        if SECURITY_AVAILABLE and security:
            security.schedule_clipboard_clear(30)
        else:
            QTimer.singleShot(
                30000,
                lambda: QApplication.clipboard().setText("")
            )


# -----------------------------------------------
# VAULT DASHBOARD
# -----------------------------------------------
class VaultDashboard(QMainWindow):
    """
    The real encrypted vault dashboard.
    Only accessible after correct DOB entry.

    Security features active while vault is open:
        - Print Screen key blocked
        - Window excluded from screenshots
        - Process scanner running in background
        - Auto-lock after inactivity
        - Panic lock on Ctrl+Shift+X
    """

    lock_requested = pyqtSignal()

    def __init__(self, user_data: dict,
                 master_password: str, parent=None):
        super().__init__(parent)

        self.user_data  = user_data
        self.username   = user_data.get('username', 'Operator')
        self.vault      = VaultManager(master_password)
        self.active_section = 'files'

        # Auto-lock timer
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._auto_lock)
        self.idle_timer.start(AUTO_LOCK_SECONDS * 1000)

        self.setWindowTitle("Shuraksha Vault")
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None

        self.setStyleSheet(GLOBAL_STYLE)
        self._build()

        # Panic button shortcut
        self.panic = QShortcut(
            QKeySequence("Ctrl+Shift+X"), self
        )
        self.panic.activated.connect(self._instant_lock)

        # Log vault open
        write_log(f"VAULT_OPENED  operator:{self.username}")

        # Start security monitoring after vault opens
        # Use a timer delay to ensure window handle is ready
        QTimer.singleShot(500, self._start_security)

    def _start_security(self):
        """
        Start security monitoring after the window
        has fully loaded and the window handle exists.
        """
        try:
            if SECURITY_AVAILABLE and security:
                security.set_lock_callback(self._instant_lock)
                security.start()
                # Block window from appearing in screenshots
                hwnd = int(self.winId())
                security.block_screenshot_api(hwnd)
        except Exception:
            pass

    def _stop_security(self):
        """Stop security monitoring and unblock screenshots."""
        try:
            if SECURITY_AVAILABLE and security:
                security.stop()
                hwnd = int(self.winId())
                security.unblock_screenshot_api(hwnd)
        except Exception:
            pass

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

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        content.addWidget(self._build_sidebar())

        vdiv = QFrame()
        vdiv.setFixedWidth(1)
        vdiv.setStyleSheet(f"background:{C_BORDER};border:none;")
        content.addWidget(vdiv)

        self.section_stack = QStackedWidget()
        self.section_stack.addWidget(self._build_files_section())
        self.section_stack.addWidget(self._build_creds_section())
        self.section_stack.addWidget(self._build_notes_section())
        self.section_stack.addWidget(self._build_log_section())
        content.addWidget(self.section_stack, stretch=1)

        cw = QWidget()
        cw.setLayout(content)
        v.addWidget(cw, stretch=1)

        v.addWidget(self._build_statusbar())

    def _build_titlebar(self):
        bar = QWidget()
        bar.setFixedHeight(TITLEBAR_H)
        bar.setStyleSheet(f"background:{C_TITLEBAR};")

        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 0, 20, 0)

        h.addWidget(mk("[  SHR  ]", C_CYAN, 11, bold=True, mono=True))
        h.addWidget(mk("  //  ",    C_GHOST, 11, mono=True))
        h.addWidget(mk("SECURE VAULT", C_DIM, 11, mono=True))
        h.addStretch()

        h.addWidget(mk(
            f"// operator:  {self.username}",
            C_DIM, 11, mono=True
        ))
        h.addSpacing(20)

        panic_btn = QPushButton("[ LOCK  Ctrl+Shift+X ]")
        panic_btn.setStyleSheet(
            f"QPushButton{{background:transparent;"
            f"color:{C_DIM};border:none;font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{color:{C_RED};}}"
        )
        panic_btn.clicked.connect(self._instant_lock)
        h.addWidget(panic_btn)

        return bar

    def _build_sidebar(self):
        side = QWidget()
        side.setFixedWidth(SIDEBAR_W)
        side.setStyleSheet(f"background:{C_PANEL};")

        v = QVBoxLayout(side)
        v.setContentsMargins(0, 32, 0, 24)
        v.setSpacing(0)

        bl = QVBoxLayout()
        bl.setContentsMargins(24, 0, 24, 0)
        bl.setSpacing(4)

        brand = QLabel("SHURAKSHA")
        brand.setStyleSheet(
            f"color:{C_WHITE};font-size:15px;font-weight:bold;"
            f"letter-spacing:4px;background:transparent;"
        )
        bl.addWidget(brand)
        bl.addWidget(mk("> vault_v1.0", C_DIM, 11, mono=True))
        v.addLayout(bl)

        v.addSpacing(20)
        v.addWidget(hline())
        v.addSpacing(16)

        self.nav_btns = {}
        nav_items = [
            ("files", "📁", "ENCRYPTED FILES"),
            ("creds", "🔑", "CREDENTIALS"),
            ("notes", "📝", "SECURE NOTES"),
            ("log",   "📋", "ACCESS LOG"),
        ]

        for key, icon, label in nav_items:
            btn = self._nav_btn(icon, label, key)
            self.nav_btns[key] = btn
            v.addWidget(btn)

        v.addStretch()
        v.addWidget(hline())
        v.addSpacing(12)

        for line in [
            "// AES-256-GCM",
            "// LOCAL ONLY",
            "// NO CLOUD SYNC",
        ]:
            lbl = mk(line, C_GHOST, 10, mono=True)
            lbl.setContentsMargins(24, 0, 0, 0)
            v.addWidget(lbl)
            v.addSpacing(2)

        self.nav_btns['files'].set_active()
        return side

    def _nav_btn(self, icon: str, label: str, key: str):

        class NavBtn(QPushButton):
            def __init__(self_, icon, label, key):
                super().__init__()
                self_.key = key
                h = QHBoxLayout(self_)
                h.setContentsMargins(24, 0, 24, 0)
                h.setSpacing(12)

                il = QLabel(icon)
                il.setStyleSheet(
                    "font-size:15px;background:transparent;"
                )
                il.setFixedWidth(22)
                h.addWidget(il)

                nl = QLabel(label)
                nl.setStyleSheet(
                    f"color:{C_DIM};font-size:12px;"
                    f"font-family:'Consolas','Courier New',monospace;"
                    f"letter-spacing:1px;background:transparent;"
                )
                h.addWidget(nl)
                h.addStretch()

                self_.text_lbl = nl
                self_.setFixedHeight(40)
                self_.set_inactive()

            def set_active(self_):
                self_.setStyleSheet(
                    f"QPushButton{{"
                    f"  background:{C_CYAN_DIM};"
                    f"  border-left:3px solid {C_CYAN};"
                    f"  border-top:none;"
                    f"  border-right:none;"
                    f"  border-bottom:none;"
                    f"}}"
                )
                self_.text_lbl.setStyleSheet(
                    f"color:{C_CYAN};font-size:12px;"
                    f"font-family:'Consolas','Courier New',monospace;"
                    f"letter-spacing:1px;background:transparent;"
                    f"font-weight:bold;"
                )

            def set_inactive(self_):
                self_.setStyleSheet(
                    "QPushButton{background:transparent;border:none;}"
                    "QPushButton:hover{"
                    f"background:{C_GHOST};}}"
                )
                self_.text_lbl.setStyleSheet(
                    f"color:{C_DIM};font-size:12px;"
                    f"font-family:'Consolas','Courier New',monospace;"
                    f"letter-spacing:1px;background:transparent;"
                )

        btn = NavBtn(icon, label, key)
        btn.clicked.connect(lambda: self._switch_section(key))
        return btn

    def _switch_section(self, key: str):
        sections = {
            'files': 0, 'creds': 1,
            'notes': 2, 'log':   3
        }
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.set_active()
            else:
                btn.set_inactive()

        self.section_stack.setCurrentIndex(sections[key])
        self.active_section = key
        self._reset_idle()

        if key == 'files':  self._reload_files()
        elif key == 'creds': self._reload_creds()
        elif key == 'notes': self._load_notes()
        elif key == 'log':   self._load_log()

    # -----------------------------------------------
    # FILES SECTION
    # -----------------------------------------------

    def _build_files_section(self):
        widget = QWidget()
        v      = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        toolbar = QWidget()
        toolbar.setFixedHeight(58)
        toolbar.setStyleSheet(
            f"background:{C_BG};"
            f"border-bottom:1px solid {C_BORDER};"
        )
        th = QHBoxLayout(toolbar)
        th.setContentsMargins(28, 0, 28, 0)
        th.setSpacing(12)

        th.addWidget(mk(
            "//  ENCRYPTED FILES", C_CYAN, 11, bold=True, mono=True
        ))
        th.addWidget(mk(
            "All files encrypted with AES-256-GCM.", C_DIM, 12
        ))
        th.addStretch()

        self.files_count_lbl = mk("0 files", C_DIM, 12, mono=True)
        th.addWidget(self.files_count_lbl)

        add_btn = QPushButton("+ ADD FILE")
        add_btn.setFixedSize(120, 36)
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_file)
        th.addWidget(add_btn)

        v.addWidget(toolbar)

        self.files_scroll = QScrollArea()
        self.files_scroll.setWidgetResizable(True)
        self.files_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.files_scroll.setStyleSheet(
            f"QScrollArea{{background:{C_BG};border:none;}}"
        )

        self.files_container = QWidget()
        self.files_container.setStyleSheet(f"background:{C_BG};")
        self.files_layout = QVBoxLayout(self.files_container)
        self.files_layout.setContentsMargins(0, 0, 0, 0)
        self.files_layout.setSpacing(0)
        self.files_layout.addStretch()

        self.files_scroll.setWidget(self.files_container)
        v.addWidget(self.files_scroll, stretch=1)

        QTimer.singleShot(100, self._reload_files)
        return widget

    def _reload_files(self):
        while self.files_layout.count() > 1:
            item = self.files_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        files = self.vault.load_meta()
        self.files_count_lbl.setText(
            f"{len(files)} file{'s' if len(files) != 1 else ''}"
        )

        if not files:
            empty = mk(
                "// No files in vault.\n"
                "// Click  + ADD FILE  to encrypt and store a file.",
                C_DIM, 13, mono=True
            )
            empty.setContentsMargins(28, 40, 28, 0)
            self.files_layout.insertWidget(0, empty)
            return

        for meta in files:
            row = FileRow(meta)
            row.export_requested.connect(self._export_file)
            row.delete_requested.connect(self._delete_file)
            self.files_layout.insertWidget(
                self.files_layout.count() - 1, row
            )

    def _add_file(self):
        self._reset_idle()
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Add to Vault",
            str(Path.home()), "All Files (*)"
        )
        if not path:
            return
        try:
            meta = self.vault.add_file(Path(path))
            self._reload_files()
            self._toast(f"// FILE ADDED:  {meta['name']}")
        except Exception as e:
            self._err(f"Failed to add file:\n{e}")

    def _export_file(self, vault_id: str):
        self._reset_idle()
        dest = QFileDialog.getExistingDirectory(
            self, "Choose Export Location", str(Path.home())
        )
        if not dest:
            return
        try:
            out = self.vault.export_file(vault_id, Path(dest))
            self._toast(f"// EXPORTED:  {out.name}")
        except Exception as e:
            self._err(f"Export failed:\n{e}")

    def _delete_file(self, vault_id: str):
        self._reset_idle()
        box = QMessageBox(self)
        box.setWindowTitle("// CONFIRM DELETE")
        box.setText(
            "Permanently delete this file from the vault?\n\n"
            "The file will be overwritten and cannot be recovered."
        )
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton{{background:{C_CYAN};color:#000;"
            f"border:none;padding:6px 16px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        if box.exec() == QMessageBox.StandardButton.Yes:
            try:
                self.vault.delete_file(vault_id)
                self._reload_files()
                self._toast("// FILE SECURELY DELETED")
            except Exception as e:
                self._err(f"Delete failed:\n{e}")

    # -----------------------------------------------
    # CREDENTIALS SECTION
    # -----------------------------------------------

    def _build_creds_section(self):
        widget = QWidget()
        v      = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        toolbar = QWidget()
        toolbar.setFixedHeight(58)
        toolbar.setStyleSheet(
            f"background:{C_BG};"
            f"border-bottom:1px solid {C_BORDER};"
        )
        th = QHBoxLayout(toolbar)
        th.setContentsMargins(28, 0, 28, 0)
        th.setSpacing(12)

        th.addWidget(mk(
            "//  CREDENTIALS", C_CYAN, 11, bold=True, mono=True
        ))
        th.addStretch()

        add_cred_btn = QPushButton("+ ADD CREDENTIAL")
        import_btn = QPushButton("IMPORT FROM BROWSER")
        import_btn.setFixedSize(200, 36)
        import_btn.setStyleSheet(BTN_GHOST)
        import_btn.clicked.connect(self._import_from_browser)
        th.addWidget(import_btn)
        add_cred_btn.setFixedSize(160, 36)
        add_cred_btn.setStyleSheet(BTN_PRIMARY)
        add_cred_btn.clicked.connect(self._add_credential)
        th.addWidget(add_cred_btn)

        v.addWidget(toolbar)

        headers = QWidget()
        headers.setFixedHeight(36)
        headers.setStyleSheet(
            f"background:{C_PANEL};"
            f"border-bottom:1px solid {C_BORDER};"
        )
        hh = QHBoxLayout(headers)
        hh.setContentsMargins(20, 0, 16, 0)
        hh.setSpacing(16)

        for label, width in [
            ("SITE / APP", 180),
            ("USERNAME",   160),
            ("PASSWORD",   140),
        ]:
            lbl = mk(label, C_DIM, 11, mono=True)
            lbl.setFixedWidth(width)
            hh.addWidget(lbl)

        hh.addStretch()
        v.addWidget(headers)

        self.creds_scroll = QScrollArea()
        self.creds_scroll.setWidgetResizable(True)
        self.creds_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.creds_scroll.setStyleSheet(
            f"QScrollArea{{background:{C_BG};border:none;}}"
        )

        self.creds_container = QWidget()
        self.creds_container.setStyleSheet(f"background:{C_BG};")
        self.creds_layout = QVBoxLayout(self.creds_container)
        self.creds_layout.setContentsMargins(0, 0, 0, 0)
        self.creds_layout.setSpacing(0)
        self.creds_layout.addStretch()

        self.creds_scroll.setWidget(self.creds_container)
        v.addWidget(self.creds_scroll, stretch=1)

        return widget

    def _reload_creds(self):
        while self.creds_layout.count() > 1:
            item = self.creds_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        creds = self.vault.load_creds()

        if not creds:
            empty = mk(
                "// No credentials saved.\n"
                "// Click  + ADD CREDENTIAL  to store a password.",
                C_DIM, 13, mono=True
            )
            empty.setContentsMargins(28, 40, 28, 0)
            self.creds_layout.insertWidget(0, empty)
            return

        for i, cred in enumerate(creds):
            row = CredRow(cred, i)
            row.delete_requested.connect(self._delete_cred)
            self.creds_layout.insertWidget(
                self.creds_layout.count() - 1, row
            )

    def _add_credential(self):
        self._reset_idle()

        site, ok = QInputDialog.getText(
            self, "Add Credential", "Site or App Name:"
        )
        if not ok or not site.strip():
            return

        username, ok = QInputDialog.getText(
            self, "Add Credential", "Username or Email:"
        )
        if not ok:
            return

        password, ok = QInputDialog.getText(
            self, "Add Credential", "Password:",
            QLineEdit.EchoMode.Password
        )
        if not ok:
            return

        creds = self.vault.load_creds()
        creds.append({
            'site'    : site.strip(),
            'username': username.strip(),
            'password': password,
            'added'   : datetime.now().strftime("%d %b %Y"),
        })
        self.vault.save_creds(creds)
        write_log(f"CREDENTIAL_ADDED  {site.strip()}")
        self._reload_creds()
        self._toast(f"// CREDENTIAL SAVED:  {site.strip()}")

    def _delete_cred(self, index: int):
        self._reset_idle()
        creds = self.vault.load_creds()
        if 0 <= index < len(creds):
            name = creds[index].get('site', '')
            del creds[index]
            self.vault.save_creds(creds)
            write_log(f"CREDENTIAL_DELETED  {name}")
            self._reload_creds()

    # -----------------------------------------------
    # NOTES SECTION
    # -----------------------------------------------

    def _build_notes_section(self):
        widget = QWidget()
        v      = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        toolbar = QWidget()
        toolbar.setFixedHeight(58)
        toolbar.setStyleSheet(
            f"background:{C_BG};"
            f"border-bottom:1px solid {C_BORDER};"
        )
        th = QHBoxLayout(toolbar)
        th.setContentsMargins(28, 0, 28, 0)
        th.setSpacing(12)

        th.addWidget(mk(
            "//  SECURE NOTES", C_CYAN, 11, bold=True, mono=True
        ))
        th.addWidget(mk(
            "Encrypted with AES-256-GCM. Auto-saved.", C_DIM, 12
        ))
        th.addStretch()

        save_btn = QPushButton("SAVE NOTES")
        save_btn.setFixedSize(120, 36)
        save_btn.setStyleSheet(BTN_SUCCESS)
        save_btn.clicked.connect(self._save_notes)
        th.addWidget(save_btn)

        v.addWidget(toolbar)

        self.notes_editor = QTextEdit()
        self.notes_editor.setPlaceholderText(
            "// Start typing your secure notes here...\n"
            "// This content is encrypted and stored locally."
        )
        self.notes_editor.setStyleSheet(
            f"QTextEdit{{"
            f"  background:{C_BG};"
            f"  border:none;"
            f"  color:{C_WHITE};"
            f"  font-size:14px;"
            f"  padding:28px 36px;"
            f"  font-family:'Consolas','Courier New',monospace;"
            f"}}"
        )
        v.addWidget(self.notes_editor, stretch=1)

        return widget

    def _load_notes(self):
        content = self.vault.load_notes()
        self.notes_editor.setPlainText(content)

    def _save_notes(self):
        self._reset_idle()
        content = self.notes_editor.toPlainText()
        try:
            self.vault.save_notes(content)
            write_log("NOTES_SAVED")
            self._toast("// NOTES SAVED AND ENCRYPTED")
        except Exception as e:
            self._err(f"Failed to save notes:\n{e}")

    # -----------------------------------------------
    # LOG SECTION
    # -----------------------------------------------

    def _build_log_section(self):
        widget = QWidget()
        v      = QVBoxLayout(widget)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        toolbar = QWidget()
        toolbar.setFixedHeight(58)
        toolbar.setStyleSheet(
            f"background:{C_BG};"
            f"border-bottom:1px solid {C_BORDER};"
        )
        th = QHBoxLayout(toolbar)
        th.setContentsMargins(28, 0, 28, 0)

        th.addWidget(mk(
            "//  ACCESS LOG", C_CYAN, 11, bold=True, mono=True
        ))
        th.addWidget(mk(
            "Every vault operation is recorded here.", C_DIM, 12
        ))
        th.addStretch()

        clear_btn = QPushButton("CLEAR LOG")
        clear_btn.setFixedSize(110, 36)
        clear_btn.setStyleSheet(BTN_DANGER)
        clear_btn.clicked.connect(self._clear_log)
        th.addWidget(clear_btn)

        v.addWidget(toolbar)

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet(
            f"QTextEdit{{"
            f"  background:{C_BG};"
            f"  border:none;"
            f"  color:{C_MID};"
            f"  font-size:12px;"
            f"  padding:28px 36px;"
            f"  font-family:'Consolas','Courier New',monospace;"
            f"}}"
        )
        v.addWidget(self.log_viewer, stretch=1)

        return widget

    def _load_log(self):
        content = self.vault.load_log()
        self.log_viewer.setPlainText(content)
        sb = self.log_viewer.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear_log(self):
        self._reset_idle()
        try:
            if LOG_FILE.exists():
                LOG_FILE.unlink()
            self.log_viewer.clear()
            write_log("LOG_CLEARED")
            self._toast("// ACCESS LOG CLEARED")
        except Exception as e:
            self._err(f"Could not clear log:\n{e}")

    # -----------------------------------------------
    # STATUS BAR
    # -----------------------------------------------

    def _build_statusbar(self):
        status = QWidget()
        status.setFixedHeight(28)
        status.setStyleSheet(
            f"background:{C_PANEL};"
            f"border-top:1px solid {C_BORDER};"
        )

        h = QHBoxLayout(status)
        h.setContentsMargins(20, 0, 20, 0)

        self.toast_lbl = mk("", C_GREEN, 11, mono=True)
        h.addWidget(self.toast_lbl)
        h.addStretch()

        h.addWidget(mk(
            "PANIC LOCK:  Ctrl+Shift+X",
            C_GHOST, 10, mono=True
        ))

        return status

    # -----------------------------------------------
    # UTILITY
    # -----------------------------------------------

    def _toast(self, message: str):
        """Show a brief status message at the bottom."""
        self.toast_lbl.setText(message)
        self.toast_lbl.setStyleSheet(
            f"color:{C_GREEN};font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        QTimer.singleShot(
            4000, lambda: self.toast_lbl.setText("")
        )

    def _err(self, message: str):
        """Show an error dialog."""
        box = QMessageBox(self)
        box.setWindowTitle("// ERROR")
        box.setText(message)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton{{background:{C_CYAN};color:#000;"
            f"border:none;padding:6px 16px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        box.exec()

    def _reset_idle(self):
        """Reset the auto-lock timer on any user activity."""
        self.idle_timer.start(AUTO_LOCK_SECONDS * 1000)

    def _auto_lock(self):
        """Lock after inactivity timeout."""
        write_log("VAULT_AUTO_LOCKED  reason:inactivity")
        self._stop_security()
        self.lock_requested.emit()

    def _instant_lock(self):
        """Immediately lock the vault (panic button)."""
        write_log("VAULT_LOCKED  reason:panic_button")
        self._stop_security()
        self.lock_requested.emit()

    def mousePressEvent(self, event):
        self._reset_idle()
        if event.position().y() < TITLEBAR_H:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        self._reset_idle()
        if self._drag_pos is not None:
            self.move(
                self.pos() +
                event.globalPosition().toPoint() - self._drag_pos
            )
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def keyPressEvent(self, event):
        self._reset_idle()
        super().keyPressEvent(event)

def _import_from_browser(self):
        """
        Extract saved passwords from installed browsers
        and import them into the vault credentials section.
        Shows a summary of what was found and imported.
        """
        self._reset_idle()

        try:
            from src.browser.extractor import BrowserExtractor

            extractor  = BrowserExtractor()
            available  = extractor.get_available_browsers()

            if not available:
                self._toast(
                    "// No supported browsers found."
                )
                return

            self._toast(
                f"// Scanning:  "
                f"{', '.join(available)}  ..."
            )

            # Extract all credentials
            extracted = extractor.extract_all()

            if not extracted:
                self._toast(
                    "// No saved credentials found in browsers."
                )
                return

            # Load existing credentials to avoid duplicates
            existing = self.vault.load_creds()
            existing_keys = {
                (c.get('site', ''), c.get('username', ''))
                for c in existing
            }

            # Filter out duplicates
            new_creds = []
            for cred in extracted:
                key = (
                    cred.get('site', ''),
                    cred.get('username', '')
                )
                if key not in existing_keys:
                    new_creds.append({
                        'site'    : cred['site'],
                        'username': cred['username'],
                        'password': cred['password'],
                        'added'   : (
                            datetime.now()
                            .strftime("%d %b %Y")
                        ),
                    })
                    existing_keys.add(key)

            if not new_creds:
                self._toast(
                    "// All browser credentials already "
                    "in vault. Nothing new to import."
                )
                return

            # Confirm import
            box = QMessageBox(self)
            box.setWindowTitle("// IMPORT CREDENTIALS")
            box.setText(
                f"Found {len(new_creds)} new credential"
                f"{'s' if len(new_creds) != 1 else ''} "
                f"from {', '.join(available)}.\n\n"
                f"Import them into the vault?"
            )
            box.setStandardButtons(
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No
            )
            box.setStyleSheet(
                f"QMessageBox{{background:{C_BG};"
                f"color:{C_WHITE};"
                f"font-family:'Consolas','Courier New',"
                f"monospace;}}"
                f"QPushButton{{background:{C_CYAN};"
                f"color:#000;border:none;"
                f"padding:6px 16px;font-weight:bold;"
                f"font-family:'Consolas','Courier New',"
                f"monospace;}}"
            )

            if box.exec() == QMessageBox.StandardButton.Yes:
                existing.extend(new_creds)
                self.vault.save_creds(existing)
                write_log(
                    f"BROWSER_IMPORT  "
                    f"{len(new_creds)} credentials imported"
                )
                self._reload_creds()
                self._toast(
                    f"// IMPORTED:  {len(new_creds)} "
                    f"credential"
                    f"{'s' if len(new_creds) != 1 else ''}"
                )

        except Exception as e:
            self._err(f"Browser import failed:\n{str(e)}")

# -----------------------------------------------
# ENTRY POINT
# -----------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    test_user = {
        'username': 'TestUser',
        'hints'   : ['hint1', 'hint2', 'hint3'],
    }

    window = VaultDashboard(
        user_data=test_user,
        master_password="testpassword123"
    )
    window.lock_requested.connect(app.quit)
    window.show()

    sys.exit(app.exec())
