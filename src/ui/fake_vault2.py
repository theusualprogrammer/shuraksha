# -----------------------------------------------
# Shuraksha - Second Fake Vault
# File: src/ui/fake_vault2.py
# -----------------------------------------------
# This vault appears when someone correctly solves
# the BODMAS math question.
# It looks and behaves exactly like the real vault
# but everything is fake:
#   - Files added get fake encrypted names
#   - Fake file metadata is generated
#   - Pre-loaded with convincing fake files
#   - Credentials appear to save but are fake
#   - Notes appear to save but are not real
#   - Access log shows convincing fake entries
#   - All operations show success messages
# -----------------------------------------------

import sys
import random
import string
from pathlib import Path
from datetime import datetime, timedelta

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

# -----------------------------------------------
# DIMENSIONS
# -----------------------------------------------
WIN_W      = 1100
WIN_H      = 720
SIDEBAR_W  = 220
TITLEBAR_H = 46

# -----------------------------------------------
# AUTO LOCK
# -----------------------------------------------
AUTO_LOCK_SECONDS = 300

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
# FAKE DATA GENERATORS
# These generate convincing looking fake data
# whenever a user adds something to this vault.
# -----------------------------------------------

# Fake file name pools by extension type
FAKE_NAMES = {
    'document': [
        "Tax_Return_{year}.pdf",
        "Insurance_Policy_{year}.pdf",
        "Bank_Statement_{month}_{year}.pdf",
        "Medical_Records_{year}.pdf",
        "Property_Agreement_{year}.pdf",
        "Employment_Contract_{year}.pdf",
        "Legal_Notice_{year}.pdf",
        "Passport_Scan_{year}.pdf",
        "Driving_Licence_Copy.pdf",
        "Salary_Slip_{month}_{year}.pdf",
        "Loan_Agreement_{year}.pdf",
        "Investment_Statement_{year}.pdf",
    ],
    'image': [
        "Family_Photo_{year}.jpg",
        "Vacation_{month}_{year}.jpg",
        "ID_Card_Scan.png",
        "Profile_Backup_{year}.jpg",
        "Screenshot_{date}.png",
        "Document_Scan_{date}.jpg",
        "Receipt_{date}.jpg",
        "Certificate_{year}.png",
    ],
    'video': [
        "Birthday_{year}.mp4",
        "Meeting_Recording_{date}.mp4",
        "Family_Event_{month}_{year}.mp4",
        "Backup_Clip_{date}.avi",
        "Interview_{date}.mp4",
        "Tutorial_Recording_{date}.mkv",
    ],
    'audio': [
        "Voice_Note_{date}.mp3",
        "Meeting_Audio_{date}.mp3",
        "Recording_{date}.wav",
        "Backup_Audio_{date}.mp3",
    ],
    'archive': [
        "Project_Backup_{year}.zip",
        "Documents_{month}_{year}.zip",
        "Photos_{year}.zip",
        "Work_Files_{date}.zip",
        "Archive_{date}.rar",
    ],
    'code': [
        "Project_Source_{year}.zip",
        "Backup_Scripts_{date}.py",
        "Work_Code_{date}.zip",
    ],
    'other': [
        "Important_File_{date}",
        "Backup_{date}",
        "Document_{date}",
        "Secure_File_{date}",
    ],
}

# Fake file sizes
FAKE_SIZES = [
    "128 KB", "256 KB", "512 KB",
    "1.2 MB", "2.4 MB", "3.7 MB",
    "5.1 MB", "8.3 MB", "12.4 MB",
    "24.6 MB", "48.2 MB", "96.1 MB",
]

# Pre-loaded fake files to show on first open
PRELOADED_FILES = [
    ("📑", "Tax_Returns_2024.pdf",         "1.2 MB",  "12 Jan 2025"),
    ("🖼",  "Family_Vacation_Photos.zip",   "48.3 MB", "3 Mar 2025"),
    ("📄", "Insurance_Policy_2025.pdf",     "890 KB",  "22 Feb 2025"),
    ("📄", "Bank_Statement_March2025.pdf",  "234 KB",  "1 Mar 2025"),
    ("💻", "Work_Project_Backup.zip",       "12.4 MB", "18 Mar 2025"),
    ("📑", "Medical_Records_2024.pdf",      "2.1 MB",  "9 Dec 2024"),
    ("🖼",  "Passport_Scan.jpg",            "3.4 MB",  "5 Jan 2025"),
    ("📄", "Property_Documents.pdf",        "5.7 MB",  "28 Feb 2025"),
]

# Pre-loaded fake credentials
PRELOADED_CREDS = [
    {
        'site'    : 'Gmail',
        'username': 'user.backup@gmail.com',
        'password': 'G$3kP@ss2024!',
        'added'   : '10 Jan 2025',
    },
    {
        'site'    : 'LinkedIn',
        'username': 'professional.user@outlook.com',
        'password': 'Link3dIn#Secure',
        'added'   : '15 Jan 2025',
    },
    {
        'site'    : 'Online Banking',
        'username': 'account.holder@bank.com',
        'password': 'B@nk$ecure2024',
        'added'   : '20 Jan 2025',
    },
    {
        'site'    : 'Instagram',
        'username': '@user_profile_backup',
        'password': 'Insta#2024Pass',
        'added'   : '25 Jan 2025',
    },
]

# Pre-loaded fake notes
PRELOADED_NOTES = """// Personal secure notes

Important account numbers:
  - Savings account:  XXXX-XXXX-4821
  - Credit card:      XXXX-XXXX-XXXX-7734
  - Insurance policy: POL-2024-88421

Emergency contacts:
  - Dr. Sharma:  +91 98765 43210
  - Lawyer:      +91 87654 32109

Locker combination: 14 - 27 - 39

House keys: spare set at main drawer

Vehicle insurance renewal: March 2026

Note to self: review investments by April 2025
"""

# Pre-loaded fake access log entries
PRELOADED_LOG = [
    "[2025-01-10  09:14:22]  VAULT_OPENED  operator:user",
    "[2025-01-10  09:18:43]  FILE_ADDED  Tax_Returns_2024.pdf",
    "[2025-01-15  14:22:11]  VAULT_OPENED  operator:user",
    "[2025-01-15  14:25:38]  CREDENTIAL_ADDED  LinkedIn",
    "[2025-01-20  11:08:55]  VAULT_OPENED  operator:user",
    "[2025-01-20  11:12:04]  FILE_ADDED  Insurance_Policy_2025.pdf",
    "[2025-02-01  16:44:19]  VAULT_OPENED  operator:user",
    "[2025-02-01  16:48:32]  NOTES_SAVED",
    "[2025-03-18  10:33:07]  VAULT_OPENED  operator:user",
    "[2025-03-18  10:36:21]  FILE_ADDED  Work_Project_Backup.zip",
]


def _fake_date() -> str:
    """Generate a realistic recent date string."""
    now  = datetime.now()
    days = random.randint(1, 90)
    dt   = now - timedelta(days=days)
    return dt.strftime("%d %b %Y  %H:%M")


def _fake_short_date() -> str:
    now  = datetime.now()
    days = random.randint(1, 60)
    dt   = now - timedelta(days=days)
    return dt.strftime("%d %b %Y")


def _fake_log_timestamp() -> str:
    now  = datetime.now()
    secs = random.randint(60, 3600 * 24 * 30)
    dt   = now - timedelta(seconds=secs)
    return dt.strftime("%Y-%m-%d  %H:%M:%S")


def generate_fake_filename(real_name: str) -> str:
    """
    Given the real filename, generate a convincing
    fake filename of the same type.
    For example:
        mypassport.jpg -> Passport_Scan_2025.jpg
        budget.xlsx    -> Bank_Statement_March_2025.pdf
    """
    ext  = Path(real_name).suffix.lower()
    now  = datetime.now()

    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    subs = {
        'year' : str(now.year),
        'month': months[now.month - 1],
        'date' : now.strftime("%d%m%Y"),
    }

    if ext in ['.pdf', '.doc', '.docx', '.txt', '.xlsx']:
        pool = FAKE_NAMES['document']
        fake_ext = ext
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
        pool = FAKE_NAMES['image']
        fake_ext = ext
    elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
        pool = FAKE_NAMES['video']
        fake_ext = ext
    elif ext in ['.mp3', '.wav', '.flac', '.aac']:
        pool = FAKE_NAMES['audio']
        fake_ext = ext
    elif ext in ['.zip', '.rar', '.7z']:
        pool = FAKE_NAMES['archive']
        fake_ext = ext
    elif ext in ['.py', '.js', '.html', '.css']:
        pool = FAKE_NAMES['code']
        fake_ext = ext
    else:
        pool = FAKE_NAMES['other']
        fake_ext = ext or '.dat'

    template = random.choice(pool)
    name     = template.format(**subs)

    # Make sure the extension matches
    if not name.endswith(fake_ext):
        name = Path(name).stem + fake_ext

    return name


def get_icon(name: str) -> str:
    ext = Path(name).suffix.lower()
    icons = {
        '.jpg': '🖼', '.jpeg': '🖼', '.png': '🖼',
        '.gif': '🖼', '.bmp': '🖼', '.webp': '🖼',
        '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬',
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
        '.pdf': '📑', '.doc': '📄', '.docx': '📄',
        '.txt': '📄', '.xlsx': '📄',
        '.zip': '🗜', '.rar': '🗜',
        '.py':  '💻', '.js':  '💻',
    }
    return icons.get(ext, '📎')


# -----------------------------------------------
# HELPERS
# -----------------------------------------------
def mk(text, color=C_WHITE, size=13, bold=False,
       mono=False, wrap=False, align=None):
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


# -----------------------------------------------
# FILE ROW WIDGET
# -----------------------------------------------
class FakeFileRow(QWidget):
    """A single fake file row in the vault list."""

    delete_requested = pyqtSignal(int)

    def __init__(self, index: int, icon: str, name: str,
                 size: str, date: str, parent=None):
        super().__init__(parent)
        self.index = index
        self._build(icon, name, size, date)

    def _build(self, icon, name, size, date):
        self.setFixedHeight(56)
        self.setStyleSheet(
            f"QWidget{{background:{C_CARD};"
            f"border-bottom:1px solid {C_BORDER};}}"
        )

        h = QHBoxLayout(self)
        h.setContentsMargins(20, 0, 16, 0)
        h.setSpacing(16)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(
            "font-size:20px;background:transparent;"
        )
        icon_lbl.setFixedWidth(28)
        h.addWidget(icon_lbl)

        name_lbl = mk(name, C_WHITE, 13, bold=True)
        name_lbl.setMinimumWidth(200)
        h.addWidget(name_lbl)
        h.addStretch()

        size_lbl = mk(size, C_DIM, 12, mono=True)
        size_lbl.setFixedWidth(80)
        size_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        h.addWidget(size_lbl)

        date_lbl = mk(date, C_DIM, 12, mono=True)
        date_lbl.setFixedWidth(160)
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        h.addWidget(date_lbl)

        # Export button - shows success but does nothing real
        exp_btn = QPushButton("EXPORT")
        exp_btn.setFixedSize(80, 32)
        exp_btn.setStyleSheet(BTN_GHOST)
        exp_btn.clicked.connect(self._fake_export)
        h.addWidget(exp_btn)

        # Delete button - removes from the fake list
        del_btn = QPushButton("DELETE")
        del_btn.setFixedSize(80, 32)
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.index)
        )
        h.addWidget(del_btn)

    def _fake_export(self):
        """Show a convincing export success message."""
        QMessageBox.information(
            self, "// EXPORT COMPLETE",
            "File decrypted and exported successfully.\n\n"
            "Saved to Downloads folder."
        )


# -----------------------------------------------
# CREDENTIAL ROW WIDGET
# -----------------------------------------------
class FakeCredRow(QWidget):
    """A single fake credential row."""

    delete_requested = pyqtSignal(int)

    def __init__(self, cred: dict, index: int, parent=None):
        super().__init__(parent)
        self.index        = index
        self._pwd_visible = False
        self._pwd_text    = cred.get('password', '')
        self._build(cred)

    def _build(self, cred: dict):
        self.setFixedHeight(52)
        self.setStyleSheet(
            f"QWidget{{background:{C_CARD};"
            f"border-bottom:1px solid {C_BORDER};}}"
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

        self.pwd_lbl = mk(
            "●" * min(len(self._pwd_text), 16),
            C_DIM, 12, mono=True
        )
        self.pwd_lbl.setMinimumWidth(140)
        h.addWidget(self.pwd_lbl)
        h.addStretch()

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
        """Copy the fake password to clipboard."""
        QApplication.clipboard().setText(self._pwd_text)
        QTimer.singleShot(
            30000,
            lambda: QApplication.clipboard().setText("")
        )


# -----------------------------------------------
# SECOND FAKE VAULT
# -----------------------------------------------
class FakeVault2(QMainWindow):
    """
    The second fake vault dashboard.

    Triggered when someone correctly solves the
    BODMAS math question instead of typing the DOB.

    Fully interactive:
        - Add files  -> generates convincing fake names
        - Delete files
        - Export files -> shows success message
        - Add credentials -> saves fake entries
        - Edit secure notes -> saves to memory only
        - Access log -> shows convincing fake history
        - All operations show proper success toasts

    Nothing is actually encrypted or stored permanently.
    Session data exists only in memory.
    On lock all session data is wiped.
    """

    lock_requested = pyqtSignal()

    def __init__(self, username: str = "User", parent=None):
        super().__init__(parent)

        self.username = username

        # In-memory fake data storage
        # Nothing is written to disk
        self.fake_files = list(PRELOADED_FILES)
        self.fake_creds = list(PRELOADED_CREDS)
        self.fake_notes = PRELOADED_NOTES
        self.fake_log   = list(PRELOADED_LOG)

        # Add a fresh login entry to the log
        self.fake_log.append(
            f"[{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}]"
            f"  VAULT_OPENED  operator:{username}"
        )

        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._lock)
        self.idle_timer.start(AUTO_LOCK_SECONDS * 1000)

        self.setWindowTitle("Shuraksha Vault")
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None

        self.setStyleSheet(GLOBAL_STYLE)
        self._build()

        # Panic button
        self.panic = QShortcut(
            QKeySequence("Ctrl+Shift+X"), self
        )
        self.panic.activated.connect(self._lock)

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

        h.addWidget(mk(
            "[  SHR  ]", C_CYAN, 11, bold=True, mono=True
        ))
        h.addWidget(mk("  //  ", C_GHOST, 11, mono=True))
        h.addWidget(mk("SECURE VAULT", C_DIM, 11, mono=True))
        h.addStretch()
        h.addWidget(mk(
            f"// operator:  {self.username}",
            C_DIM, 11, mono=True
        ))
        h.addSpacing(20)

        lock_btn = QPushButton("[ LOCK  Ctrl+Shift+X ]")
        lock_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C_DIM};"
            f"border:none;font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{color:{C_RED};}}"
        )
        lock_btn.clicked.connect(self._lock)
        h.addWidget(lock_btn)

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

        for line in ["// AES-256-GCM", "// LOCAL ONLY",
                     "// NO CLOUD SYNC"]:
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
                    f"QPushButton{{background:{C_CYAN_DIM};"
                    f"border-left:3px solid {C_CYAN};"
                    f"border-top:none;border-right:none;"
                    f"border-bottom:none;}}"
                )
                self_.text_lbl.setStyleSheet(
                    f"color:{C_CYAN};font-size:12px;"
                    f"font-weight:bold;"
                    f"font-family:'Consolas','Courier New',monospace;"
                    f"letter-spacing:1px;background:transparent;"
                )

            def set_inactive(self_):
                self_.setStyleSheet(
                    "QPushButton{background:transparent;border:none;}"
                    f"QPushButton:hover{{background:{C_GHOST};}}"
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
        self._reset_idle()

        if key == 'files':   self._reload_files()
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

        self.files_count_lbl = mk(
            f"{len(self.fake_files)} files", C_DIM, 12, mono=True
        )
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
        """Reload the fake file list."""
        while self.files_layout.count() > 1:
            item = self.files_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.files_count_lbl.setText(
            f"{len(self.fake_files)} file"
            f"{'s' if len(self.fake_files) != 1 else ''}"
        )

        if not self.fake_files:
            empty = mk(
                "// No files in vault.\n"
                "// Click  + ADD FILE  to encrypt and store a file.",
                C_DIM, 13, mono=True
            )
            empty.setContentsMargins(28, 40, 28, 0)
            self.files_layout.insertWidget(0, empty)
            return

        for i, entry in enumerate(self.fake_files):
            if isinstance(entry, tuple):
                icon, name, size, date = entry
            else:
                icon = get_icon(entry.get('name', ''))
                name = entry.get('name', '')
                size = entry.get('size', '')
                date = entry.get('date', '')

            row = FakeFileRow(i, icon, name, size, date)
            row.delete_requested.connect(self._delete_file)
            self.files_layout.insertWidget(
                self.files_layout.count() - 1, row
            )

    def _add_file(self):
        """
        Open a file picker.
        Generate a convincing fake name for the file.
        Add it to the in-memory fake list.
        """
        self._reset_idle()
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Add to Vault",
            str(Path.home()), "All Files (*)"
        )
        if not path:
            return

        real_path  = Path(path)
        fake_name  = generate_fake_filename(real_path.name)
        fake_size  = random.choice(FAKE_SIZES)
        fake_date  = _fake_date()
        fake_icon  = get_icon(fake_name)

        # Add to in-memory list as a tuple
        self.fake_files.append(
            (fake_icon, fake_name, fake_size, fake_date)
        )

        # Add to fake log
        self.fake_log.append(
            f"[{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}]"
            f"  FILE_ADDED  {fake_name}"
        )

        self._reload_files()
        self._toast(f"// FILE ENCRYPTED AND STORED:  {fake_name}")

    def _delete_file(self, index: int):
        """Delete a fake file from the in-memory list."""
        self._reset_idle()
        if 0 <= index < len(self.fake_files):
            entry = self.fake_files[index]
            name  = (
                entry[1] if isinstance(entry, tuple)
                else entry.get('name', '')
            )

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
                del self.fake_files[index]
                self.fake_log.append(
                    f"[{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}]"
                    f"  FILE_DELETED  {name}"
                )
                self._reload_files()
                self._toast("// FILE SECURELY DELETED")

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

        QTimer.singleShot(100, self._reload_creds)
        return widget

    def _reload_creds(self):
        """Reload the fake credentials list."""
        while self.creds_layout.count() > 1:
            item = self.creds_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.fake_creds:
            empty = mk(
                "// No credentials saved.\n"
                "// Click  + ADD CREDENTIAL  to store a password.",
                C_DIM, 13, mono=True
            )
            empty.setContentsMargins(28, 40, 28, 0)
            self.creds_layout.insertWidget(0, empty)
            return

        for i, cred in enumerate(self.fake_creds):
            row = FakeCredRow(cred, i)
            row.delete_requested.connect(self._delete_cred)
            self.creds_layout.insertWidget(
                self.creds_layout.count() - 1, row
            )

    def _add_credential(self):
        """Add a new fake credential to the in-memory list."""
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

        self.fake_creds.append({
            'site'    : site.strip(),
            'username': username.strip(),
            'password': password,
            'added'   : _fake_short_date(),
        })

        self.fake_log.append(
            f"[{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}]"
            f"  CREDENTIAL_ADDED  {site.strip()}"
        )

        self._reload_creds()
        self._toast(f"// CREDENTIAL SAVED:  {site.strip()}")

    def _delete_cred(self, index: int):
        """Delete a fake credential from the in-memory list."""
        self._reset_idle()
        if 0 <= index < len(self.fake_creds):
            name = self.fake_creds[index].get('site', '')
            del self.fake_creds[index]
            self.fake_log.append(
                f"[{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}]"
                f"  CREDENTIAL_DELETED  {name}"
            )
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
            f"QTextEdit{{background:{C_BG};border:none;"
            f"color:{C_WHITE};font-size:14px;"
            f"padding:28px 36px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        v.addWidget(self.notes_editor, stretch=1)

        QTimer.singleShot(100, self._load_notes)
        return widget

    def _load_notes(self):
        """Load the fake notes into the editor."""
        self.notes_editor.setPlainText(self.fake_notes)

    def _save_notes(self):
        """
        Save notes to memory only.
        Shows a convincing save success message.
        """
        self._reset_idle()
        self.fake_notes = self.notes_editor.toPlainText()
        self.fake_log.append(
            f"[{datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}]"
            f"  NOTES_SAVED"
        )
        self._toast("// NOTES SAVED AND ENCRYPTED")

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
            f"QTextEdit{{background:{C_BG};border:none;"
            f"color:{C_MID};font-size:12px;"
            f"padding:28px 36px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        v.addWidget(self.log_viewer, stretch=1)

        QTimer.singleShot(100, self._load_log)
        return widget

    def _load_log(self):
        """Display the fake access log."""
        content = "\n".join(reversed(self.fake_log))
        self.log_viewer.setPlainText(content)
        sb = self.log_viewer.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear_log(self):
        """Clear the fake log."""
        self._reset_idle()
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
            f"QPushButton{{background:{C_CYAN};color:#000;"
            f"border:none;padding:6px 16px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        if box.exec() == QMessageBox.StandardButton.Yes:
            self.fake_log = []
            self.log_viewer.clear()
            self._toast("// ACCESS LOG CLEARED")

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
            "PANIC LOCK:  Ctrl+Shift+X", C_GHOST, 10, mono=True
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
        QTimer.singleShot(4000, lambda: self.toast_lbl.setText(""))

    def _reset_idle(self):
        self.idle_timer.start(AUTO_LOCK_SECONDS * 1000)

    def _lock(self):
        """Lock and return to login. Wipe all session data."""
        self.fake_files = []
        self.fake_creds = []
        self.fake_notes = ""
        self.fake_log   = []
        self.lock_requested.emit()

    # -----------------------------------------------
    # WINDOW DRAG
    # -----------------------------------------------

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


# -----------------------------------------------
# ENTRY POINT
# -----------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = FakeVault2(username="TestUser")
    window.lock_requested.connect(app.quit)
    window.show()
    sys.exit(app.exec())